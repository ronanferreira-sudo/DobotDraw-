import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add the parent directory (project root) to sys.path so imports work
# regardless of where pytest is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class MockWebSocket:
    """Mock de websocket para testes sem servidor real."""

    def __init__(self) -> None:
        self._closed = False
        self._sent: list[str] = []
        self._recv_queue: asyncio.Queue[str] = asyncio.Queue()

    @property
    def closed(self) -> bool:
        return self._closed

    async def send(self, data: str) -> None:
        if self._closed:
            raise ConnectionError("WebSocket is closed")
        self._sent.append(data)

    async def recv(self) -> str:
        if self._closed:
            raise ConnectionError("WebSocket is closed")
        return await self._recv_queue.get()

    async def close(self) -> None:
        self._closed = True
        # Wake up any pending recv calls
        while not self._recv_queue.empty():
            try:
                self._recv_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def queue_response(self, response: Any) -> None:
        """Enfileira uma resposta para ser retornada por recv()."""
        self._recv_queue.put_nowait(json.dumps(response))


@pytest.fixture
def mock_ws() -> MockWebSocket:
    """Fixture que retorna uma instância de MockWebSocket."""
    return MockWebSocket()


@pytest.fixture
def rpc_client(mock_ws: MockWebSocket) -> Any:
    """Fixture que retorna um RPCClient com websocket mockado."""
    from dobot.rpc import RPCClient
    client = RPCClient(host="127.0.0.1", port=9090)
    client.ws = mock_ws
    client.id = 0
    return client
