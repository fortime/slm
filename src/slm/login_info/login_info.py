import os
import yaml

from functools import wraps

def heritable(func):
    @wraps(func)
    def from_parent(this, *args, **kwargs):
        value = func(this, *args, **kwargs)
        if value is None and hasattr(this, 'parent') and hasattr(this.parent, '__call__'):
            parent = this.parent()
            if (parent is not None):
                return getattr(parent, func.__name__)(*args, **kwargs)
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
    def __init__(self, name, prompt_msg=None):
        self._name = name
        self._prompt_msg = prompt_msg
        self._values = None
        self._default_index = None

    def load(self, values):
        if self._values is not None:
            return self

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

        self._values = tmp_values
        return self

    def val(self):
        # TODO prompt to choose value
        if self._values is None or len(self._values) == 0:
            return None
        if self._default_index is None:
            if len(self._values) == 1:
                return self._values[0]
            return None
        return self._values[self._default_index]

NONE_PROPERTY = Property(None).load([])

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
        self._credential = NONE_PROPERTY
        self._previous_login = None
        self._after_hooks = NONE_PROPERTY
        # password prompt: password:
        self._password_prompt = None
        # shell prompt: ]$
        self._shell_prompt = None
        self._unable_auto_exit = None
        self._login_timeout = NONE_PROPERTY
        self._split_direction = NONE_PROPERTY
        self._load(path)

    def _load(self, path):
        if not os.path.exists(path):
            return
        with open(path, 'r') as fin:
            config = yaml.load(fin)
            self._port = config.get('PORT')
            self._after_hooks = Property('AFTER_HOOKS').load(config.get('AFTER_HOOKS'))
            self._credential = Property('CREDENTIAL').load(config.get('CREDENTIAL'))
            self._next_login_format = config.get('NEXT_LOGIN_FORMAT')
            self._password_prompt = config.get('PASSWORD_PROMPT')
            self._shell_prompt = config.get('SHELL_PROMPT')
            self._previous_login = config.get('PREVIOUS_LOGIN')
            self._unable_auto_exit = config.get('UNABLE_AUTO_EXIT')

    @heritable
    def after_hooks(self):
        return self._after_hooks.val()

    @heritable
    def credential(self):
        return self._credential.val()

    def host(self):
        return self._host

    @heritable
    def next_login_format(self):
        return self._next_login_format

    @heritable
    def unable_auto_exit(self):
        return self._unable_auto_exit

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
