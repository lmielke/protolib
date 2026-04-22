"""
script_path: src/protolib/test/app/apis/test_select_files.py
purpose: "Integration tests for app/apis/select_files.py — import graph CLI wrapper."
update_rules: "Append scenarios. Never remove existing tests."
"""
import os, unittest
from protolib.app.apis.select_files import main, _no_target_msg, _format_output


class TestNoTargetMsg(unittest.TestCase):
    """_no_target_msg: returns usage string."""

    def test_contains_usage(self, *args, **kwargs):
        msg = _no_target_msg()
        assert "no target provided" in msg
        assert "Usage:" in msg


class TestFormatOutput(unittest.TestCase):
    """_format_output: format file list for display."""

    def test_empty_files(self, *args, **kwargs):
        result = _format_output(files=[], path="/tmp/x.py")
        assert "no files found" in result

    def test_plain_list(self, *args, **kwargs):
        files = [{"file_path": "/a.py"}, {"file_path": "/b.py"}]
        result = _format_output(files=files)
        assert "/a.py" in result
        assert "/b.py" in result

    def test_json_output(self, *args, **kwargs):
        files = [{"file_path": "/a.py"}]
        result = _format_output(files=files, as_json=True)
        assert '"file_path"' in result


class TestMain(unittest.TestCase):
    """main: end-to-end with real import graph."""

    def test_no_target_returns_usage(self, *args, **kwargs):
        result = main(tgt_dir=None, target=None)
        assert "no target provided" in result

    def test_settings_file_returns_output(self, *args, **kwargs):
        import protolib.core.settings as sts
        target = os.path.join(sts.core_dir, "settings.py")
        result = main(target=target)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_real_file_returns_string(self, *args, **kwargs):
        import protolib.core.settings as sts
        target = os.path.join(sts.apis_dir, "select_files.py")
        if not os.path.exists(target):
            return
        result = main(target=target)
        assert isinstance(result, str)


if __name__ == '__main__':
    unittest.main()
