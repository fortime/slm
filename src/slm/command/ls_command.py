from treelib import Tree

from .base_command import BaseCommand, register_command

@register_command
class LsCommand(BaseCommand):
    _name = 'ls'

    def run_x(self, node_id, *args):
        tree = self._login_info_manager.tree()
        if node_id not in tree:
            return
        tmp_tree = Tree()
        tmp_tree.create_node(node_id, '')
        has_leef = False
        for tree_node in tree.children(node_id):
            tmp_tree.paste('', tree.subtree(tree_node.identifier))
            has_leef = True
        if not has_leef:
            tmp_tree.get_node('').tag = tree.get_node(node_id).tag
        tmp_tree.show()

    def complete_x(self, line_parser):
        if line_parser.cursor_word_idx() != 1:
            return []
        return self._login_info_manager.search_nodes(line_parser.cursor_word())
