import json
import os
import readline
import yaml

from functools import wraps

def heritable(func):
    @wraps(func)
    def from_parent(this, *args, **kwargs):
        is_raw = kwargs.pop('is_raw', False)
        value = func(this, *args, **kwargs)
        if (value is None or value == Property.NONE_PROPERTY) \
                and hasattr(this, 'parent') and hasattr(this.parent, '__call__'):
            parent = this.parent()
            if (parent is not None):
                kwargs['is_raw'] = is_raw
                value = getattr(parent, func.__name__)(*args, **kwargs)
        if isinstance(value, Property) and not is_raw:
            return value.val()
        return value

    return from_parent

class LoginInfoNode(object):
    NODE_CONF = '.base.yaml'

    def __init__(self, path, name=None, parent=None):
        """
        """
        self._path = path
        self._name = name
        if parent is None or parent.id() is None:
            self._id = name
        else:
            self._id = '.'.join((parent.id(), name))
        if self._name is not None:
            if self._name.endswith('.yaml'):
                self._name = self._name[:-5]
            elif self._name.endswith('.yml'):
                self._name = self._name[:-4]
        self._parent = parent
        self._children = []
        self._login_info = None

        if parent is not None:
            parent._add_child(self)

    def _add_child(self, child):
        """add a child node to this node
        :child: child node to be added
        """
        self._children.append(child)

    def __repr__(self):
        return self._id

    def has_child(self):
        return len(self._children) > 0

    def children(self):
        return self._children

    def id(self):
        return self._id

    def login_info(self):
        return self._login_info

    def name(self):
        return self._name

    def parent(self):
        return self._parent

    def path(self):
        return self._path

    def init_login_info(self):
        """
        """
        if self._login_info is not None:
            return

        path = self._path
        if os.path.isdir(path):
            path = os.path.join(path, self.NODE_CONF)
        self._login_info = LoginInfo(self, path)

class Property(object):
    NONE_PROPERTY = None

    def __init__(self, name, prompt_msg=None):
        self._name = name
        self._prompt_msg = prompt_msg
        self._values = None
        self._default_index = None
        self._config_values = None

    def load(self, config):
        values = config.get(self._name)

        if self._values is not None:
            return self

        if values is None and self._name in config:
            # don't want to inherit from parent
            self._values = []
            return self

        self._config_values = values

        tmp_values = []
        default_index = None
        values = values if values is not None else []
        for value in values:
            if isinstance(value, dict):
                if 'DEFAULT' in value and len(value) == 1:
                    default_index = value['DEFAULT']
                else:
                    tmp_values.append(value)
            else:
                tmp_values.append(value)

        if default_index is not None and default_index >= 0 and default_index < len(tmp_values):
            self._default_index = default_index

        if len(tmp_values) == 0:
            return Property.NONE_PROPERTY

        self._values = tmp_values
        return self

    def values(self):
        return self._values

    def select_one(self, node, prompt_key=None):
        if (len(self._values) == 0):
            return None
        elif (len(self._values) == 1):
            return self._values[0]

        prompt_msg = self._prompt_msg
        if prompt_msg is None:
            prompt_msg = 'select a value for {}:'.format(self._name)

        msg = '''
==={}===
{}
{}default: {}

Your choice is: '''
        value_msg = '''{}: {}
'''
        values_msg = ''
        for idx in range(len(self._values)):
            value = self._values[idx]
            if isinstance(value, dict) and prompt_key is not None:
                values_msg += value_msg.format(idx, value[prompt_key])
            else:
                values_msg += value_msg.format(idx, value)
        readline.set_auto_history(False)
        try:
            while True:
                line = input(msg.format(
                    node.id(), prompt_msg, values_msg,
                    0 if self._default_index is None else self._default_index))
                if line.strip() == '':
                    idx = 0 if self._default_index is None else self._default_index
                    return self._values[idx]
                try:
                    idx = int(line.strip())
                    if idx < 0 or idx >= len(self._values):
                        print('Please input a number between 0 and {}!'.format(len(self._values)-1))
                        continue
                    return self._values[idx]
                except Exception:
                    print('Please input a number!')
                    continue
        finally:
            readline.set_auto_history(True)


    def val(self):
        if self._values is None or len(self._values) == 0:
            return None
        if self._default_index is None:
            return self._values[0]
        return self._values[self._default_index]

    def __repr__(self):
        return json.dumps(self._config_values, indent=2)

Property.NONE_PROPERTY = Property(None)

class LoginInfo(object):
    def __init__(self, login_info_node, path):
        self._parent_login_info = login_info_node.parent().login_info() \
                if login_info_node.parent() is not None else None

        self._host = login_info_node.name()
        if os.path.isdir(login_info_node.path()):
            self._host = None

        # format: 'ssh -p{port} {user}@{host}'.format(port=22, user='viewlog', host='127.0.0.1')
        self._next_login_format = None
        self._port = None
        self._credential = Property.NONE_PROPERTY
        self._previous_login = None
        self._after_hooks = Property.NONE_PROPERTY
        self._no_batch = False
        # password prompt: password:
        self._password_prompt = None
        # shell prompt: ]$
        self._shell_prompt = None
        self._auto_exit_enabled = None
        self._login_timeout = Property.NONE_PROPERTY
        self._split_direction = Property.NONE_PROPERTY
        self._load(path)

    def _load(self, path):
        if not os.path.exists(path):
            return
        with open(path, 'r') as fin:
            config = yaml.load(fin)
            self._port = config.get('PORT')
            self._after_hooks = Property('AFTER_HOOKS').load(config)
            self._credential = Property('CREDENTIAL').load(config)
            self._next_login_format = config.get('NEXT_LOGIN_FORMAT')
            self._password_prompt = config.get('PASSWORD_PROMPT')
            self._shell_prompt = config.get('SHELL_PROMPT')
            self._previous_login = config.get('PREVIOUS_LOGIN')
            self._auto_exit_enabled = config.get('AUTO_EXIT_ENABLED')
            self._no_batch = config.get('NO_BATCH')

    @heritable
    def after_hooks(self):
        return self._after_hooks

    @heritable
    def credential(self):
        return self._credential

    def host(self):
        return self._host

    @heritable
    def next_login_format(self):
        return self._next_login_format

    @heritable
    def no_batch(self):
        return self._no_batch

    @heritable
    def auto_exit_enabled(self):
        return self._auto_exit_enabled

    @heritable
    def password_prompt(self):
        return self._password_prompt

    def parent(self):
        return self._parent_login_info

    @heritable
    def port(self):
        return self._port

    @heritable
    def previous_login(self):
        return self._previous_login

    @heritable
    def shell_prompt(self):
        return self._shell_prompt
