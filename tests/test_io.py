import pytest

from dobot.io import IO


class FakeRobot:
    """Objeto fake para substituir o robô em testes."""

    def __init__(self):
        self.command = None


class TestIO:
    """Testes para a classe IO."""

    def test_initialization(self):
        fake_robot = FakeRobot()
        io = IO(fake_robot)
        assert io.robot is fake_robot

    async def test_do_valid_values(self, monkeypatch):
        io = IO(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        io.robot.command = fake_command
        result = await io.do(0, 1)
        assert result == "ok"
        assert received == [("SetDO", {"index": 0, "status": 1})]

    async def test_do_invalid_index_negative(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.do(-1, 1)

    async def test_do_invalid_index_above_15(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.do(16, 1)

    async def test_do_invalid_value_not_zero_or_one(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="must be 0 or 1"):
            await io.do(0, 2)

    async def test_pwm_valid(self, monkeypatch):
        io = IO(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return "ok"

        io.robot.command = fake_command
        result = await io.pwm(0, 1000, 50)
        assert result == "ok"
        assert received == [("SetPWM", {"index": 0, "frequency": 1000, "dutyCycle": 50})]

    async def test_pwm_invalid_frequency_too_low(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 1 and 100000"):
            await io.pwm(0, 0, 50)

    async def test_pwm_invalid_frequency_too_high(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 1 and 100000"):
            await io.pwm(0, 100001, 50)

    async def test_pwm_invalid_duty_too_low(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 100"):
            await io.pwm(0, 1000, -1)

    async def test_pwm_invalid_duty_too_high(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 100"):
            await io.pwm(0, 1000, 101)

    async def test_pwm_invalid_index(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.pwm(-1, 1000, 50)

    async def test_di_valid_index(self, monkeypatch):
        io = IO(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return 1

        io.robot.command = fake_command
        result = await io.di(3)
        assert result == 1
        assert received == [("GetDI", {"index": 3})]

    async def test_di_invalid_index(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.di(-1)

    async def test_di_invalid_index_above_15(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.di(16)

    async def test_ai_valid_index(self, monkeypatch):
        io = IO(FakeRobot())
        received = []

        async def fake_command(method, **params):
            received.append((method, params))
            return 1024

        io.robot.command = fake_command
        result = await io.ai(5)
        assert result == 1024
        assert received == [("GetAI", {"index": 5})]

    async def test_ai_invalid_index(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.ai(-1)

    async def test_ai_invalid_index_above_15(self):
        io = IO(FakeRobot())
        with pytest.raises(ValueError, match="between 0 and 15"):
            await io.ai(16)
