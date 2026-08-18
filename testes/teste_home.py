import warnings

warnings.warn(
    "testes/teste_home.py está depreciado. Use a API async.",
    DeprecationWarning,
    stacklevel=2
)

from dobot.conexao import Dobot

print("=" * 50)
print("TESTE 01 - HOME")
print("=" * 50)

robo = Dobot()

print("Executando Home...")
robo.home()

print("Teste concluído!")
