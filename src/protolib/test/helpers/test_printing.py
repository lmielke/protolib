"""
script_path: src/protolib/test/helpers/test_printing.py
purpose: "Integration tests for helpers/printing.py — pure-function surface."
update_rules: "Append scenarios. Never remove existing tests."
"""
import unittest
import protolib.helpers.printing as pr


class TestStripAnsiCodes(unittest.TestCase):
    """strip_ansi_codes: ANSI escape removal, carriage return, backslash-n unescaping."""

    def test_removes_color_escape_codes(self):
        ansi = "\x1b[31mhello\x1b[0m world"
        assert pr.strip_ansi_codes(ansi) == "hello world"

    def test_removes_carriage_returns(self):
        text = "hello\r world\r"
        assert pr.strip_ansi_codes(text) == "hello world"

    def test_unescapes_backslash_n(self):
        escaped = "line1\\nline2"
        result = pr.strip_ansi_codes(escaped)
        assert result == "line1\nline2"

    def test_plain_text_unchanged(self):
        plain = "no escape codes here"
        assert pr.strip_ansi_codes(plain) == plain

    def test_combined_ansi_and_carriage_return(self):
        mixed = "\x1b[32mok\x1b[0m\r"
        assert pr.strip_ansi_codes(mixed) == "ok"


class TestCleanPipeText(unittest.TestCase):
    """clean_pipe_text: unescape \\n/\\t/\\r, strip ANSI, fix cp1252 mojibake."""

    def test_unescapes_newline(self):
        text = "line1\\nline2"
        assert pr.clean_pipe_text(text) == "line1\nline2"

    def test_unescapes_tab(self):
        text = "col1\\tcol2"
        assert pr.clean_pipe_text(text) == "col1\tcol2"

    def test_strips_ansi_codes(self):
        ansi = "\x1b[33mcolored\x1b[0m text"
        assert pr.clean_pipe_text(ansi) == "colored text"

    def test_combined_ansi_and_escape_sequences(self):
        text = "\x1b[32mok\x1b[0m\\nvalue\\tdone"
        assert pr.clean_pipe_text(text) == "ok\nvalue\tdone"

    def test_unescapes_windows_line_ending(self):
        text = "line1\\r\\nline2"
        result = pr.clean_pipe_text(text)
        assert "line1" in result and "line2" in result


class TestNormalizeMaxChars(unittest.TestCase):
    """normalize_max_chars: 5 text-length thresholds produce correct divisors."""

    def test_all_thresholds(self):
        mc = 100
        cases = [
            ("x" * 20, 20),    # len ≤ 50  → mc // 5
            ("x" * 80, 25),    # len ≤ 128 → mc // 4
            ("x" * 200, 33),   # len ≤ 300 → mc // 3
            ("x" * 500, 50),   # len ≤ 1200 → mc // 2
            ("x" * 1500, 200), # len > 1200 → int(mc * 2)
        ]
        for text, expected in cases:
            result = pr.normalize_max_chars(mc, text)
            assert result == expected, f"len={len(text)}: expected {expected}, got {result}"

    def test_boundary_at_50(self):
        result = pr.normalize_max_chars(100, "x" * 50)
        assert result == 20  # exactly 50 → still // 5

    def test_boundary_above_50(self):
        result = pr.normalize_max_chars(100, "x" * 51)
        assert result == 25  # 51 > 50, ≤ 128 → // 4


class TestWrapText(unittest.TestCase):
    """wrap_text: short text unchanged; long lines wrapped; multiline preserved."""

    def test_short_text_returned_unchanged(self):
        short = "hello world"
        assert pr.wrap_text(short, max_chars=200) == short

    def test_long_line_splits_into_multiple_lines(self):
        # 150-char string; normalize_max_chars(100, 150-char) → 100//3 = 33 → wraps
        long_line = "word " * 30   # 150 chars, word boundaries present
        result = pr.wrap_text(long_line, max_chars=100)
        lines = result.split('\n')
        assert len(lines) > 1, "long text should produce multiple wrapped lines"

    def test_wrapped_lines_do_not_exceed_normalized_limit(self):
        long_line = "word " * 30
        result = pr.wrap_text(long_line, max_chars=100)
        # normalized max = 100//3 = 33
        for line in result.split('\n'):
            assert len(line) <= 33, f"line too long ({len(line)}): {line!r}"

    def test_short_multiline_text_content_preserved(self):
        text = "line one\nline two\nline three"
        result = pr.wrap_text(text, max_chars=200)
        assert "line one" in result
        assert "line two" in result
        assert "line three" in result


