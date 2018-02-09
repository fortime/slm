import os

from .login_info import LoginInfoNode

class LoginInfoManager(object):

    def __init__(self, root_path):
        """
        :root_path: root path of login info
        """
        self._login_info_nodes_cache = {}
        self._login_info_nodes_id_cache = {}
        self._root_path = root_path
        self._login_info_root_node = LoginInfoNode(self._root_path)
        self._walk_through()

        self._login_info_nodes_ids = sorted(self._login_info_nodes_id_cache.keys())

    def _walk_through(self, path=None, parent_node=None):
        """walk through the root path and find all login info
        """
        if path is None:
            path = self._root_path
            parent_node = self._login_info_root_node
        if not os.path.isdir(path):
            return None

        parent_node.init_login_info()

        for f in os.listdir(path):
            if f.startswith('.'):
                continue
            sub_path = os.path.join(path, f)
            sub_node = LoginInfoNode(sub_path, f, parent_node)
            if os.path.isdir(sub_path):
                self._walk_through(sub_path, sub_node)
            else:
                sub_node.init_login_info()

            nodes = self._login_info_nodes_cache.get(sub_node.name())
            if nodes is None:
                nodes = []
                self._login_info_nodes_cache[sub_node.name()] = nodes
            nodes.append(sub_node)
            self._login_info_nodes_id_cache[sub_node.id()] = sub_node

    def search_nodes(self, text):
        results = []
        if text == '':
            return results
        for id in self._login_info_nodes_ids:
            if text in id:
                results.append((id, self._login_info_nodes_id_cache.get(id)))
        return results

    def list_nodes(self, parent_id):
        results = []
        if parent_id == '':
            return results
        for id in self._login_info_nodes_ids:
            if id.startswith(parent_id):
                results.append((id, self._login_info_nodes_id_cache.get(id)))
        return results

    def print_nodes(self):
        for name, nodes in self._login_info_nodes_cache.items():
            print(name+':')
            count = 0
            for node in nodes:
                print('\t{}:'.format(count))
                print('\t\t{}:[{}]'.format('id', node.id()))
                print('\t\t{}:[{}]'.format('host', node.login_info().host()))
                print('\t\t{}:[{}]'.format('port', node.login_info().port()))
                print('\t\t{}:[{}]'.format('credential', node.login_info().credential()))
                print('\t\t{}:[{}]'.format('next_login_format', node.login_info().next_login_format()))
                print('\t\t{}:[{}]'.format('password_prompt', node.login_info().password_prompt()))
                print('\t\t{}:[{}]'.format('shell_prompt', node.login_info().shell_prompt()))
                print('\t\t{}:[{}]'.format('previous_login', node.login_info().previous_login()))
                print('\t\t{}:[{}]'.format('after_hooks', node.login_info().after_hooks()))
                count += 1
            print('--------')
