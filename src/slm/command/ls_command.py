from treelib import Tree

from .base_command import BaseCommand, register_command

@register_command
class LsCommand(BaseCommand):
    _name = 'ls'

    def run(self, args):
        tree = self._login_info_manager.tree()
        if not args[0] in tree:
            return
        tmp_tree = Tree()
        tmp_tree.create_node(args[0], '')
        has_leef = False
        for tree_node in tree.children(args[0]):
            tmp_tree.paste('', tree.subtree(tree_node.identifier))
            has_leef = True
        if not has_leef:
            tmp_tree.get_node('').tag = tree.get_node(args[0]).tag
        tmp_tree.show()

    def complete(self, text, line, begidx, endidx):
        return self._login_info_manager.search_nodes(text)
