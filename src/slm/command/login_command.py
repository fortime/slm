import libtmux
import logging
import time

from .base_command import BaseCommand, register_command
from ..setting import setting

logger = logging.getLogger(__name__)

server = libtmux.Server()
session = server.find_where({'session_name': 'login'})
if session is None:
    session = server.new_session(session_name='login')

def wait_until(pane, prompt, timeout):
    outs = pane.cmd('capture-pane', '-p').stdout
    if len(outs) < 1:
        out = ''
    else:
        out = outs[-1].strip()
    total = 0
    while not out.endswith(prompt):
        logger.debug(prompt)
        logger.debug(out)
        time.sleep(0.1)
        total += 0.1
        if total > timeout:
            return False
        outs = pane.cmd('capture-pane', '-p').stdout
        if len(outs) < 1:
            out = ''
        else:
            out = outs[-1].strip()
    return True

@register_command
class LoginCommand(BaseCommand):
    _name = 'login'

    def _login(self, pane, node, login_format, exit):
        login_info = node.login_info()
        credential = login_info.credential()
        if credential is None:
            print('no credential found for {}'.format(node.id()))
            return False
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

    def _run_shell_command(self, pane, command, shell_prompt):
        pane.send_keys(command)
        result = wait_until(pane, shell_prompt, 60)
        return result

    def _chain_login(self, nodes):
        pane = None
        # TODO to solve window name conllision
        target_node = nodes[-1]
        name = target_node.name()
        window = session.find_where({'window_name': name})
        pane = None
        if window is None:
            window = session.new_window(window_name=name)
            pane = window.panes[0]
        else:
            window.select_window()
            pane = window.split_window()
        pane.send_keys('clear')
        login_format = setting.LOGIN_FORMAT
        result = False
        exit = False
        for node in nodes:
            try:
                result = self._login(pane, node, login_format, exit)
                exit = True and (node.login_info().unable_auto_exit() is None or not node.login_info().unable_auto_exit())
            except Exception:
                logger.warn('unknow error', exc_info=True)
                result = False
            if not result:
                print('login {} failed'.format(node.id()))
                logger.info('login {} failed', node.id())
                return result
            login_format = node.login_info().next_login_format()
        after_hooks = target_node.login_info().after_hooks()
        if after_hooks is not None and isinstance(after_hooks, list):
            shell_prompt = target_node.login_info().shell_prompt()
            for command in after_hooks:
                hook_result = self._run_shell_command(pane, command, shell_prompt)
                if not hook_result:
                    print('run {} failed after login'.format(command))
                    break
        return result

    def login(self, node):
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
        self._chain_login(chain_nodes)

    def run(self, args):
        node = self._login_info_manager.node(args[0])
        if node is None:
            print('{} does not exist'.format(args[0]))
            return
        if node.login_info().host() is None:
            print('there is no host in {}'.format(args[0]))
            return
        self.login(node)

    def complete(self, text, line, begidx, endidx):
        nodes = self._login_info_manager.search_nodes(text, False)
        results = []
        for id, node in nodes:
            if node.login_info().host() is not None:
                results.append(id)
        return results
