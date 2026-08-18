import asyncio

from dobot import Robot


async def main():
    async with Robot() as robot:
        print("Conectado!")

        print("Indo para Home...")
        await robot.motion.home()

        print("Iniciando desenho contínuo...")
        await robot.canvas.start(speed=100, acceleration=100)

        print("Desenhando linha...")
        await robot.canvas.line(200, 0, 0, 0, absolute=True)
        await robot.canvas.line(200, 100, 0, 0, absolute=True)
        await robot.canvas.line(300, 100, 0, 0, absolute=True)

        print("Parando desenho...")
        await robot.canvas.stop()

        print("Finalizado!")


if __name__ == "__main__":
    asyncio.run(main())
