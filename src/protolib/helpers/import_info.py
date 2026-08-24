"""
script_path: src/protolib/helpers/import_info.py
description: >-
  Parses Python source files using AST to extract import statements and builds a directed
  dependency graph. Renders the graph via graphviz with node styling based on incoming edge
  counts. Used to audit module coupling and detect unexpected cross-layer imports within a
  package.
tags:
- blueprint
- infra
- parsing
"""
import ast, os, argparse
import graphviz
import protolib.app.settings as sts
from protolib.helpers.dir_context import DirContext


class PackageInfo:
    """
    description: 'Builds a graphviz dependency graph by walking AST import statements
        from a main file outward; styles nodes by incoming edge count.'
    """

    def __init__(self, *args, main_file: str = "", **kwargs):
        """description: 'Locate root dir, initialize graphviz Digraph, and set tracking sets.'"""
        self.root_dir, self.package_name = self.find_root_dir(*args, **kwargs)
        if not self.root_dir: raise RuntimeError("Root directory not found.")
        self.main_file = main_file
        self.graph = graphviz.Digraph(comment='Package Dependency Graph')
        self.visited_files, self.visited_paths, self.incoming_edges = set(), set(), {}
        self._init_graph_style(*args, **kwargs)

    def _init_graph_style(self, *args, **kwargs):
        """description: 'Set default graphviz node and edge attributes for the dependency graph.'"""
        self.graph.attr('node', style='filled', fillcolor='white')
        self.graph.attr('edge', fontsize='10')

    def find_root_dir(self, *args, **kwargs):
        """description: 'Walk cwd to find the directory containing __main__.py; return (parent, name).'"""
        for root, dirs, files in os.walk(os.getcwd()):
            dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
            if '__main__.py' in files:
                return os.path.split(root)
        return None

    # ---------- graph building ----------

    def build_graph(self, filepath, *args, **kwargs):
        """description: 'Recursively add filepath and its imports to the graph, skipping already-visited files.'"""
        filename = os.path.basename(filepath)
        if filename in self.visited_files:
            return
        self.visited_files.add(filename)
        self.visited_paths.add(os.path.abspath(filepath))
        self.incoming_edges.setdefault(filename, 0)
        self._add_edges(filepath, filename, *args, **kwargs)

    def _add_edges(self, filepath, filename, *args, **kwargs):
        """description: 'Resolve imports of filepath and add directed edges to the graph for each.'"""
        for imp, origin in self.parse_imports(filepath, *args, **kwargs):
            next_file = self.resolve_module_path_to_file(imp, *args, **kwargs)
            if not next_file: continue
            nf = os.path.basename(next_file)
            self.incoming_edges[nf] = self.incoming_edges.get(nf, 0) + 1
            self.graph.edge(filename, nf, label=imp)
            self.build_graph(next_file, *args, **kwargs)

    def finalize_graph(self, *args, **kwargs):
        """description: 'Apply per-node font size and fill color scaled by incoming edge count.'"""
        max_edges = max(self.incoming_edges.values(), default=1)
        for node, count in self.incoming_edges.items():
            fs, fc = self._node_style(node, count, max_edges, *args, **kwargs)
            self.graph.node(node, fontsize=fs, fillcolor=fc)

    def _node_style(self, node, count, max_edges, *args, **kwargs):
        """description: 'Return (fontsize, fillcolor) for a node based on its incoming edge count.'"""
        fontsize = '12' if node == self.main_file else str(10 + min(count * 2, 10))
        if node == self.main_file:
            return fontsize, 'lightblue'
        intensity = int(255 * (1 - count / max(max_edges, 1)))
        fill = f'#{255 - intensity:02x}{intensity:02x}{intensity:02x}'
        return fontsize, fill

    def create_graph(self, *args, **kwargs):
        """description: 'Locate main_file, build the full import graph, finalize styles, and return it.'"""
        main_path = self.locate_file(self.main_file, self.root_dir, *args, **kwargs)
        if not main_path:
            raise FileNotFoundError(f"{self.main_file} not found in {self.root_dir}")
        self.build_graph(main_path, *args, **kwargs)
        self.finalize_graph(*args, **kwargs)
        return self.graph

    # ---------- imports ----------

    def parse_imports(self, filepath, *args, **kwargs):
        """description: 'Parse filepath and return list of (module_path, origin_rel) import tuples.'"""
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filepath)
        imports = []
        for node in ast.walk(tree):
            self._collect_imports(node, filepath, imports, *args, **kwargs)
        return imports

    def _collect_imports(self, node, filepath, imports, *args, **kwargs):
        """description: 'Dispatch AST node to _collect_import or _collect_from_import as appropriate.'"""
        rel = os.path.relpath(filepath, self.root_dir).replace(os.sep, '.')
        if isinstance(node, ast.Import):
            self._collect_import(node, rel, imports, *args, **kwargs)
        elif isinstance(node, ast.ImportFrom):
            self._collect_from_import(node, rel, imports, *args, **kwargs)

    def _collect_import(self, node, rel, imports, *args, **kwargs):
        """description: 'Append package-internal import aliases to imports list.'"""
        for alias in node.names:
            if alias.name.split('.')[0].startswith(self.package_name):
                imports.append((alias.name, rel))

    def _collect_from_import(self, node, rel, imports, *args, **kwargs):
        """description: 'Append package-internal from-import names as dotted paths to imports list.'"""
        if not (node.module and node.module.startswith(self.package_name)):
            return
        for alias in node.names:
            imports.append((f"{node.module}.{alias.name}", rel))

    # ---------- resolution ----------

    def resolve_module_path_to_file(self, module_path, *args, **kwargs):
        """description: 'Resolve dotted module_path to a .py file path under root_dir, or None.'"""
        parts = module_path.split('.')
        for i in range(len(parts), 0, -1):
            path = os.path.join(self.root_dir, *parts[:i]) + '.py'
            if os.path.exists(path):
                return path
        return None

    def get_file_list(self, *args, **kwargs) -> list[dict]:
        """description: 'Return sorted list of {file_path, file_content} dicts for all visited paths.'"""
        result = []
        for path in sorted(self.visited_paths):
            content = self._read_file(path, *args, **kwargs)
            if content is not None:
                result.append({"file_path": path, "file_content": content})
        return result

    def _read_file(self, path, *args, **kwargs):
        """description: 'Read path as UTF-8 text; return None on any exception.'"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def locate_file(self, filename, search_dir, *args, **kwargs):
        """description: 'Walk search_dir to find filename; return full path or None.'"""
        for root, dirs, files in os.walk(search_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "PackageInfo(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short text showing package name and visited file count.'"""
        return f"PackageInfo(pkg={self.package_name}, visited={len(self.visited_files)})"


