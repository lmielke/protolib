import ast
import os
import graphviz
import argparse
import protopy.settings as sts

ignore_dirs = {
                ".git",
                "build",
                "gp",
                "dist",
                "models",
                "*.egg-info",
                "__pycache__",
                ".pytest_cache",    
                ".tox",
}

class PackageInfo:
    def __init__(self, *args, main_file_name: str = sts.package_name, **kwargs):
        self.root_dir, self.package_name = self.find_root_dir(*args, **kwargs)
        if not self.root_dir:
            raise RuntimeError("Root directory not found.")
        self.main_file_name = self.handle_file_name(main_file_name)
        self.graph = graphviz.Digraph(comment='Package Dependency Graph')
        self.visited_files = set()
        self.incoming_edges = {}  # Track incoming edges for each node
        # Set default styles for the graph
        self.graph.attr('node', style='filled', fillcolor='white')
        self.graph.attr('edge', fontsize='10')  # Smaller font size for edges

    def handle_file_name(self, main_file_name, *args, **kwargs):
        """
        Handle the main file name to ensure it ends with '.py'.
        """
        if not main_file_name.endswith('.py'):
            main_file_name += '.py'
        return main_file_name

    def find_root_dir(self, start_dir:str=None, *args, **kwargs):
        """
        Determine the root directory of a Python project by locating __main__.py.
        """
        start_dir = start_dir if start_dir is not None else os.getcwd()
        if not sts.package_name in start_dir and sts.package_name not in os.listdir(start_dir):
            raise Exception(
                                f"{sts.RED}package_name '{sts.package_name}' "
                                f"not in start_dir {start_dir}{sts.ST_RESET}"
                                )
        for root, dirs, files in os.walk(start_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            if '__main__.py' in files:
                return os.path.split(root)
        return self.find_root_dir(os.path.dirname(start_dir))

    def build_graph(self, filepath):
        filename = os.path.basename(filepath)
        if filename in self.visited_files:
            return
        self.visited_files.add(filename)

        # Initialize incoming edges count if not already
        if filename not in self.incoming_edges:
            self.incoming_edges[filename] = 0

        imports = self.parse_imports(filepath)
        for imp, origin in imports:
            next_file = self.resolve_module_path_to_file(imp)
            if next_file:
                next_filename = os.path.basename(next_file)
                # Increment the incoming edge count for the target node
                if next_filename not in self.incoming_edges:
                    self.incoming_edges[next_filename] = 0
                self.incoming_edges[next_filename] += 1

                self.graph.edge(filename, next_filename, label=imp)
                self.build_graph(next_file)

    def finalize_graph(self):
        # Determine the maximum number of incoming edges for scaling
        max_edges = max(self.incoming_edges.values(), default=1)
        
        # Set node attributes based on incoming edges
        for node, count in self.incoming_edges.items():
            # Scale the fontsize according to the number of incoming edges
            fontsize = '12' if node == self.main_file_name else str(10 + min(count * 2, 10))
            
            # Calculate the intensity of the red color based on incoming edges
            if max_edges > 0:
                intensity = int(255 * (1 - (count / max_edges)))  # Adjust for a proper scale
            else:
                intensity = 255  # No edges lead to lightest color
            
            fillcolor = f'#{255-intensity:02x}{intensity//1:02x}{intensity//1:02x}'  # Adjusting for lighter shades
            
            # Adjusting the fill color and font size
            self.graph.node(node, fontsize=fontsize, fillcolor=fillcolor, style='filled')
            self.graph.node(node, fontsize=fontsize, fillcolor='lightblue' if node == self.main_file_name else fillcolor)

    def create_import_graph(self, *args, main_file_name:str=None, **kwargs):
        """
        Start the graph creation process from the specified main file.
        """
        main_file_name = main_file_name if main_file_name is not None else self.main_file_name
        main_path = self.locate_file(main_file_name, self.root_dir)
        if not main_path:
            raise FileNotFoundError(f"{main_file_name} not found in {self.root_dir}")
        self.build_graph(main_path)
        self.finalize_graph()  # Apply final node styles based on connectivity
        return self.graph

    def parse_imports(self, filepath):
        """
        Parse a Python file and extract all local import statements relevant to the package.
        """
        with open(filepath, 'r') as file:
            tree = ast.parse(file.read(), filepath)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name.startswith(self.package_name):
                        imports.append((alias.name, os.path.relpath(filepath, self.root_dir).replace(os.sep, '.')))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(self.package_name):
                    for alias in node.names:
                        full_import_path = f"{node.module}.{alias.name}"
                        imports.append((full_import_path, os.path.relpath(filepath, self.root_dir).replace(os.sep, '.')))
        return imports

    def resolve_module_path_to_file(self, module_path):
        """
        Resolve a dot-separated module path to a file path by checking each segment of the path.
        This method iteratively shortens the path from the rightmost segment until a valid file is found.
        """
        module_parts = module_path.split('.')
        for i in range(len(module_parts), 0, -1):
            potential_path = os.path.join(self.root_dir, *module_parts[:i]) + '.py'
            potential_rel = os.path.relpath(potential_path, self.root_dir)
            if os.path.exists(potential_path):
                return potential_path
            else:
                pass
        return None

    def locate_file(self, filename, search_dir):
        """
        Recursively locate a specific file within a given directory.
        """
        for root, dirs, files in os.walk(search_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def analyze_package_imports(self, *args, 
                                        main_file_name: str, 
                                        verbose: int = 1, 
                                **kwargs ) -> str:
        """
        Analyze the import structure of modules in a Python package and generate a graph,
        starting from main file.  Standard library imports are excluded.
        The graph can be visualized if `verbose` is set to a value greater than zero.
            Example triggers: 
                Show me the import structure of my package.
                Display the import graph for my project.
                Where is this module used in my project?
        Args:
            *args: Additional positional arguments. (not relevant here)
            main_file_name (str): The name file to trace imports from.
                Defaults to the package entry file.
            verbose (int, optional): Verbose mode.
                Defaults to 1.
            **kwargs: Additional keyword arguments. (not relevant here)
        Returns:
            str: The Graphviz source code of the generated import graph.
        Example arguments:
            {main_file_name: "info.py", verbose: 1}
        """
        graph = self.create_import_graph(*args, main_file_name=main_file_name, **kwargs)
        dot_source = graph.source
        if verbose:
            graph_filepath = os.path.join(sts.info_logs_dir, "Digraph.gv")
            graph.render(filename=graph_filepath, format="pdf")
            graph.view()
        return dot_source


def set_params(*args, **kwargs):
    parser = argparse.ArgumentParser(description="Analyze Python package structure and visualize import relationships.")
    parser.add_argument('main_file_name', type=str, help='The name of the main Python file to trace imports from.')
    parser.add_argument('--verbose', type=int, default=1,
                        help='Verbose mode. If set to 1 or higher, the graph is displayed.')
    return parser.parse_args().__dict__

def main(*args, **kwargs):
    if not kwargs:
        kwargs = set_params(*args, **kwargs)
    return PackageInfo(*args, **kwargs).analyze_package_imports(*args, **kwargs)

if __name__ == '__main__':
    main()
