import logging

from .base_command import BaseCommand, register_command

logger = logging.getLogger(__name__)

@register_command
class ReloadCommand(BaseCommand):
    _name = 'reload'

    def run(self, args):
        self._manager.reload(self._shell)
