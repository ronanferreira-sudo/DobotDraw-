import asyncio
from dobot import Robot


async def main():
    robot = Robot()

    print("Biblioteca carregada com sucesso.")
    print(robot)

if __name__ == "__main__":
    asyncio.run(main())