import cmd
import logging
import logging.config
import os
import readline
import sys
import weakref
import yaml

from pynput.keyboard import Key, Controller

from .setting import setting
from .login_info.login_info_manager import LoginInfoManager

logger = logging.getLogger(__name__)

COMPLETER_DELIMS = " \t\n"


def extend_command(clazz, commandClass):
    def run(this, arg):
        c = commandClass(this, this._manager, this._login_info_manager)
        args = [] if arg is None else arg.split()
        this.clear_completer_state()
        return c.run(args)

    def help(this):
        c = commandClass(this, this._manager, this._login_info_manager)
        this.clear_completer_state()
        return c.help()

    def complete(this, line_parser):
        c = commandClass(this, this._manager, this._login_info_manager)
        return c.complete(line_parser)

    setattr(clazz, "do_" + commandClass.name(), run)
    setattr(clazz, "help_" + commandClass.name(), help)
    setattr(clazz, "complete_" + commandClass.name(), complete)


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


class LineParser(object):
    def __init__(self, line, cur_pos):
        self._cursor_word_idx = None
        self._words = []
        word_beg_idx = 0
        word_end_idx = 0

        while True:
            while word_beg_idx < len(line) and line[word_beg_idx] in COMPLETER_DELIMS:
                word_beg_idx += 1
                word_end_idx = word_beg_idx

            if word_beg_idx == len(line) or line[word_beg_idx] in COMPLETER_DELIMS:
                if self._cursor_word_idx is None:
                    self._cursor_word_idx = len(self._words)
                self._words.append(
                    (line[word_beg_idx:word_end_idx], word_beg_idx, word_end_idx)
                )
                break

            while (
                word_end_idx < len(line) and line[word_end_idx] not in COMPLETER_DELIMS
            ):
                word_end_idx += 1
            if word_end_idx >= cur_pos and self._cursor_word_idx is None:
                self._cursor_word_idx = len(self._words)
            self._words.append(
                (line[word_beg_idx:word_end_idx], word_beg_idx, word_end_idx)
            )
            if word_end_idx == len(line):
                break

            word_beg_idx = word_end_idx

    def __len__(self):
        return len(self._words)

    def _at(self, idx):
        try:
            return self._words[idx]
        except IndexError:
            return None

    def word_at(self, idx):
        item = self._at(idx)
        if item is None:
            return None
        return item[0]

    def word_beg_idx_at(self, idx):
        item = self._at(idx)
        if item is None:
            return None
        return item[1]

    def word_end_idx_at(self, idx):
        item = self._at(idx)
        if item is None:
            return None
        return item[2]

    def cursor_word_idx(self):
        return self._cursor_word_idx

    def cursor_word(self):
        return self.word_at(self.cursor_word_idx())

    def cursor_word_beg_idx(self):
        return self.word_beg_idx_at(self.cursor_word_idx())

    def cursor_word_end_idx(self):
        return self.word_end_idx_at(self.cursor_word_idx())


class CompleterState(object):
    def __init__(self, shell):
        readline.set_completer_delims(COMPLETER_DELIMS)
        self._last_word = None
        self._last_word_idx = None
        self._matches_idx = 0
        self._matches = []
        self._shell_ref = weakref.ref(shell)

    def clear(self):
        self._last_word = None
        self._last_word_idx = None
        self._matches_idx = 0
        self._matches = []

    def try_complete(self, state):
        if state != 0:
            return None

        line_parser = LineParser(readline.get_line_buffer(), readline.get_endidx())
        logger.debug(
            "cur_word: %s, from: %d, to: %d, word_idx: %d",
            line_parser.cursor_word(),
            line_parser.cursor_word_beg_idx(),
            line_parser.cursor_word_end_idx(),
            line_parser.cursor_word_idx(),
        )
        if line_parser.cursor_word_end_idx() > readline.get_endidx():
            self._shell_ref().move_cursor_right(
                line_parser.cursor_word_end_idx() - readline.get_endidx()
            )
            self._shell_ref().tab(1)
            return None

        if (
            self._last_word != line_parser.cursor_word()
            or self._last_word_idx != line_parser.cursor_word_idx()
        ):
            self.clear()

        if self._last_word_idx is None:
            self._last_word_idx = line_parser.cursor_word_idx()
            if self._last_word_idx == 0:
                self._matches.extend(
                    self._shell_ref().completenames(line_parser.cursor_word())
                )
            else:
                try:
                    logger.debug(
                        "complete param at %d for command: %s",
                        line_parser.cursor_word_idx(),
                        line_parser.word_at(0),
                    )
                    func = getattr(
                        self._shell_ref(), "complete_" + line_parser.word_at(0)
                    )
                except AttributeError:
                    func = self._shell_ref().completedefault
                self._matches.extend(func(line_parser))

        if len(self._matches) == 0:
            return None
        idx = self._matches_idx % len(self._matches)
        self._matches_idx = idx + 1
        self._last_word = self._matches[idx]
        return self._last_word

    def word_idx(self):
        return self._word_idx


