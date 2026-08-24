# DobotDraw

Async Python client for Dobot robotic arms (Magician Lite) via **direct USB serial** or WebSocket.

## Installation

```bash
pip install -e .
```

## Connection Modes

### Modo 1: USB Direto (recomendado)

Conecte o Magician Lite diretamente via USB, sem precisar do Dobot Studio/Lab:

```python
from dobot import Robot

# Auto-detectar porta automaticamente
async with Robot(mode="usb", serial_port="auto") as robot:
    await robot.motion.home()
    await robot.canvas.start(speed=100, acceleration=100)
    await robot.canvas.line(200, 0, 0, 0)
    await robot.canvas.stop()

# Ou especificar a porta manualmente
async with Robot(mode="usb", serial_port="COM3") as robot:
    await robot.motion.home()
```

**Requisitos para modo USB:**
- Driver USB-Serial instalado (Silabs CP210x)
- Cabo USB conectado ao Magician Lite
- Porta serial correta (ex: `COM3` no Windows, `/dev/ttyUSB0` no Linux)

**Auto-detecção:**
- Use `serial_port="auto"` para detectar automaticamente a porta do Dobot

### Modo 2: WebSocket (DobotLab / Dobot Studio)

1. Instale o **Dobot Studio** ou **Dobot EDU** da Dobot
2. Conecte o Dobot Magician Lite via USB
3. Inicie o servidor RPC dentro do software (geralmente em `127.0.0.1:9090`)

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
- **Direct USB** — No Dobot Studio/Lab required (uses pydobot)
- **WebSocket** — Also supports DobotLab RPC server
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

## GUI

Interface gráfica para controle manual do robô:

```bash
dobotdraw-gui
```

Ou execute diretamente:

```bash
python interface.py
```

## API Reference

```python
from dobot import Robot

# USB mode (default, no DobotLab needed)
async with Robot(mode="usb", serial_port="auto") as robot:
    # Motion
    await robot.motion.home()
    await robot.motion.movj(200, 0, 0, r=0)

    # Canvas (continuous path)
    await robot.canvas.start(speed=100, acceleration=100)
    await robot.canvas.line(200, 0, 0, 0)
    await robot.canvas.stop()

    # IO
    await robot.io.do(0, 1)

    # Dashboard
    await robot.dashboard.get_pose()
```

## Requirements

- Python 3.11+
- Para modo USB: Driver USB-Serial + cabo USB
- Para modo WebSocket: Dobot RPC server em `127.0.0.1:9090`
