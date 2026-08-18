import pytest

from dobot.canvas import Canvas


class FakeRobot:
    """Objeto fake para substituir o robô em testes."""

    def __init__(self):
        self.command = None


class TestCanvas:
    """Testes para a classe Canvas."""

    def test_initialization(self):
        fake_robot = FakeRobot()
        canvas = Canvas(fake_robot)
        assert canvas.robot is fake_robot
        assert canvas.active is False

    async def test_start(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "started"

        canvas.robot.command = fake_command
        await canvas.start()
        assert canvas.active is True
        assert received[0] == ("SetCPParams", {"planVel": 100, "acc": 100, "dirty": 0})
        assert received[1] == ("SetQueuedCmdStartExec", {})

    async def test_start_custom_speed_acceleration(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "started"

        canvas.robot.command = fake_command
        await canvas.start(speed=500, acceleration=200)
        assert received[0] == ("SetCPParams", {"planVel": 500, "acc": 200, "dirty": 0})

    async def test_stop(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        canvas._active = True
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "stopped"

        canvas.robot.command = fake_command
        await canvas.stop()
        assert canvas.active is False
        assert received == [("SetQueuedCmdStopExec", {})]

    async def test_active_property(self):
        canvas = Canvas(FakeRobot())
        assert canvas.active is False
        canvas._active = True
        assert canvas.active is True

    async def test_line_raises_runtime_error_when_not_active(self):
        canvas = Canvas(FakeRobot())
        assert canvas.active is False
        with pytest.raises(RuntimeError, match="not active"):
            await canvas.line(0.0, 0.0, 0.0)

    async def test_arc_raises_runtime_error_when_not_active(self):
        canvas = Canvas(FakeRobot())
        assert canvas.active is False
        with pytest.raises(RuntimeError, match="not active"):
            await canvas.arc(0.0, 0.0, 0.0)

    async def test_line_absolute_true_sends_cp_mode_1(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        canvas._active = True
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        canvas.robot.command = fake_command
        await canvas.line(100.0, 200.0, 50.0, r=0.0, absolute=True)
        assert received[0][1]["cpMode"] == 1
        assert received[0][1]["x"] == 100.0
        assert received[0][1]["y"] == 200.0
        assert received[0][1]["z"] == 50.0

    async def test_line_absolute_false_sends_cp_mode_0(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        canvas._active = True
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        canvas.robot.command = fake_command
        await canvas.line(100.0, 200.0, 50.0, r=0.0, absolute=False)
        assert received[0][1]["cpMode"] == 0

    async def test_arc_absolute_true_sends_cp_mode_3(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        canvas._active = True
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        canvas.robot.command = fake_command
        await canvas.arc(100.0, 200.0, 50.0, r=0.0, absolute=True)
        assert received[0][1]["cpMode"] == 3

    async def test_arc_absolute_false_sends_cp_mode_2(self, monkeypatch):
        canvas = Canvas(FakeRobot())
        canvas._active = True
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        canvas.robot.command = fake_command
        await canvas.arc(100.0, 200.0, 50.0, r=0.0, absolute=False)
        assert received[0][1]["cpMode"] == 2
