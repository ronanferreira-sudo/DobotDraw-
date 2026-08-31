import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import serial
import serial.tools.list_ports

from .exceptions import ConnectionError, RPCError, TimeoutError

logger = logging.getLogger(__name__)

_DEFAULT_BAUDRATE = 115200
_HEADER = bytes([0xAA, 0xAA])


class USBClient:
    """Cliente USB direto usando serial puro, sem dependencia de DobotEDU ou pydobot."""

    def __init__(self, port: str = "auto", baudrate: int = _DEFAULT_BAUDRATE, timeout: float = 1.0, max_retries: int = 3):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_retries = max_retries
        self._serial = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()

    @staticmethod
    def find_port() -> str | None:
        """Tenta encontrar uma porta serial compatível com o Dobot."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.description or "").lower()
            if "dobot" in desc or "usb serial" in desc or "ch340" in desc:
                return p.device
        for p in ports:
            if "com" in p.device.lower() or "ttyusb" in p.device.lower() or "ttyacm" in p.device.lower():
                return p.device
        return None

    async def connect(self) -> None:
        """Abre a porta serial."""
        if self.port == "auto" or not self.port:
            self.port = self.find_port()
            if not self.port:
                raise ConnectionError("Nenhuma porta serial compativel encontrada")
            logger.info(f"Porta auto-detectada: {self.port}")

        logger.info(f"Opening serial port {self.port} at {self.baudrate}")
        try:
            self._serial = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            )
            await asyncio.sleep(0.1)
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            logger.info("Serial port opened")
        except serial.SerialException as exc:
            raise ConnectionError(f"Failed to open serial port {self.port}: {exc}") from exc

    async def disconnect(self) -> None:
        """Fecha a porta serial."""
        if self._serial is not None:
            try:
                await asyncio.get_event_loop().run_in_executor(self._executor, self._serial.close)
            except Exception as exc:
                logger.warning(f"Error closing serial port: {exc}")
            finally:
                self._serial = None
        self._executor.shutdown(wait=False)

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    @staticmethod
    def _checksum(data: bytes) -> int:
        return (~(sum(data) & 0xFF)) & 0xFF

    def _build_packet(self, command: int, params: bytes = b"") -> bytes:
        length = len(params) + 1
        payload = bytes([length, command]) + params
        checksum = self._checksum(payload)
        return _HEADER + payload + bytes([checksum])

    async def _read_response(self) -> dict[str, Any]:
        header = await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._serial.read,
            2
        )
        if header != _HEADER:
            raise ConnectionError(f"Invalid response header: {header.hex()}")

        length_data = await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._serial.read,
            1
        )
        length = length_data[0]

        rest = await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._serial.read,
            length + 1
        )
        full = header + length_data + rest
        return self._parse_response(full)

    def _parse_response(self, data: bytes) -> dict[str, Any]:
        if len(data) < 4:
            raise ConnectionError("Response too short")
        if data[0] != 0xAA or data[1] != 0xAA:
            raise ConnectionError("Invalid response header")

        length = data[2]
        command = data[3]
        params = data[4:4 + length - 1]
        checksum = data[4 + length - 1]

        calc_checksum = self._checksum(data[2:4 + length - 1])
        if checksum != calc_checksum:
            raise ConnectionError("Invalid response checksum")

        return {"command": command, "params": params}

    async def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        if not self.connected:
            raise ConnectionError("Serial port not open")

        if params is None:
            params = {}

        cmd_id = self._get_command_id(command)
        if cmd_id is None:
            raise RPCError(-1, f"Unknown command: {command}")

        packet = self._build_packet(cmd_id, self._encode_params(params))

        async with self._lock:
            for attempt in range(1, self.max_retries + 1):
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._serial.write,
                        packet
                    )

                    response = await asyncio.wait_for(
                        self._read_response(),
                        timeout=self.timeout
                    )
                    return self._decode_result(command, response)
                except TimeoutError:
                    if attempt == self.max_retries:
                        raise TimeoutError(f"Serial command '{command}' timed out") from None
                    logger.warning(f"Timeout on attempt {attempt}, retrying...")
                except ConnectionError as exc:
                    if attempt == self.max_retries:
                        raise
                    logger.warning(f"Connection error on attempt {attempt}: {exc}")

        raise ConnectionError("Max retries exceeded for serial command")

    async def command(self, method: str, **params: Any) -> Any:
        """Alias para send, mantendo compatibilidade com DobotClient."""
        return await self.send(method, params)

    @staticmethod
    def _encode_params(params: dict[str, Any]) -> bytes:
        parts = []
        for k, v in params.items():
            if isinstance(v, bool):
                parts.append(int(v))
            elif isinstance(v, float):
                parts.append(int(v * 100))
            elif isinstance(v, int):
                parts.append(v)
            else:
                parts.append(int(v))
        return bytes(parts)

    @staticmethod
    def _decode_result(command: str, response: dict[str, Any]) -> Any:
        params = response.get("params", b"")
        if not params:
            return None
        return params

    @staticmethod
    def _get_command_id(command: str) -> int | None:
        mapping = {
            "set_homecmd": 3,
            "set_ptpcmd": 4,
            "SetQueuedCmdStartExec": 14,
            "SetQueuedCmdStopExec": 15,
            "SetQueuedCmdClear": 16,
            "GetQueuedCmdCurrentIndex": 17,
            "SetEndEffectorSuctionCup": 21,
            "SetEndEffectorGripper": 22,
            "SetEndEffectorLaser": 23,
            "SetDO": 24,
            "SetPWM": 25,
            "GetDI": 26,
            "GetAI": 27,
            "GetPose": 30,
            "GetErrorID": 32,
            "GetDeviceVersion": 33,
            "SetWAITCmd": 35,
            "SetCPParams": 90,
            "SetCPCmd": 91,
        }
        return mapping.get(command)
