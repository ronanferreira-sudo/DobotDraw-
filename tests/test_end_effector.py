
from dobot.end_effector import EndEffector


class FakeRobot:
    """Objeto fake para substituir o robô em testes."""

    def __init__(self):
        self.command = None


class TestEndEffector:
    """Testes para a classe EndEffector."""

    def test_initialization(self):
        fake_robot = FakeRobot()
        tool = EndEffector(fake_robot)
        assert tool.robot is fake_robot

    async def test_suction_on(self, monkeypatch):
        tool = EndEffector(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        tool.robot.command = fake_command
        result = await tool.suction(enable=True)
        assert result == "ok"
        assert received[0][0] == "SetEndEffectorSuctionCup"
        assert received[0][1] == {"enableCtrl": True, "on": True}

    async def test_suction_off(self, monkeypatch):
        tool = EndEffector(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        tool.robot.command = fake_command
        result = await tool.suction(enable=False)
        assert result == "ok"
        assert received[0][1] == {"enableCtrl": True, "on": False}

    async def test_gripper_on(self, monkeypatch):
        tool = EndEffector(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        tool.robot.command = fake_command
        result = await tool.gripper(enable=True)
        assert result == "ok"
        assert received[0][0] == "SetEndEffectorGripper"
        assert received[0][1] == {"enableCtrl": True, "on": True}

    async def test_gripper_off(self, monkeypatch):
        tool = EndEffector(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        tool.robot.command = fake_command
        result = await tool.gripper(enable=False)
        assert result == "ok"
        assert received[0][1] == {"enableCtrl": True, "on": False}

    async def test_laser_on(self, monkeypatch):
        tool = EndEffector(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        tool.robot.command = fake_command
        result = await tool.laser(enable=True)
        assert result == "ok"
        assert received[0][0] == "SetEndEffectorLaser"
        assert received[0][1] == {"enableCtrl": True, "on": True}

    async def test_laser_off(self, monkeypatch):
        tool = EndEffector(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        tool.robot.command = fake_command
        result = await tool.laser(enable=False)
        assert result == "ok"
        assert received[0][1] == {"enableCtrl": True, "on": False}
