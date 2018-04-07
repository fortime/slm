#import cmd2 as cmd
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

def extend_command(clazz, commandClass):
    def run(this, arg):
        c = commandClass(this, this._manager, this._login_info_manager)
        args = [] if arg is None else arg.split()
        this.clear_complete_state()
        return c.run(args)
    def help(this):
        c = commandClass(this, this._manager, this._login_info_manager)
        this.clear_complete_state()
        return c.help()
    def complete(this, text, line, begidx, endidx):
        c = commandClass(this, this._manager, this._login_info_manager)
        return c.complete(text, line, begidx, endidx)
    setattr(clazz, 'do_' + commandClass.name(), run)
    setattr(clazz, 'help_' + commandClass.name(), help)
    setattr(clazz, 'complete_' + commandClass.name(), complete)

def extend_commands(clazz):
    from . import command
    for commandClass in command.__all__:
        extend_command(clazz, commandClass)

    return clazz

def create_completion_display_matches_func(shell):
    def completion_display_matches(substitution, matches, longest_match_length):
        print(shell.completion_matches)
        readline.redisplay()
    return completion_display_matches

@extend_commands
class ManagerShell(cmd.Cmd):
    prompt='slm> '

    def __init__(self, manager):
        """slm shell

        :manager: slm instance
        """
        super().__init__()
        self._manager = manager
        self._login_info_manager = manager.login_info_manager()
        self.allow_cli_args = False
        self.clear_complete_state()
#        readline.set_completion_display_matches_hook(
#                create_completion_display_matches_func(self))

    def update(self):
        self._login_info_manager = self._manager.login_info_manager()

    def clear_complete_state(self):
        self._last_completed_index = 0
        self._last_attempt_text = None
        self._has_printed_matches = False
        self._last_prefix = None

    def complete(self, text, state):
        logger.debug('complete %s: %d, last attempt text: %s, eqaul: %s',
                text, state, self._last_attempt_text, self._last_attempt_text == text)
        # is there any method to skip the fisrt tab without implementing ourself line editor?

        # get prefix, if prefix is not the same clear self._last_attempt_text
        line = readline.get_line_buffer()
        prefix = line[:readline.get_begidx()]
        if prefix != self._last_prefix:
            self._last_attempt_text = None

        # first tab: first attempt to get completion
        if self._last_attempt_text is None or text != self._last_attempt_text:
            result = super().complete(text, state)
            self._last_attempt_text = None
            # if there is only one match, run the original logic
            if self.completion_matches is not None \
                    and len(self.completion_matches) > 1:
                self._last_prefix = prefix
                self._last_attempt_text = text
                self._has_printed_matches = False
                # in this case, state greater than 0 is meaningless, tell
                # readline there is no match, so it will break this attempt.
                return None
            return result

        # second tab: can't complete, print all matches
        if not self._has_printed_matches:
            result = super().complete(text, state)
            if result is None:
                logger.debug('complete %s new completion: %d', text, state)
                self._last_completed_index = -1
                if text.strip() != '':
                    self.completion_matches.append(text)
                self.completion_matches.append(None)

                # make readline thought it is a new completion
                readline.insert_text('　')
                self._last_attempt_text = text + '　'

                # mark
                self._has_printed_matches = True
            return result

        if state == 0:
            #logger.debug('completion matches: %s', self.completion_matches)
            result = self.completion_matches[self._last_completed_index + 1]
            self._last_completed_index += 1
            if result is None:
                self._last_completed_index = 0
                result = self.completion_matches[self._last_completed_index]

            return result
        else:
            self._last_attempt_text = self.completion_matches[self._last_completed_index]
            return None

    def do_quit(self, arg):
        return True

    def do_exit(self, arg):
        return True

    def postcmd(self, stop, line):
        if stop:
            self._manager.close()
        if line != '':
            print()
        return stop

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

    def reload(self, shell):
        self._login_info_manager = LoginInfoManager(self._login_info_root_path)
        shell.update()

    def run(self):
        """start a running loop
        """
        history_file_path = os.path.expanduser(setting.HISTORY_FILE_PATH)
        if os.path.exists(history_file_path):
            readline.read_history_file(history_file_path)
        shell = ManagerShell(self)
        try:
            while True:
                try:
                    shell.cmdloop()
                    break
                except KeyboardInterrupt:
                    print()
        finally:
            self._make_sure_directory_exists(history_file_path)
            readline.write_history_file(history_file_path)
