"""
script_path: src/protolib/core/creator/python_versions.py
purpose: Cross-platform discovery of installed Python interpreters.
description: |-
  Scans pyenv, uv-managed
  installs, the Windows py launcher, and PATH for python executables, deduplicates
  them, and returns sorted version strings (both full x.y.z and short x.y forms).
  Used by the clone utility to validate user-requested Python versions and to render
  the available choices in clone usage info.
"""
import os, re, subprocess, sys
from colorama import Fore


class PythonVersions:
    """
    purpose: Discovers installed Python interpreters across pyenv, uv, PATH, py launcher.
    """

    _VER_RX = re.compile(r"Python\s+(\d+\.\d+\.\d+)")
    _IS_WIN = sys.platform == "win32"
    _EXE_NAME = "python.exe" if _IS_WIN else "python3"

    def __init__(self, *args, **kwargs):
        self._cache = None

    @classmethod
    def run_cmd(cls, *args, cmd: list, **kwargs) -> str:
        """
        purpose: Execute cmd, return stdout, swallow errors as empty string.
        """
        try: return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        except Exception: return ""

    @classmethod
    def scan_versioned_dir(cls, *args, root: str, **kwargs) -> set:
        """
        purpose: Scan a versioned-install root (pyenv/uv layout) for python exes.
        """
        if not os.path.isdir(root): return set()
        return {p for d in os.listdir(root)
                if os.path.exists(p := cls._exe_in_versioned(root=root, version=d))}

    @classmethod
    def _exe_in_versioned(cls, *args, root: str, version: str, **kwargs) -> str:
        if cls._IS_WIN: return os.path.join(root, version, cls._EXE_NAME)
        return os.path.join(root, version, "bin", cls._EXE_NAME)

    @classmethod
    def from_pyenv(cls, *args, **kwargs) -> set:
        """
        purpose: Discover pyenv-managed python executables.
        """
        home = os.path.expanduser("~")
        roots = [os.path.join(home, ".pyenv", "pyenv-win", "versions"),
                 os.path.join(home, ".pyenv", "versions")]
        return set().union(*(cls.scan_versioned_dir(root=r) for r in roots))

    @classmethod
    def from_uv(cls, *args, **kwargs) -> set:
        """
        purpose: Discover uv-managed python installs under ~/.local/share/uv/python.
        """
        root = os.path.join(os.path.expanduser("~"), ".local", "share", "uv", "python")
        return cls.scan_versioned_dir(root=root)

    @classmethod
    def _path_names(cls, *args, **kwargs) -> list:
        if cls._IS_WIN: return [f"python{s}.exe" for s in ("", "3", "3.11", "3.12", "3.13")]
        return [f"python{s}" for s in ("3", "3.11", "3.12", "3.13", "3.14")]

    @classmethod
    def _dir_exes(cls, *args, directory: str, **kwargs) -> set:
        return {os.path.abspath(exe) for n in cls._path_names()
                if os.path.exists(exe := os.path.join(directory, n))}

    @classmethod
    def from_path(cls, *args, **kwargs) -> set:
        """
        purpose: Discover python executables on PATH.
        """
        sep = ";" if cls._IS_WIN else ":"
        out = set()
        for p in os.environ.get("PATH", "").split(sep):
            if p and os.path.exists(p): out.update(cls._dir_exes(directory=p))
        return out

    @classmethod
    def from_py_launcher(cls, *args, **kwargs) -> set:
        """
        purpose: Discover python executables registered with the Windows py launcher.
        """
        if not cls._IS_WIN: return set()
        out = cls.run_cmd(cmd=["py", "-0p"])
        return {ln.split(": ", 1)[-1] for ln in out.splitlines() if ": " in ln}

    @classmethod
    def version_of(cls, *args, exe: str, **kwargs):
        """
        purpose: Return version string from `exe --version`, or None.
        """
        m = cls._VER_RX.search(cls.run_cmd(cmd=[exe, "--version"]))
        return m.group(1) if m else None

    def _all_exes(self, *args, **kwargs) -> set:
        sources = (self.from_py_launcher(), self.from_pyenv(),
                   self.from_uv(), self.from_path())
        return set().union(*sources)

    def _collect_versions(self, *args, **kwargs) -> set:
        vers = set()
        for exe in self._all_exes():
            v = self.version_of(exe=exe)
            if not v: continue
            vers.add(v)
            vers.add(".".join(v.split(".")[:2]))
        return vers

    @staticmethod
    def _ver_key(*args, ver: str, **kwargs) -> tuple:
        return tuple(int(x) for x in ver.split("."))

    def all(self, *args, **kwargs) -> list:
        """
        purpose: All installed python versions (short + full), sorted ascending.
        """
        if self._cache is not None: return self._cache
        self._cache = sorted(self._collect_versions(), key=lambda s: self._ver_key(ver=s))
        return self._cache

    def full(self, *args, **kwargs) -> list:
        """
        purpose: Full versions only (x.y.z).
        """
        return [v for v in self.all() if v.count(".") == 2]

    def latest(self, *args, **kwargs):
        """
        purpose: Highest installed full version, or None.
        """
        f = self.full()
        return f[-1] if f else None

    def info_string(self, *args, **kwargs) -> str:
        """
        purpose: Render the clone usage banner including available versions.
        """
        ex = self.latest()
        sh = ".".join(ex.split(".")[:2]) if ex else "3.11"
        vals = dict(Y=Fore.YELLOW, C=Fore.CYAN, R=Fore.RESET,
                    example=ex, short=sh, shown=", ".join(self.full()))
        return _INFO_TEMPLATE.format(**vals)


_INFO_TEMPLATE = (
    "{Y}NOTE, to Clone the package use:{R}\n\n"
    "\tproto clone {Y}-pr{R} 'badylib' {Y}-n{R} 'badypackage' "
    "{Y}-a{R} 'bady' {Y}-t{R} '/tmp' {Y}-p{R} '{example}' "
    "{Y}--port{R} 9006 {Y}--install\n\n"
    "Parameter Explained: \n"
    "\t{C}Mandatory:{R} \n"
    "\t{Y}-pr{R} [name of target project], \n"
    "\t{Y}-n{R} [package name used inside project],  \n"
    "\t{Y}-a{R} [package alias],  \n"
    "\t{Y}-t{R} [target directory],  \n"
    "\t{Y}--port{R} [HTTP port for server.py]\n"
    "\t{C}Optionals:{R} \n"
    "\t{Y}-p{R} [Python version for env]  \n"
    "\t{Y}--install{R} [run uv sync]\n"
    "\t{Y}-y{R} [skip confirmation prompts]\n"
    "\nAvailable Python versions: {C}{shown}{R}\n"
    "{Y}Note:{R} You can also use short versions like "
    "{C}{short}{R} if they map to a valid patch (e.g. {example})."
)
