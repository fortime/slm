ALL_COMMANDS = []

def register_command(clazz):
    ALL_COMMANDS.append(clazz)
    return clazz

class BaseCommand(object):
    def __init__(self, shell, login_info_manager):
        self._shell = shell
        self._login_info_manager = login_info_manager

    @classmethod
    def name(cls):
        if hasattr(cls, '_name'):
            return cls._name
        raise NotImplemented()

    def run(self, args):
        print('NotImplemented')

    def help(self):
        print('No help! The author is too lazy.')

    def complete(self, text, line, begidx, endidx):
        return []
