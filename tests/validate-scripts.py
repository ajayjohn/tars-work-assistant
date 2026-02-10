#!/usr/bin/env python3
"""Validate script health: executable, shebangs, stdlib-only imports."""

import ast
import os
import stat
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PLUGIN_ROOT, "scripts")

# Python standard library modules (comprehensive list for Python 3.8+)
# This is not exhaustive but covers the most common stdlib modules
STDLIB_MODULES = {
    # Built-in modules
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii", "binhex",
    "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb", "chunk",
    "cmath", "cmd", "code", "codecs", "codeop", "collections", "colorsys",
    "compileall", "concurrent", "configparser", "contextlib", "contextvars",
    "copy", "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses",
    "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
    "distutils", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "formatter",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io",
    "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc", "nis",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev",
    "parser", "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtpd",
    "smtplib", "sndhdr", "socket", "socketserver", "spwd", "sqlite3",
    "sre_compile", "sre_constants", "sre_parse", "ssl", "stat", "statistics",
    "string", "stringprep", "struct", "subprocess", "sunau", "symtable",
    "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib",
    "tempfile", "termios", "test", "textwrap", "threading", "time",
    "timeit", "tkinter", "token", "tokenize", "trace", "traceback",
    "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib",
    # Common sub-modules people import from
    "collections.abc", "concurrent.futures", "email.mime",
    "http.client", "http.server", "importlib.metadata",
    "logging.handlers", "multiprocessing.pool",
    "os.path", "unittest.mock", "urllib.parse", "urllib.request",
    "xml.etree", "xml.etree.ElementTree",
}


def check_executable(filepath):
    """Check if file has executable permission."""
    st = os.stat(filepath)
    return bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def check_shebang(filepath):
    """Check if file has a proper shebang line. Returns (has_shebang, shebang_line)."""
    try:
        with open(filepath, "rb") as f:
            first_line = f.readline().decode("utf-8", errors="replace").strip()
    except Exception:
        return False, ""

    if first_line.startswith("#!"):
        return True, first_line
    return False, ""


def get_python_imports(filepath):
    """Parse Python file and extract all imported module names."""
    try:
        with open(filepath) as f:
            source = f.read()
    except Exception:
        return [], "Cannot read file"

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [], f"Syntax error: {e}"

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Get top-level module name
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return sorted(imports), None


def is_stdlib_module(module_name):
    """Check if a module name is part of Python standard library."""
    # Check direct match
    if module_name in STDLIB_MODULES:
        return True
    # Check if it's a private/internal module (starts with _)
    if module_name.startswith("_"):
        return True
    return False


def main():
    errors = []
    warnings = []

    if not os.path.isdir(SCRIPTS_DIR):
        errors.append("scripts/ directory not found")
        print_results(errors, warnings)
        return 1

    script_files = []
    for entry in sorted(os.listdir(SCRIPTS_DIR)):
        full_path = os.path.join(SCRIPTS_DIR, entry)
        if os.path.isfile(full_path) and not entry.startswith("."):
            # Skip __pycache__ and similar
            if entry == "__pycache__" or entry.endswith(".pyc"):
                continue
            script_files.append(entry)

    if not script_files:
        warnings.append("No script files found in scripts/")
        print_results(errors, warnings)
        return 0

    print(f"\n  Found {len(script_files)} scripts to validate\n")

    for script_name in script_files:
        script_path = os.path.join(SCRIPTS_DIR, script_name)

        # --- 1. Check executable permission ---
        if not check_executable(script_path):
            errors.append(f"scripts/{script_name}: Not executable (chmod +x needed)")

        # --- 2. Check shebang ---
        has_shebang, shebang = check_shebang(script_path)
        if not has_shebang:
            errors.append(f"scripts/{script_name}: Missing shebang line")
        else:
            # Validate shebang content
            if script_name.endswith(".py"):
                if "python" not in shebang:
                    warnings.append(f"scripts/{script_name}: Shebang doesn't reference python: {shebang}")
            elif script_name.endswith(".sh"):
                if "bash" not in shebang and "sh" not in shebang:
                    warnings.append(f"scripts/{script_name}: Shebang doesn't reference bash/sh: {shebang}")

        # --- 3. Python-specific checks ---
        if script_name.endswith(".py"):
            imports, parse_err = get_python_imports(script_path)
            if parse_err:
                errors.append(f"scripts/{script_name}: {parse_err}")
            else:
                # Check for non-stdlib imports
                for module in imports:
                    if not is_stdlib_module(module):
                        errors.append(
                            f"scripts/{script_name}: Non-stdlib import '{module}' "
                            f"(all scripts must use only Python standard library)"
                        )

        # --- 4. Shell script checks ---
        if script_name.endswith(".sh"):
            try:
                with open(script_path) as f:
                    content = f.read()
                # Check for common issues
                if "set -e" not in content and "set -eu" not in content:
                    warnings.append(f"scripts/{script_name}: Missing 'set -e' (exit on error)")
            except Exception:
                pass

    print_results(errors, warnings)
    return 1 if errors else 0


def print_results(errors, warnings):
    print("=" * 60)
    print("TARS Script Health Validation")
    print("=" * 60)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")

    if not errors and not warnings:
        print("\n  ✓ All script health checks passed")

    print()
    print(f"Result: {len(errors)} errors, {len(warnings)} warnings")
    if not errors:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    sys.exit(main())
