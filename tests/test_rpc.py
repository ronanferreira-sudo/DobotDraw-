import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from dobot.exceptions import ConnectionError, RPCError, TimeoutError
from dobot.rpc import RPCClient


class TestRPCClient:
    """Testes para o RPCClient."""

    def test_connected_property_when_ws_is_none(self):
        client = RPCClient(host="127.0.0.1", port=9090)
        assert client.connected is False

    async def test_send_returns_result(self, rpc_client, mock_ws):
        mock_ws.queue_response({"jsonrpc": "2.0", "result": 42, "id": 1})
        result = await rpc_client.send("test_method", {"param": "value"})
        assert result == 42

    async def test_send_raises_rpc_error(self, rpc_client, mock_ws):
        mock_ws.queue_response({
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": 1
        })
        with pytest.raises(RPCError) as exc_info:
            await rpc_client.send("test_method")
        assert exc_info.value.code == -32600

    async def test_send_raises_connection_error_when_not_connected(self):
        client = RPCClient(host="127.0.0.1", port=9090)
        with pytest.raises(ConnectionError, match="Not connected"):
            await client.send("test_method")

    async def test_connect_and_disconnect(self):
        client = RPCClient(host="127.0.0.1", port=9090)
        assert client.connected is False

        fake_ws = AsyncMock()
        fake_ws.closed = False
        client.ws = fake_ws
        client.id = 0

        assert client.connected is True
        await client.disconnect()
        assert client.connected is False

    async def test_disconnect_when_ws_already_none(self):
        client = RPCClient(host="127.0.0.1", port=9090)
        await client.disconnect()
        assert client.ws is None

    async def test_send_timeout_raises_timeout_error(self, rpc_client, mock_ws):
        mock_ws._recv_queue = asyncio.Queue()

        async def slow_recv():
            await asyncio.sleep(10)

        mock_ws.recv = slow_recv

        client = RPCClient(host="127.0.0.1", port=9090, timeout=0.05)
        client.ws = mock_ws
        client.id = 0

        with pytest.raises(TimeoutError, match="timed out"):
            await client.send("test_method")

    async def test_send_connection_closed_during_recv(self, rpc_client, mock_ws):
        import websockets
        from websockets.frames import Close

        client = RPCClient(host="127.0.0.1", port=9090, max_retries=1)
        client.ws = mock_ws
        client.id = 0
        client._was_connected = True

        async def recv_closed():
            raise websockets.ConnectionClosed(
                Close(1000, "going away"),
                Close(1000, "going away"),
                rcvd_then_sent=True,
            )

        mock_ws.recv = recv_closed

        with pytest.raises(ConnectionError, match="Max retries exceeded"):
            await client.send("test_method")

    async def test_send_connection_closed_error(self, rpc_client, mock_ws):
        import websockets
        from websockets.frames import Close

        client = RPCClient(host="127.0.0.1", port=9090)
        client.ws = mock_ws
        client.id = 0

        async def recv_error():
            raise websockets.ConnectionClosedError(
                Close(1001, "going away"),
                Close(1001, "going away"),
                rcvd_then_sent=True,
            )

        mock_ws.recv = recv_error

        with pytest.raises(ConnectionError):
            await client.send("test_method")

    async def test_jsonrpc_success_result_extraction(self, rpc_client, mock_ws):
        mock_ws.queue_response({"jsonrpc": "2.0", "result": {"x": 10.0, "y": 20.0}, "id": 1})
        result = await rpc_client.send("get_pose")
        assert result == {"x": 10.0, "y": 20.0}

    async def test_send_increments_id(self, rpc_client, mock_ws):
        mock_ws.queue_response({"jsonrpc": "2.0", "result": "ok", "id": 1})
        await rpc_client.send("method_a")
        assert rpc_client.id == 1

        mock_ws.queue_response({"jsonrpc": "2.0", "result": "ok", "id": 2})
        await rpc_client.send("method_b")
        assert rpc_client.id == 2

    async def test_send_with_none_params(self, rpc_client, mock_ws):
        mock_ws.queue_response({"jsonrpc": "2.0", "result": "ok", "id": 1})
        await rpc_client.send("method")
        sent = json.loads(mock_ws._sent[0])
        assert sent["params"] == {}

    async def test_send_with_params(self, rpc_client, mock_ws):
        mock_ws.queue_response({"jsonrpc": "2.0", "result": "ok", "id": 1})
        await rpc_client.send("method", {"x": 1.0, "y": 2.0})
        sent = json.loads(mock_ws._sent[0])
        assert sent["params"] == {"x": 1.0, "y": 2.0}
