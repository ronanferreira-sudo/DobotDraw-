import logging
from typing import Any

from .canvas import Canvas
from .client import DobotClient
from .dashboard import Dashboard
from .drawer import Drawer
from .end_effector import EndEffector
from .io import IO
from .motion import Motion
from .queue import Queue

logger = logging.getLogger(__name__)


class Robot:
    """Interface principal para controle do robô Dobot."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9090, max_retries: int = 3):
        self.client = DobotClient(host, port, max_retries=max_retries)

        self.motion = Motion(self)
        self.dashboard = Dashboard(self)
        self.io = IO(self)
        self.queue = Queue(self)
        self.tool = EndEffector(self)
        self.canvas = Canvas(self)
        self.drawer = Drawer(self.canvas)

    async def connect(self) -> None:
        """Estabelece conexão com o robô."""
        logger.info("Connecting to robot")
        return await self.client.connect()

    async def disconnect(self) -> None:
        """Encerra a conexão com o robô."""
        logger.info("Disconnecting from robot")
        return await self.client.disconnect()

    async def command(self, method: str, **params: Any) -> Any:
        """Envia um comando direto ao robô.

        Args:
            method: Nome do método RPC.
            **params: Parâmetros do comando.

        Returns:
            Resultado retornado pelo servidor.
        """
        return await self.client.command(method, **params)

    async def __aenter__(self) -> "Robot":
        """Entra no contexto assíncrono e conecta ao robô."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Sai do contexto assíncrono e desconecta do robô."""
        await self.disconnect()
        return False
