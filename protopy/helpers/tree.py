import os, re
from typing import Set, List, Tuple
from colorama import Fore, Style
import protopy.settings as sts
from protopy.helpers.collections import temp_chdir

class Tree:
    def __init__(self, *args, style=None, **kwargs):
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
                # Define a dictionary to map Colorama colors to their reset codes


    def mk_tree(self, project_dir: str, max_depth: int = None, ignores: Set[str] = sts.ignore_dirs, colorized=False) -> str:
        """
        Generate a string representation of the directory tree.

        Args:
            project_dir (str): The path to the project directory.
            max_depth (int): The maximum depth for directory traversal (None for unlimited).
            ignores (Set[str]): A set of directory names to ignore.

        Returns:
            str: A string representing the directory tree.
        """
        tree_structure = "<hierarchy>\n"
        base_level = project_dir.count(os.sep)
        for root, dirs, files in os.walk(project_dir):
            level = root.count(os.sep) - base_level
            subdir = os.path.basename(root)
            indent_level = self.indent * level
            if any(subdir == ig_dir or subdir.endswith(ig_dir.lstrip("*")) for ig_dir in ignores):
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
                if log_dir and file_listed:
                    tree_structure += f"{indent_level}{self.indent}{self.disc_sym}\n"
                    break
                tree_structure += f"{indent_level}{self.indent}{self.file_sym} {file}\n"
                file_listed = True
        tree_structure += "</hierarchy>"
        if colorized:
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
                        line = re.sub(r'(\S*\.py)', f"{col}\\1{Style.RESET_ALL}", line)
                else:
                    line = line.replace(symbol, f"{color}{symbol}{Style.RESET_ALL}")
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
                    Fore.YELLOW,
                    Fore.GREEN,
                    Fore.RED,
                    Fore.BLUE,
                    Fore.CYAN,
                    Fore.WHITE,
                    Style.RESET_ALL,
                    Style.DIM,
                    Style.RESET_ALL,
                    ]
        for line in tree.split('\n'):
            for color in colors:
                line = line.replace(color, "")
            uncolorized_lines.append(line)
        return '\n'.join(uncolorized_lines).strip()


styles_dict = {
                'default': {
                                'dir': {
                                    'sym': "|--",
                                    'col': f"{Fore.WHITE}"
                                },
                                'file': {
                                    'sym': "|-",
                                    'col': f"{Fore.WHITE}"
                                },
                                'fold': {
                                    'sym': "▼",
                                    'col': f"{Fore.YELLOW}"
                                },
                                'disc': {
                                    'sym': "|...",
                                    'col': f"{Style.DIM}{Fore.WHITE}"
                                },
                                'ext': {
                                    'sym': [".py"],
                                    'col': [f"{Fore.BLUE}"]
                                },
                            },
}