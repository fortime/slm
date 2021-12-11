import logging

from .base_command import BaseCommand, register_command
from ..login_info import login_info

logger = logging.getLogger(__name__)


@register_command
class ShowCommand(BaseCommand):
    _name = "show"
    _fields = sorted(
        [field for field in dir(login_info.LoginInfo) if not field.startswith("_")]
    )

    def run_x(self, node_id, field, *args):
        node = self._login_info_manager.node(node_id)
        if node is None:
            print(f"{node_id} does not exist")
            return
        if node.login_info().host() is None:
            print(f"there is no host in {node_id}")
            return
        msg = "There is no property of {} in LoginInfo".format(field)
        if hasattr(node.login_info(), field):
            func = getattr(node.login_info(), field)
            if hasattr(func, "__call__"):
                msg = str(func(is_raw=True))
        print(msg)

    def complete_x(self, line_parser):
        if line_parser.cursor_word_idx() == 1:
            return self.complete_node(line_parser.cursor_word())
        elif line_parser.cursor_word_idx() == 2:
            return [
                field
                for field in self._fields
                if field.startswith(line_parser.cursor_word())
            ]
        return []
