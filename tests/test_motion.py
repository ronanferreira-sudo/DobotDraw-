
from dobot.constants import PTP_MOVJ, PTP_MOVL
from dobot.motion import Motion


class FakeRobot:
    """Objeto fake para substituir o robô em testes."""

    def __init__(self):
        self.command = None


class TestMotion:
    """Testes para a classe Motion."""

    def test_initialization(self):
        fake_robot = FakeRobot()
        motion = Motion(fake_robot)
        assert motion.robot is fake_robot

    async def test_home_command(self, monkeypatch):
        motion = Motion(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "home_ok"

        motion.robot.command = fake_command
        result = await motion.home()
        assert result == "home_ok"
        assert received == [("set_homecmd", {})]

    async def test_movj_uses_ptp_movj_constant(self, monkeypatch):
        motion = Motion(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "movj_ok"

        motion.robot.command = fake_command
        result = await motion.movj(100.0, 200.0, 50.0, r=30.0)
        assert result == "movj_ok"
        assert received[0][0] == "set_ptpcmd"
        assert received[0][1]["ptp_mode"] == PTP_MOVJ
        assert received[0][1]["x"] == 100.0
        assert received[0][1]["y"] == 200.0
        assert received[0][1]["z"] == 50.0
        assert received[0][1]["r"] == 30.0

    async def test_movl_uses_ptp_movl_constant(self, monkeypatch):
        motion = Motion(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "movl_ok"

        motion.robot.command = fake_command
        result = await motion.movl(100.0, 200.0, 50.0, r=30.0)
        assert result == "movl_ok"
        assert received[0][0] == "set_ptpcmd"
        assert received[0][1]["ptp_mode"] == PTP_MOVL
        assert received[0][1]["x"] == 100.0
        assert received[0][1]["y"] == 200.0
        assert received[0][1]["z"] == 50.0
        assert received[0][1]["r"] == 30.0

    async def test_movj_default_r_value(self, monkeypatch):
        motion = Motion(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        motion.robot.command = fake_command
        await motion.movj(0.0, 0.0, 0.0)
        assert received[0][1]["r"] == 0

    async def test_movl_default_r_value(self, monkeypatch):
        motion = Motion(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        motion.robot.command = fake_command
        await motion.movl(0.0, 0.0, 0.0)
        assert received[0][1]["r"] == 0
