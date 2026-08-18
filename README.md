# DobotDraw

Async Python client for Dobot robotic arms (Magician Lite) via JSON-RPC 2.0 over WebSocket.

## Installation

```bash
pip install -e .
```

## Server Setup

Esta biblioteca é um **cliente**. Ela se conecta a um servidor RPC rodando em `127.0.0.1:9090`.

### Opção 1: Usar o software oficial da Dobot
1. Instale o **Dobot Studio** ou **Dobot EDU** da Dobot
2. Conecte o Dobot Magician Lite via USB
3. Inicie o servidor RPC dentro do software (geralmente em `127.0.0.1:9090`)

### Opção 2: Servidor RPC standalone
Se você tem o executável/servidor RPC separado:
1. Conecte o Dobot via USB ou rede
2. Execute o servidor RPC apontando para a porta 9090
3. Verifique se está acessível em `http://127.0.0.1:9090`

### Verificar conexão
```bash
python -c "from dobot.rpc import RPCClient; import asyncio; c = RPCClient(); asyncio.get_event_loop().run_until_complete(c.connect()); print('Conectado!'); asyncio.get_event_loop().run_until_complete(c.disconnect())"
```

## Usage

```python
import asyncio
from dobot import Robot

async def main():
    async with Robot() as robot:
        await robot.motion.home()
        await robot.canvas.start(speed=100, acceleration=100)
        await robot.canvas.line(200, 0, 0, 0)
        await robot.canvas.line(200, 100, 0, 0)
        await robot.canvas.stop()

asyncio.run(main())
```

## Features

- **Async API** — Full asyncio support with context manager
- **Robust connection** — Auto-reconnect with exponential backoff
- **Continuous path drawing** — Smooth line and arc movements via Canvas
- **Shape helpers** — Draw squares and circles with Drawer
- **Type hints** — Full type annotations for IDE support
- **Structured logging** — Configurable logging throughout
- **Input validation** — Validates IO ranges and parameters
- **Queue control** — Wait for command queue completion

## CLI

```bash
# Go to home position
dobotdraw home

# Draw a 50mm square
dobotdraw square --size 50

# Draw a 30mm circle
dobotdraw circle --radius 30

# Show robot status
dobotdraw status
```

## API Reference

### Robot

```python
from dobot import Robot

async with Robot(host="127.0.0.1", port=9090, max_retries=3) as robot:
    # Motion
    await robot.motion.home()
    await robot.motion.movj(200, 0, 0, r=0)
    await robot.motion.movl(200, 100, 0, r=0)

    # Canvas (continuous path)
    await robot.canvas.start(speed=100, acceleration=100)
    await robot.canvas.line(200, 0, 0, 0)
    await robot.canvas.arc(200, 100, 0, r=0)
    await robot.canvas.stop()

    # Drawer (shapes)
    await robot.drawer.draw_square(100, 100, 50, z=0)
    await robot.drawer.draw_circle(200, 200, 30, z=0)

    # IO
    await robot.io.do(0, 1)
    await robot.io.pwm(1, 1000, 50)

    # Dashboard
    await robot.dashboard.get_pose()
    await robot.dashboard.get_alarm()
    await robot.dashboard.get_version()

    # Queue
    await robot.queue.wait_for_queue(timeout=60)

    # End effector
    await robot.tool.suction(enable=True)
    await robot.tool.gripper(enable=True)
    await robot.tool.laser(enable=True)
```

## GUI

Interface gráfica para controle manual do robô:

```bash
dobotdraw-gui
```

Ou execute diretamente:

```bash
python interface.py
```

### Funcionalidades da interface
- **Conectar/Desconectar** — Botão para conectar ao robô
- **Movimento** — Botão Home e Parar Fila
- **Desenho Contínuo** — Iniciar/Parar CP e enviar linhas com coordenadas X/Y/Z/R
- **Formas** — Desenhar quadrado e círculo pré-configurados
- **IO** — Ligar/Desligar saída digital 0
- **Log** — Área de texto com mensagens de status e erros

## Requirements

- Python 3.11+
- Dobot RPC server running at `127.0.0.1:9090`
