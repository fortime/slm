import os

modules = []

for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    __import__(__name__ + '.' + module[:-3], locals(), globals())
    modules.append(module)

del module
del modules
del os

from .base_command import ALL_COMMANDS
__all__ = ALL_COMMANDS

del ALL_COMMANDS
