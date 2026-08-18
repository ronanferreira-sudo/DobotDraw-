import asyncio

import pytest

from dobot.queue import Queue


class FakeRobot:
    """Objeto fake para substituir o robô em testes."""

    def __init__(self):
        self.command = None


class TestQueue:
    """Testes para a classe Queue."""

    def test_initialization(self):
        fake_robot = FakeRobot()
        queue = Queue(fake_robot)
        assert queue.robot is fake_robot

    async def test_start(self, monkeypatch):
        queue = Queue(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append(method)
            return "started"

        queue.robot.command = fake_command
        result = await queue.start()
        assert result == "started"
        assert received == ["SetQueuedCmdStartExec"]

    async def test_stop(self, monkeypatch):
        queue = Queue(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append(method)
            return "stopped"

        queue.robot.command = fake_command
        result = await queue.stop()
        assert result == "stopped"
        assert received == ["SetQueuedCmdStopExec"]

    async def test_clear(self, monkeypatch):
        queue = Queue(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append(method)
            return "cleared"

        queue.robot.command = fake_command
        result = await queue.clear()
        assert result == "cleared"
        assert received == ["SetQueuedCmdClear"]

    async def test_index(self, monkeypatch):
        queue = Queue(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append(method)
            return 5

        queue.robot.command = fake_command
        result = await queue.index()
        assert result == 5
        assert received == ["GetQueuedCmdCurrentIndex"]

    async def test_wait_for_queue_when_index_returns_minus_one(self, monkeypatch):
        queue = Queue(FakeRobot())
        call_count = [0]

        async def fake_command(method, **params):
            call_count[0] += 1
            return -1

        queue.robot.command = fake_command
        monkeypatch.setattr(asyncio, "sleep", lambda *_: None)

        result = await queue.wait_for_queue(timeout=5)
        assert result is None
        assert call_count[0] == 1

    async def test_wait_for_queue_timeout_raises_timeout_error(self, monkeypatch):
        queue = Queue(FakeRobot())
        call_count = [0]

        async def fake_command(method, **params):
            call_count[0] += 1
            return 0

        queue.robot.command = fake_command

        async def fake_sleep(duration):
            pass

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        with pytest.raises(TimeoutError, match="did not finish within"):
            await queue.wait_for_queue(timeout=0.05)
