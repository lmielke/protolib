"""
script_path: src/protolib/test/core/helpers/setup.py
purpose: "Temp-file + chdir context managers and @test_setup decorator for tests."
description: |-
  Relocated from test/core/testhelper.py. Public API unchanged so that consumer
  imports keep the `testhelper` alias via `test/core/helpers/__init__.py`.
update_rules: "Do not modify in clones."
"""
import os, shutil, functools
from contextlib import contextmanager
from pathlib import Path
import protolib.app.settings as sts


@contextmanager
def temp_chdir(tempDataPath, *args, temp_chdir: Path = None, **kwargs) -> None:
    """purpose: Switch cwd to temp_chdir (or tempDataPath if 'temp_file') for the block."""
    origin = os.getcwd()
    if temp_chdir == 'temp_file':
        if os.path.isfile(tempDataPath): temp_chdir = os.path.dirname(tempDataPath)
        elif os.path.isdir(tempDataPath): temp_chdir = tempDataPath
        else: raise Exception(f"testhelper.temp_chdir.tempDataPath: {tempDataPath} not found")
    temp_chdir = temp_chdir if temp_chdir is not None else os.getcwd()
    try: os.chdir(temp_chdir); yield
    finally: os.chdir(origin)


@contextmanager
def temp_test_file(temp_dir_name: str, *args, temp_file: str, **kwargs) -> None:
    """purpose: Copy test_data_dir/temp_file into a temp subdir named temp_dir_name."""
    if temp_file is None: temp_file = 'empty.txt'
    sourcePath = os.path.join(sts.test_data_dir, temp_file)
    assert os.path.isfile(sourcePath), f"file {sourcePath} not found"
    try:
        tempDir = os.path.join(sts.test_data_dir, temp_dir_name)
        tempPath = os.path.join(tempDir, temp_file)
        if not os.path.isdir(tempDir): os.makedirs(tempDir)
        shutil.copyfile(sourcePath, tempPath)
        yield tempPath
    finally:
        if os.path.exists(tempDir): shutil.rmtree(tempDir, ignore_errors=False, onerror=None)


def test_setup(*args, temp_pass: str = None, **kwargs):
    """purpose: Decorator: wrap a test in temp_test_file + temp_chdir context managers."""
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(self, *inner_args, **inner_kwargs):
            with temp_test_file(test_func.__name__, *args, **kwargs) as tempDataPath:
                with temp_chdir(tempDataPath, *args, **kwargs):
                    return test_func(self, tempDataPath, *inner_args, **inner_kwargs)
        return wrapper
    return decorator
