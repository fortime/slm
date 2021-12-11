import logging

logger = logging.getLogger(__name__)

ALL_COMMANDS = []

def register_command(clazz):
    ALL_COMMANDS.append(clazz)
    return clazz

class BaseCommand(object):
    def __init__(self, shell, manager, login_info_manager):
        self._shell = shell
        self._manager = manager
        self._login_info_manager = login_info_manager

    @classmethod
    def name(cls):
        if hasattr(cls, '_name'):
            return cls._name
        raise NotImplemented()

    def run(self, args):
        try:
            return self.run_x(*args)
        except Exception as e:
            logger.warn('run with error:', exc_info=True)
            print('run with error: %s' % e)
            return None

    def run_x(self, *args):
        print('NotImplemented')

    def help(self):
        print('No help! The author is too lazy.')

    def complete(self, line_parser):
        try:
            return self.complete_x(line_parser)
        except:
            logger.warn('complete with error:', exc_info=True)
            return []

    def complete_x(self, line_parser):
        return []

    def complete_node(self, text):
        nodes = self._login_info_manager.search_nodes(text, False)
        results = []
        for id, node in nodes:
            if node.login_info().host() is not None:
                results.append(id)
        return results