@extend_commands
class ManagerShell(cmd.Cmd):
    prompt = "slm> "

    def __init__(self, manager):
        """slm shell

        :manager: slm instance
        """
        super().__init__()
        self._manager = manager
        self._login_info_manager = manager.login_info_manager()
        self.allow_cli_args = False
        self._completer_state = CompleterState(self)
        self._keyboard = Controller()

    #        readline.set_completion_display_matches_hook(
    #                create_completion_display_matches_func(self))

    def update(self):
        self._login_info_manager = self._manager.login_info_manager()

    def clear_completer_state(self):
        self._completer_state.clear()

    def move_cursor_left(self, n):
        while n > 0:
            self._keyboard.press(Key.left)
            self._keyboard.release(Key.left)
            n -= 1

    def move_cursor_right(self, n):
        while n > 0:
            self._keyboard.press(Key.right)
            self._keyboard.release(Key.right)
            n -= 1

    def tab(self, n):
        while n > 0:
            self._keyboard.press(Key.tab)
            self._keyboard.release(Key.tab)
            n -= 1

    def complete(self, text, state):
        try:
            return self._completer_state.try_complete(state)
        except Exception:
            logger.exception("try_complete failed")
            return None

    def do_quit(self, arg):
        return True

    def do_exit(self, arg):
        return True

    def precmd(self, line):
        line = super().precmd(line)
        if line == "EOF":
            # CTRL-d will generate a line of 'EOF', if we meet 'EOF', we change it to 'quit'
            print()
            return "quit"
        return line

    def postcmd(self, stop, line):
        if stop:
            self._manager.close()
        if line != "":
            print()
        return stop


class Manager(object):
    def __init__(self, config_path):
        """

        :config_path: path of config file

        """
        self._stopped = False
        with open(config_path, "r") as fin:
            config = yaml.safe_load(fin)
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
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "root_formatter": {
                        "format": "%(asctime)s|%(levelname)s|%(name)s|line:%(lineno)s|func:%(funcName)s|%(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    }
                },
                "handlers": {
                    "root_handler": {
                        "level": "DEBUG",
                        "class": "logging.FileHandler",
                        "formatter": "root_formatter",
                        "filename": log_file_path,
                    }
                },
                "loggers": {
                    "": {
                        "handlers": ["root_handler"],
                        "level": setting.LOG_LEVEL,
                        "propagate": True,
                    },
                    "libtmux": {
                        "handlers": ["root_handler"],
                        "level": "INFO",
                        "propagate": True,
                    },
                    "py.warnings": {
                        "handlers": ["root_handler"],
                        "level": "ERROR",
                        "propagate": True,
                    },
                },
            }
        )

        logging.captureWarnings(True)

    def _make_sure_directory_exists(self, path):
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    def close(self):
        print("bye!")

    def login_info_manager(self):
        return self._login_info_manager

    def reload(self, shell):
        self._login_info_manager = LoginInfoManager(self._login_info_root_path)
        shell.update()

    def run(self):
        """start a running loop"""
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
