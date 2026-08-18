# teste_porta.py

import socket

s = socket.socket()

try:
    s.connect(("127.0.0.1", 9090))
    print("PORTA ABERTA")
except Exception as e:
    print("PORTA FECHADA")
    print(e)

s.close()