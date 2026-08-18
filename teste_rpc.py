import asyncio
from dobot.rpc import RPCClient


async def main():
    rpc = RPCClient()

    print("Conectando...")
    await rpc.connect()

    print("Conectado!")

    resposta = await rpc.send("listMethods")

    print("RESPOSTA:")
    print(resposta)

    await rpc.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
