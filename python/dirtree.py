#!/usr/bin/env python3

import click
import os
from pathlib import Path
from anytree import Node, RenderTree
from anytree.render import ContStyle


def print_tree(directory, directories_only=False, max_levels=None, max_lines=None):
    curr_path = Path(directory)
    root_node = Node(str(curr_path.resolve()), dsp_name=f'{curr_path.name}/')
    nodes = { root_node.name: root_node }
    for root_name, d_names, f_names in os.walk(curr_path):
        parent_node = nodes[root_name]
        for d_name in d_names:
            full_name = f'{root_name}/{d_name}'
            node = Node(full_name, dsp_name=f'{d_name}/', parent=parent_node)
            nodes[full_name] = node
        if not directories_only:
            for f_name in f_names:
                full_name = f'{root_name}/{f_name}'
                node = Node(full_name, dsp_name=f_name, parent=parent_node)
                nodes[full_name] = node

    for idx, (pre, _, node) in enumerate(RenderTree(root_node, style=ContStyle(), maxlevel=max_levels)):
        print(f'{pre}{node.dsp_name}')
        if idx == max_lines - 1:
            print('...')
            return


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--directories', is_flag=True, help='Display directories only')
@click.option('-l', '--levels', type=int, help='Max number of nested levels to display')
@click.option('-n', '--lines', type=int, help='Max number of lines to display', default=20)
def main(directories, levels, lines):
    print_tree(os.getcwd(), directories_only=directories, max_levels=levels, max_lines=lines)


if __name__ == '__main__':
    main()
