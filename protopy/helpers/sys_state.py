"""
sys_state.py

This module provides a caching mechanism to store and retrieve state information
to optimize repeated function calls by using a decorator. Cached data is stored 
in a YAML file located at `sys.package_dir/helpers/state.yaml`.

Example Usage:
    from sys_state import state_cache

    @state_cache(max_cache_hours=5)
    def get_example_method() -> Dict[str, Any]:
        # Function implementation
        pass
"""

import os, re
from datetime import datetime, timedelta
from tabulate import tabulate as tb
from typing import Any, Dict, Optional, List, Tuple
from functools import wraps
import yaml
import protopy.settings as sts


class State:
    """
    Manages the loading, saving, and updating of cached state data.

    Attributes:
        cache_state_dir: Directory where the cache file is stored.
        cache_state_name: Name of the cache file.
        cache_state_path: Full path to the cache file.
        data: Dictionary storing the cached data.
    """
    def __init__(self, 
                        cache_state_name: Optional[str] = None, 
                        cache_state_dir: Optional[str] = None
        ):
        self.cache_state_dir = cache_state_dir or sts.cache_state_dir
        self.cache_state_name = cache_state_name or sts.cache_state_name
        self.cache_state_path = os.path.join(self.cache_state_dir, self.cache_state_name)
        self.data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """
        Loads the cached data from the cache file if it exists.

        Returns:
            A dictionary with the cached data.
        """
        if os.path.exists(self.cache_state_path):
            try:
                with open(self.cache_state_path, 'r') as f:
                    cache = yaml.safe_load(f)
                    if isinstance(cache, dict):
                        return cache
                    else:
                        return {}
            except (yaml.YAMLError, IOError):
                return {}
        return {}

    def _save_cache(self) -> None:
        """
        Saves the current state data to the cache file.
        """
        os.makedirs(self.cache_state_dir, exist_ok=True)
        with open(self.cache_state_path, 'w') as f:
            yaml.safe_dump(self.data, f)

    def set(self, info_name: str, value: Any) -> None:
        """
        Sets a new value in the cache for the given info name and updates the 
        last update time.

        Args:
            info_name: The key for which to set the cached value.
            value: The value to be cached.
        """
        self.data[info_name] = {
            "value": value,
            "last_update": datetime.now().isoformat()
        }
        self._save_cache()

    def is_valid(self, info_name: str, max_cache_hours: int) -> bool:
        """
        Checks if the cached value for the given info name is still valid based on
        the max cache hours.

        Args:
            info_name: The key for which to check the validity of the cached value.
            max_cache_hours: The maximum number of hours the cache is considered valid.

        Returns:
            True if the cached value is still valid, else False.
        """
        entry = self.data.get(info_name)
        if not entry:
            return False
        last_update = datetime.fromisoformat(entry["last_update"])
        return datetime.now() - last_update < timedelta(hours=max_cache_hours)
    
    def where_used(self) -> List[Tuple[str, int, str, str]]:
        """
        Searches for the usage of the state_cache decorator in .py files within the package directory.

        Returns:
            A list of tuples containing the file path, line number, name of the decorated function, 
            and the decorator line.
        """
        usage_list = []
        for root, _, files in os.walk(sts.package_dir):
            if any(ignored in root for ignored in sts.ignore_dirs):
                continue
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        for idx, line in enumerate(lines):
                            if '@state_cache' in line:
                                # Find the function name following the decorator
                                function_match = re.search(r'def\s+(\w+)\s*\(', lines[idx + 1])
                                if function_match:
                                    function_name = function_match.group(1)
                                    relative_path = os.path.relpath(file_path, sts.package_dir)
                                    usage_list.append((relative_path, idx + 1, function_name, line.strip()))
        return usage_list



def state_cache(max_cache_hours: int = sts.max_cache_hours, \
                cache_state_name: Optional[str] = None, \
                cache_state_dir: Optional[str] = None):
    """
    Decorator that caches the result of the decorated function based on the max cache hours.

    Args:
        max_cache_hours: The maximum number of hours the cache is considered valid.
        cache_state_name: Optional custom cache state file name.
        cache_state_dir: Optional custom directory for the cache state file.

    Returns:
        The decorated function's result from cache if valid, else computes and 
        caches the result.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            info_name = func.__name__
            state = State(cache_state_name=cache_state_name, cache_state_dir=cache_state_dir)
            state_content = state.data.get(info_name, {}).get("value")
            if state.is_valid(info_name, max_cache_hours) and not sts.RED in state_content:
                # print(state_content)
                return state_content
            result = func(*args, **kwargs)
            state.set(info_name, result)
            return result

        return wrapper
    return decorator


if __name__ == "__main__":
    """
    Run like: python ./protopy/helpers/sys_state.py
    """
    state = State()
    usage = state.where_used()
    headers = ["File Path", "Line Number", "Function Name", "Decorator"]
    print(f"\n{sts.YELLOW}Currently this decorator is used by:{sts.RESET}")
    print(tb(usage, headers=headers, tablefmt="psql"))