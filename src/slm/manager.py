import cmd
import logging
import logging.config
import os
import readline
import sys

import yaml

from .setting import setting
from .login_info.login_info_manager import LoginInfoManager

logger = logging.getLogger(__name__)

class ManagerShell(cmd.Cmd):
    prompt='slm> '

    def __init__(self, manager):
        """slm shell

        :manager: slm instance
        """
        super(ManagerShell, self).__init__()
        self._manager = manager
        self._login_info_manager = manager.login_info_manager()

    def do_quit(self, arg):
        self._manager.close()
        return True

    def do_exit(self, arg):
        self._manager.close()
        return True

    def do_print(self, arg):
        self._login_info_manager.print_nodes()

    def do_ls(self, arg):
        nodes = self._login_info_manager.list_nodes(arg)
        for (id, node) in nodes:
            print(id)

    def complete_ls(self, text, line, begidx, endidx):
        return self._manager.search_node_ids(text)

class Manager(object):
    def __init__(self, config_path):
        """

        :config_path: path of config file

        """
        self._stopped = False
        with open(config_path, 'r') as fin:
            config = yaml.load(fin)
            if config is not None:
                setting.setup(config)
                setting.lock()
        self._init_log()
        self._tmp_bin_path = os.path.expanduser(setting.TMP_BIN_PATH)
        self._login_info_root_path = os.path.expanduser(setting.LOGIN_INFO_ROOT_PATH)
        self._login_info_manager = LoginInfoManager(self._login_info_root_path)

    def _init_log(self):
        log_file_path = os.path.expanduser(setting.LOG_FILE_PATH)
        self._make_sure_directory_exists(log_file_path)
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'root_handler': {
                    'level': 'DEBUG',
                    'class': 'logging.FileHandler',
                    'filename': log_file_path
                    }
                },
            'loggers': {
                '': {
                    'handlers': ['root_handler'],
                    'level': setting.LOG_LEVEL,
                    'propagate': True
                    },
                'py.warnings': {
                    'handlers': ['root_handler'],
                    'level': 'ERROR',
                    'propagate': True
                    }
                }
            })

        logging.captureWarnings(True)

    def _make_sure_directory_exists(self, path):
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    def close(self):
        print('bye!')

    def login_info_manager(self):
        return self._login_info_manager

    def run(self):
        """start a running loop
        """
        history_file_path = os.path.expanduser(setting.HISTORY_FILE_PATH)
        if os.path.exists(history_file_path):
            readline.read_history_file(history_file_path)
        shell = ManagerShell(self)
        try:
            shell.cmdloop()
        finally:
            self._make_sure_directory_exists(history_file_path)
            readline.write_history_file(history_file_path)
