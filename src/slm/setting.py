"""
Settings like settings in django.
"""


class ReadOnlySetting(object):
    """
    Class of read only setting.
    """

    def __init__(self, default_settings):
        """
        To create a wrapped Setting object, and load default settings.
        """
        self._locked = False
        self._wrapped = Setting()
        self._wrapped.load(default_settings, True)

    def _setup(self, user_settings):
        """
        To load the user settings.

        :user_settings: user settings
        """
        if not self._locked:
            self._wrapped.load(user_settings, True)

    def __getattr__(self, name):
        """
        To get value of name.
        """
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        if name == "lock" or name == "setup":
            return object.__getattribute__(self, name)

        try:
            return getattr(self._wrapped, name)
        except AttributeError as exc:
            raise PFConfigException(errorcode.SETTING_IS_MISSING, str(exc))

    def __setattr__(self, name, value):
        """
        Do nothing.
        """
        if name == "_wrapped" and not hasattr(self, name):
            object.__setattr__(self, name, value)
        # can't change _locked if it is true
        if name == "_locked" and (
            not hasattr(self, name) or not object.__getattribute__(self, name)
        ):
            object.__setattr__(self, name, value)

    def __hasattr__(self, name):
        return name in self._wrapped._overridable_dict

    def __dir__(self):
        return self._wrapped._overridable_dict.keys()

    def lock(self):
        self._locked = True

    def setup(self, user_settings):
        self._setup(user_settings)


class Setting(object):
    """
    Class of setting.
    """

    def __init__(self):
        self._overridable_dict = {}

    def _load_from_list(self, l):
        setting_list = []
        for value in l:
            if isinstance(value, dict):
                read_only_setting = ReadOnlySetting({})
                read_only_setting.setup(value)
                read_only_setting.lock()
                setting_list.append(read_only_setting)
            elif isinstance(value, list):
                sub_setting_list = self._load_from_list(value)
                setting_list.append(sub_setting_list)
            else:
                setting_list.append(value)
        return tuple(setting_list)

    def load(self, settings, overridable=False):
        """
        To load all upper fields from settings.

        :settings: settings to be load
        :overridable: setting from settings is overridable
        """
        for setting, value in settings.items():
            if setting.isupper():
                if (
                    setting not in self._overridable_dict
                    or self._overridable_dict[setting]
                ):
                    if isinstance(value, dict):
                        read_only_setting = ReadOnlySetting({})
                        read_only_setting.setup(value)
                        read_only_setting.lock()
                        setattr(self, setting, read_only_setting)
                    elif isinstance(value, list):
                        setting_list = self._load_from_list(value)
                        setattr(self, setting, setting_list)
                    else:
                        setattr(self, setting, value)
                    self._overridable_dict[setting] = overridable


_default_setting = {
    "HISTORY_FILE_PATH": "~/.slm/slm.hist",
    "LOGIN_INFO_ROOT_PATH": "~/.slm/info",
    "TMP_BIN_PATH": "/tmp/slm/bin",
    "LOG_FILE_PATH": "/tmp/slm/log/slm.log",
    "LOG_LEVEL": "INFO",
}
setting = ReadOnlySetting(_default_setting)
