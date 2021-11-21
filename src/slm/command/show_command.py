import logging

from .base_command import BaseCommand, register_command
from ..login_info import login_info

logger = logging.getLogger(__name__)

@register_command
class ShowCommand(BaseCommand):
    _name = 'show'
    _fields = sorted([field for field in dir(login_info.LoginInfo) if not field.startswith('_')])

    def run_x(self, args):
        node = self._login_info_manager.node(args[0])
        if node is None:
            print('{} does not exist'.format(args[0]))
            return
        if node.login_info().host() is None:
            print('there is no host in {}'.format(args[0]))
            return
        msg = 'There is no property of {} in LoginInfo'.format(args[1])
        if hasattr(node.login_info(), args[1]):
            func = getattr(node.login_info(), args[1])
            if hasattr(func, '__call__'):
                msg = str(func(is_raw=True))
        print(msg)

    def complete_x(self, parser):
        if parser.word_idx() == 1:
            return self.complete_node(parser.text())
        elif parser.word_idx() == 2:
            return [field for field in self._fields if field.startswith(parser.text())]
        return []
