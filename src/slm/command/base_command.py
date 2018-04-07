import logging

logger = logging.getLogger(__name__)

ALL_COMMANDS = []

def register_command(clazz):
    ALL_COMMANDS.append(clazz)
    return clazz

class CommandLineParser(object):
    def __init__(self, text, line, beg_idx, end_idx):
        self._text = text
        self._line = line
        self._beg_idx = beg_idx
        self._end_idx = end_idx
        self._word_idx = None
        self._init()

    def _init(self):
        pos = self._beg_idx - 1
        if pos > 0:
            prefix = self._line[:pos]
            self._word_idx = len(prefix.split())
        else:
            self._word_idx = 0

    def text(self):
        return self._text

    def line(self):
        return self._line

    def beg_idx(self):
        return self._beg_idx

    def end_idx(self):
        return self._end_idx

    def word_idx(self):
        return self._word_idx

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
        print('NotImplemented')

    def help(self):
        print('No help! The author is too lazy.')

    def complete(self, text, line, beg_idx, end_idx):
        try:
            return self.complete_x(CommandLineParser(text, line, beg_idx, end_idx))
        except:
            logger.warn('complete with error', exc_info=True)
            return []

    def complete_x(self, parser):
        return []

    def complete_node(self, text):
        nodes = self._login_info_manager.search_nodes(text, False)
        results = []
        for id, node in nodes:
            if node.login_info().host() is not None:
                results.append(id)
        return results
