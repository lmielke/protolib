"""
sts.project_dir/helpers/sys_info/dirs_info.py
Run like: python ./protopy/helpers/sys_info/dirs_info.py -c os_info.py
No description provided
"""


import argparse, colorama, os, re
from typing import Set, List, Tuple
from graphviz import Source, Digraph

import protopy.settings as sts
from protopy.helpers.collections import temp_chdir


class Tree:
    def __init__(self, *args, style=None, ignores:list=None, coloreds:str=None, **kwargs):
        """
        Initialize the Tree object with custom symbols.

        Args:
            dir_sym (str): The symbol to use for directory connections.
            file_sym (str): The symbol to use for file connections.
            fold_sym (str): The symbol to use for directory representation.
        """
        styles = styles_dict.get(style, styles_dict.get('default'))
        # loop over styles dict and assign values to self
        for name, style in styles.items():
            for k, v in style.items():
                setattr(self, f"{name}_{k}", v)
        self.indent = "    "
        self.ignores = ignores if ignores is not None else sts.ignore_dirs
        self.coloreds = coloreds
        self.matches = []


    def mk_tree(self, project_dir: str, max_depth: int = None, **kwargs) -> str:
        """
        Generate a string representation of the directory tree.

        Args:
            project_dir (str): The path to the project directory.
            max_depth (int): The maximum depth for directory traversal (None for unlimited).
            ignores (Set[str]): A set of directory names to ignore.

        Returns:
            str: A string representing the directory tree.
        """
        tree_structure = (
                            f"<hierarchy>\n"
                            f"root: {sts.project_dir = }\n"
                            )
        base_level = project_dir.count(os.sep)
        for root, dirs, files in os.walk(project_dir):
            level = root.count(os.sep) - base_level
            subdir = os.path.basename(root)
            indent_level = self.indent * level
            if any(subdir == ig_dir or subdir.endswith(ig_dir.lstrip("*")) \
                                                                for ig_dir in self.ignores):
                tree_structure += f"{indent_level}{self.disc_sym} {self.fold_sym} {subdir}\n"
                dirs[:] = []  # Do not traverse into this directory
                continue
            if max_depth is not None and level >= max_depth:
                tree_structure += f"{indent_level}{self.disc_sym} {self.fold_sym} {subdir}\n"
                dirs[:] = []  # Do not traverse into this directory
                continue
            tree_structure += f"{indent_level}{self.dir_sym}{self.fold_sym} {subdir}\n"
            log_dir = (subdir in sts.abrev_dirs) and not (subdir in project_dir)
            file_listed = False
            for file in files:
                if self.coloreds is not None:
                    if re.search(self.coloreds, file):
                        self.matches.append(os.path.join(root, file))
                if log_dir and file_listed:
                    tree_structure += f"{indent_level}{self.indent}{self.disc_sym}\n"
                    break
                tree_structure += f"{indent_level}{self.indent}{self.file_sym} {file}\n"
                file_listed = True
        tree_structure += "</hierarchy>"
        if self.coloreds is not None:
            tree_structure = self._colorize(tree_structure)
        return tree_structure

    def _normalize_tree(self, tree: str) -> str:
        """
        Normalize the tree string by adjusting indentation levels.

        Args:
            tree (str): The raw tree string.

        Returns:
            str: The normalized tree string.
        """
        lines = tree.split('\n')
        if not lines:
            return ""

        # Find the minimum indentation level (excluding empty lines)
        min_indent = min(
            (len(line) - len(line.lstrip(self.indent)) for line in lines if line.strip()), 
            default=0
        )

        # Adjust each line to remove the base indentation
        normalized_lines = [line[min_indent:] if line.strip() else line 
                            for line in lines]
        return '\n'.join(normalized_lines).strip()

    def _cleanup_line(self, line, *args, **kwargs):
        """
        take a line from dirs_to_tree and cleanup the line
        """
        line = line.strip()
        is_dir = True if line.startswith(self.dir_sym) else False
        # remove connectors conn
        line = line.replace(self.disc_sym, "")
        line = line.replace(self.dir_sym, '').replace(self.file_sym, '')
        line = line.replace(self.fold_sym, "")
        return line.strip(), is_dir


    def parse_tree(self, tree, *args, **kwargs):
        paths, temps = [], []
        # tree might have indents that are not hierarchy but only display indents
        normalized = self._normalize_tree(tree, *args, **kwargs)
        for i, line in enumerate(normalized.split('\n'), 0):
            if not line or line.startswith(self.disc_sym) or line.startswith('<'):
                continue
            level = line.count(self.indent)
            line, is_dir = self._cleanup_line(line)
            if not line or line == self.disc_sym: continue
            # print(f"{i}, {level = }, {len(temps) = } {line = }")
            if len(temps) < level:
                temps.append(line)
            else:
                temps = temps[:level]
                temps.append(line)
            paths.append((os.path.join(*temps), is_dir))
        return paths

    def mk_dirs_hierarchy(self, dirs, tgt_path, *args, **kwargs):
        start_dir = None
        with temp_chdir(tgt_path):
            for path, is_dir in dirs:
                if not os.path.exists(path):
                    if is_dir:
                        os.makedirs(path)
                        if start_dir is None:
                            start_dir = os.path.join(tgt_path, path)
                    else:
                        with open(path, "w") as f:
                            f.write(f"#{os.path.basename(path)}\n\n")
        return start_dir

    def _colorize(self, tree: str, style: str = 'default') -> str:
        """
        Apply colors to the lines of the tree based on the specified style.

        Args:
            tree (str): The tree string to apply colors to.
            style (str): The style to use for coloring. Default is 'default'.

        Returns:
            str: The colored tree string.
        """
        styles = styles_dict.get(style, styles_dict.get('default'))
        colored_lines = []
        for line in tree.split('\n'):
            for name, style in styles.items():
                symbol, color = style.values()
                if name == 'ext':
                    for sym, col in zip(symbol, color):
                        coloreds = '\\' + self.coloreds if self.coloreds.startswith('.')\
                                                                         else self.coloreds
                        splitted = line.split(' ')
                        splitted[-1] = re.sub(
                                        r'(\S*' + coloreds + ')', 
                                        f"{col}\\1{sts.ST_RESET}", 
                                        splitted[-1]
                                        )
                        line = ' '.join(splitted)
                else:
                    line = line.replace(symbol, f"{color}{symbol}{sts.ST_RESET}")
            colored_lines.append(line)
        return '\n'.join(colored_lines).strip()

    def uncolorize(self, tree: str) -> str:
        """
        Remove color codes from the lines of the tree.

        Args:
            tree (str): The tree string with color codes.

        Returns:
            str: The tree string with color codes removed.
        """
        uncolorized_lines = []
        colors = [
                    colorama.Fore.YELLOW,
                    colorama.Fore.GREEN,
                    colorama.Fore.RED,
                    colorama.Fore.BLUE,
                    colorama.Fore.CYAN,
                    colorama.Fore.WHITE,
                    colorama.Fore.RESET,
                    colorama.Style.DIM,
                    colorama.Style.RESET_ALL,
                    ]
        for line in tree.split('\n'):
            for color in colors:
                line = line.replace(color, "")
            uncolorized_lines.append(line)
        return '\n'.join(uncolorized_lines).strip()

    def to_dot_format(self, root_dir: str) -> Digraph:
        """
        Generate a Graphviz dot format graph of the directory structure from `root_dir`,
        highlighting specified file types based on a regex pattern, using a Digraph object.
        Args:
            root_dir (str): The path to the root directory.
        Returns:
            Digraph: A Digraph object representing the directory structure.
        """
        dot = Digraph(format='svg')
        dot.graph_attr['rankdir'] = 'LR'  # Top-to-Bottom layout
        root_dir = os.path.abspath(root_dir)  # Ensure the root_dir is absolute
        len_root_dir = len(root_dir)
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Filter out directories to ignore
            dirnames[:] = [d for d in dirnames if d not in self.ignores]
            # Create relative path IDs by removing root directory and replacing separators
            relative_path = dirpath[len_root_dir:].strip(os.sep).replace(os.sep, '_')
            path_id = f"node_{relative_path}" if relative_path else "root"
            # Add directory nodes to the graph
            label = os.path.basename(dirpath) if dirpath != root_dir else root_dir
            dot.node(path_id, label=label)
            # Only add edges if it's not the root node
            if dirpath != root_dir:
                parent_path = (
                                os.path.dirname(dirpath)[len_root_dir:]
                                                                        .strip(os.sep).
                                                                        replace(os.sep, '_')
                                )
                parent_id = f"node_{parent_path}" if parent_path else "root"
                dot.edge(parent_id, path_id)
            # Create nodes for files and edges from their directory
            for filename in filenames:
                file_id = f"{path_id}_{filename.replace(os.sep, '_').replace('.', '_')}"
                if self.coloreds and re.search(self.coloreds, filename):
                    dot.node(file_id, label=filename, style='filled', fillcolor='yellow')
                else:
                    dot.node(file_id, label=filename)
                dot.edge(path_id, file_id)
        return dot

    def view_graph(self, root_dir: str, render_format='pdf', view=True):
        """
        Generate and view the Graphviz visualization of the directory structure.
        Args:
            root_dir (str): The path to the root directory.
            render_format (str): The output format for the graph ('pdf', 'png', etc.).
            view (bool): If True, open the rendered graph in the system's default viewer.
        Returns:
            None
        """
        # Generate the dot graph using the to_dot_format method
        dot = self.to_dot_format(root_dir)
        # Render the graph to a file and optionally view it
        filename = os.path.join(root_dir, 'directory_tree')
        # dot.format = render_format
        dot.render('directory_tree', view=view)


styles_dict = {
                'default': {
                                'dir': {
                                    'sym': "|--",
                                    'col': f"{sts.WHITE}"
                                },
                                'file': {
                                    'sym': "|-",
                                    'col': f"{sts.WHITE}"
                                },
                                'fold': {
                                    'sym': "▼",
                                    'col': f"{sts.YELLOW}"
                                },
                                'disc': {
                                    'sym': "|...",
                                    'col': f"{sts.DIM}{sts.WHITE}"
                                },
                                'ext': {
                                    'sym': [".py"],
                                    'col': [f"{sts.BLUE}"]
                                },
                            },
}

def main(*args, **kwargs):
    ignores = sts.ignore_dirs | {'gp', 'models'}
    return f"{Tree(*args, **kwargs).mk_tree(os.getcwd(), *args, **kwargs)}\n"

if __name__ == "__main__":
    # use argparse to provide ignores and colored
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--ignores", nargs="+", default=None)
    p.add_argument("-c", "--coloreds", type=str, default=None)
    print(main(**p.parse_args().__dict__))
    if p.parse_args().coloreds is None:
        print(f"{sts.YELLOW}To color elements use [-c .py]{RESET}")