# ---------- entry points ----------

def select_files(*args, path: str = None, cursor_pos: int = None, **kwargs) -> list[dict]:
    """description: 'Build import graph from file at path and return list of visited file dicts.'"""
    ctx = DirContext(*args, path=path, cursor_pos=cursor_pos, **kwargs)
    if not ctx.file_name:
        return []
    pkg = PackageInfo(main_file=ctx.file_name)
    pkg.create_graph()
    return pkg.get_file_list()

def set_params(*args, **kwargs):
    """description: 'Parse CLI arguments for main_file_name and verbose; return as dict.'"""
    parser = argparse.ArgumentParser(description="Analyse Python package import graph.")
    parser.add_argument('main_file_name', type=str, help='Main Python file to trace.')
    parser.add_argument('--verbose', type=int, default=1, help='If >=1, open graph viewer.')
    return parser.parse_args().__dict__

def _resolve_args(*args, main_file_name="", verbose=1, **kwargs):
    """description: 'Return (main_file_name, verbose) from kwargs or fall back to CLI via set_params.'"""
    if main_file_name:
        return main_file_name, verbose
    params = set_params(*args, **kwargs)
    return params["main_file_name"], params.get("verbose", verbose)

def main(*args, **kwargs):
    """description: 'Entry point: build and optionally display the import graph; return graph source.'"""
    name, verb = _resolve_args(*args, **kwargs)
    pkg = PackageInfo(main_file=name)
    graph = pkg.create_graph()
    if verb:
        graph.view()
    return graph.source


if __name__ == '__main__':
    main()
