import pytest

from dobot.robot import Robot


class FakeRobot:
    """Objeto fake para substituir o robô em testes."""

    def __init__(self):
        self.command = None


class TestRobot:
    """Testes para a classe Robot."""

    def test_initialization_default_host_port(self):
        robot = Robot()
        assert robot.client.rpc.host == "127.0.0.1"
        assert robot.client.rpc.port == 9090

    def test_initialization_custom_host_port(self):
        robot = Robot(host="192.168.1.100", port=9091)
        assert robot.client.rpc.host == "192.168.1.100"
        assert robot.client.rpc.port == 9091

    async def test_aenter_connects(self, monkeypatch):
        robot = Robot(host="127.0.0.1", port=9090)
        connect_called = []

        async def fake_connect():
            connect_called.append(True)

        monkeypatch.setattr(robot, "connect", fake_connect)

        async with robot as r:
            assert r is robot
            assert len(connect_called) == 1

    async def test_aexit_disconnects(self, monkeypatch):
        robot = Robot(host="127.0.0.1", port=9090)
        disconnect_called = []

        async def fake_disconnect():
            disconnect_called.append(True)

        async def fake_connect():
            pass

        monkeypatch.setattr(robot, "disconnect", fake_disconnect)
        monkeypatch.setattr(robot, "connect", fake_connect)

        async with robot:
            pass

        assert len(disconnect_called) == 1

    async def test_aexit_propagates_exception(self, monkeypatch):
        robot = Robot(host="127.0.0.1", port=9090)
        disconnect_called = []

        async def fake_disconnect():
            disconnect_called.append(True)

        async def fake_connect():
            pass

        monkeypatch.setattr(robot, "disconnect", fake_disconnect)
        monkeypatch.setattr(robot, "connect", fake_connect)

        with pytest.raises(ValueError):
            async with robot:
                raise ValueError("test error")

        assert len(disconnect_called) == 1

    def test_submodules_are_accessible(self):
        robot = Robot()
        assert hasattr(robot, "motion")
        assert hasattr(robot, "io")
        assert hasattr(robot, "queue")
        assert hasattr(robot, "tool")
        assert hasattr(robot, "canvas")
        assert hasattr(robot, "dashboard")

    def test_submodule_types(self):
        robot = Robot()
        from dobot.canvas import Canvas
        from dobot.dashboard import Dashboard
        from dobot.end_effector import EndEffector
        from dobot.io import IO
        from dobot.motion import Motion
        from dobot.queue import Queue

        assert isinstance(robot.motion, Motion)
        assert isinstance(robot.io, IO)
        assert isinstance(robot.queue, Queue)
        assert isinstance(robot.tool, EndEffector)
        assert isinstance(robot.canvas, Canvas)
        assert isinstance(robot.dashboard, Dashboard)

    async def test_connect_delegates_to_client(self, monkeypatch):
        robot = Robot(host="127.0.0.1", port=9090)
        connect_called = []

        async def fake_connect():
            connect_called.append(True)

        monkeypatch.setattr(robot.client, "connect", fake_connect)
        await robot.connect()
        assert len(connect_called) == 1

    async def test_disconnect_delegates_to_client(self, monkeypatch):
        robot = Robot(host="127.0.0.1", port=9090)
        disconnect_called = []

        async def fake_disconnect():
            disconnect_called.append(True)

        monkeypatch.setattr(robot.client, "disconnect", fake_disconnect)
        await robot.disconnect()
        assert len(disconnect_called) == 1

    async def test_command_delegates_to_client(self, monkeypatch):
        robot = Robot(host="127.0.0.1", port=9090)
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "result"

        monkeypatch.setattr(robot.client, "command", fake_command)
        result = await robot.command("test_method", x=1.0)
        assert result == "result"
        assert received == [("test_method", {"x": 1.0})]
