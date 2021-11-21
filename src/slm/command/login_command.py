import logging

from .base_command import BaseCommand, register_command
from ..login_info.login_info import Property
from ..setting import setting
from ..util.tmux_util import (new_pane_in_window, wait_until,
        new_tiled_panes)

logger = logging.getLogger(__name__)

@register_command
class LoginCommand(BaseCommand):
    _name = 'login'

    def _login(self, pane, node, login_format, exit):
        login_info = node.login_info()
        credential = login_info.credential(is_raw=True)
        if credential == Property.NONE_PROPERTY:
            print('no credential found for {}'.format(node.id()))
            return False
        if self._credential_index is not None and len(credential.values()) > self._credential_index:
            credential = credential.values()[self._credential_index]
        else:
            credential = credential.select_one(node, 'USER')
        login_command = login_format.format(user=credential.get('USER'),
                host=login_info.host(), port=login_info.port())
        if exit:
            login_command += '; exit'
        logger.debug('login_command: %s', login_command)
        pane.send_keys(login_command)
        password = credential.get('PASSWORD')
        if password is not None:
            result = wait_until(pane, login_info.password_prompt(), 60)
            if not result:
                return result
            pane.send_keys(password, suppress_history=False)
        result = wait_until(pane, login_info.shell_prompt(), 60)
        return result

    def _run_shell_command(self, pane, command, shell_prompt, waiting):
        pane.send_keys(command)
        if waiting:
            result = wait_until(pane, shell_prompt, 60)
        else:
            result = True
        return result

    def _chain_login(self, nodes, pane):
        target_node = nodes[-1]
        pane.send_keys('clear')
        login_format = setting.LOGIN_FORMAT
        result = False
        exit = False
        for node in nodes:
            try:
                result = self._login(pane, node, login_format, exit)
                exit = True and (node.login_info().auto_exit_enabled() is None or node.login_info().auto_exit_enabled())
            except Exception:
                logger.warn('unknow error', exc_info=True)
                result = False
            if not result:
                print('login {} failed'.format(node.id()))
                logger.info('login %s failed', node.id())
                return result
            login_format = node.login_info().next_login_format()
        after_hooks = target_node.login_info().after_hooks()
        if after_hooks is not None and isinstance(after_hooks, list):
            shell_prompt = target_node.login_info().shell_prompt()
            count = 1
            for command in after_hooks:
                hook_result = self._run_shell_command(pane, command, shell_prompt, count < len(after_hooks))
                count += 1
                if not hook_result:
                    print('run {} failed after login'.format(command))
                    break
        return result

    def login(self, node, pane):
        chain_nodes = [node]
        previous_login = node.login_info().previous_login()
        while previous_login is not None:
            nodes = self._login_info_manager.nodes_by_name(previous_login)
            if nodes is not None:
                # TODO prompt to let user select
                previous_login = nodes[0].login_info().previous_login()
                chain_nodes.append(nodes[0])
            else:
                previous_login = None

        chain_nodes.reverse()
        self._chain_login(chain_nodes, pane)

    def run_x(self, args):
        node = self._login_info_manager.node(args[0])
        if node is None:
            print('{} does not exist'.format(args[0]))
            return
        if node.login_info().host() is None:
            print('there is no host in {}'.format(args[0]))
            return
        self._credential_index = None
        if len(args) > 1:
            self._credential_index = int(args[1])

        # TODO to solve window name conllision
        # find pane for login
        name = node.name()
        pane = new_pane_in_window(name)

        self.login(node, pane)

    def complete_x(self, parser):
        return self.complete_node(parser.text())

@register_command
class MLoginCommand(LoginCommand):
    """
    Login to multiple nodes of one parent node. It will always open new windows to login.
    There will be 9 panes in a window at most.
    """

    _name = 'mlogin'

    def _find_all_sub_nodes_with_host(self, parent_node):
        """
        Find all sub nodes of parent node

        :parent_node: parent node
        :returns: sub nodes which has host

        """
        sub_nodes = []
        sub_nodes_with_host = []
        if parent_node.has_child():
            sub_nodes.extend(parent_node.children())
        for sub_node in sub_nodes:
            if sub_node.login_info().host() is not None\
                    and not sub_node.login_info().no_batch():
                sub_nodes_with_host.append(sub_node)
            if sub_node.has_child():
                sub_nodes.extend(sub_node.children())
        return sub_nodes_with_host

    def run_x(self, args):
        node = self._login_info_manager.node(args[0])
        if node is None:
            print('{} does not exist'.format(args[0]))
            return
        sub_nodes = self._find_all_sub_nodes_with_host(node)
        if node.login_info().host() is not None:
            sub_nodes.insert(0, node)
        self._credential_index = None
        if len(args) > 1:
            self._credential_index = int(args[1])

        # create tiled panes for login
        panes = new_tiled_panes(args[0], len(sub_nodes))

        for idx in range(0, len(sub_nodes)):
            pane = panes[idx]
            pane.select_pane()
            self.login(sub_nodes[idx], pane)

    def complete_x(self, parser):
        return self._login_info_manager.search_nodes(parser.text())