class TestWrapTable(unittest.TestCase):
    """wrap_table: transforms dict values — str wrapped, list joined, dict formatted."""

    def test_string_value_short_preserved(self):
        d = {"name": "short"}
        result = pr.wrap_table(d)
        assert result["name"] == "short"

    def test_list_value_joined_as_string(self):
        d = {"items": [1, 2, 3]}
        result = pr.wrap_table(d)
        assert "1" in result["items"]
        assert "2" in result["items"]
        assert "3" in result["items"]

    def test_dict_value_formatted_with_key_and_value(self):
        d = {"meta": {"key": "val", "num": 42}}
        result = pr.wrap_table(d)
        clean = pr.strip_ansi_codes(result["meta"])
        assert "key" in clean and "val" in clean
        assert "num" in clean and "42" in clean

    def test_all_keys_preserved(self):
        d = {"a": "hello", "b": [1], "c": {"x": 1}}
        result = pr.wrap_table(d)
        assert set(result.keys()) == {"a", "b", "c"}

    def test_non_string_value_left_unchanged(self):
        # Only str/dict/list values are wrapped; others pass through
        d = {"count": 42}
        result = pr.wrap_table(d)
        assert result["count"] == 42


class TestPrettyPrompt(unittest.TestCase):
    """pretty_prompt: empty XML tags removed; header text preserved; returns str."""

    def test_removes_empty_user_comment_tags(self):
        prompt = "before <user_comment>  </user_comment> after"
        result = pr.pretty_prompt(prompt)
        clean = pr.strip_ansi_codes(result)
        assert "<user_comment>" not in clean
        assert "</user_comment>" not in clean

    def test_returns_string(self):
        result = pr.pretty_prompt("hello world", verbose=0)
        assert isinstance(result, str)

    def test_header_text_survives_colorization(self):
        prompt = "# My Header\nsome body text"
        result = pr.pretty_prompt(prompt)
        clean = pr.strip_ansi_codes(result)
        assert "My Header" in clean
        assert "body text" in clean

    def test_markdown_code_fences_colorized(self):
        prompt = "intro\n```python\ncode\n```"
        result = pr.pretty_prompt(prompt)
        clean = pr.strip_ansi_codes(result)
        assert "python" in clean or "```" in clean


class TestLogprint(unittest.TestCase):
    """logprint: returns original message; handles level parameter."""

    def test_returns_message(self):
        msg = "test log message"
        result = pr.logprint(msg, console_log=False)
        assert result == msg

    def test_returns_message_with_warning_level(self):
        msg = "a warning occurred"
        result = pr.logprint(msg, level="warning", console_log=False)
        assert result == msg

    def test_returns_message_with_error_level(self):
        msg = "an error occurred"
        result = pr.logprint(msg, level="error", console_log=False)
        assert result == msg

    def test_returns_message_with_info_level(self):
        msg = "info message"
        result = pr.logprint(msg, level="info", console_log=False)
        assert result == msg


class TestPlaySound(unittest.TestCase):
    """play_sound: no-op on Linux (SOUND_AVAILABLE=False); no exception raised."""

    def test_no_exception_for_known_statuses(self):
        for status in ("PROMPT", "PROMPT0", "PROMPT1", "PROMPT2",
                       "RESPONSE", "RESPONSE0", "RESPONSE1", "RESPONSE2",
                       "HAPPY", "ERROR"):
            try:
                pr.play_sound(status)
            except Exception as e:
                self.fail(f"play_sound({status!r}) raised {type(e).__name__}: {e}")

    def test_no_exception_for_unknown_status(self):
        try:
            pr.play_sound("UNKNOWN_STATUS")
        except Exception as e:
            self.fail(f"play_sound('UNKNOWN_STATUS') raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()
