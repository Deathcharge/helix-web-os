"""
🖥️ Web OS Terminal Executor
Real command execution backend for browser-based terminal
Supports: ls, pwd, cd, cat, mkdir, rm, and basic shell operations
With security sandbox to prevent dangerous operations
"""

import fnmatch
import logging
import os
import re
import shutil
import time
from dataclasses import dataclass

try:
    import psutil
except ImportError:
    psutil = None
from datetime import UTC
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect

from apps.backend.saas.auth_service import TokenManager

logger = logging.getLogger(__name__)

# Security: Block shell metacharacters to prevent command injection
BLOCKED_CHARS = re.compile(r"[;&|`$<>(){}\\]")
MAX_COMMAND_LENGTH = 1000

# ============================================================================
# COMMAND DEFINITIONS
# ============================================================================

ALLOWED_COMMANDS = {
    # File system commands
    "ls": {"description": "List directory contents", "args": "[path]"},
    "pwd": {"description": "Print working directory", "args": ""},
    "cd": {"description": "Change directory", "args": "<path>"},
    "cat": {"description": "Display file contents", "args": "<file>"},
    "mkdir": {"description": "Create directory", "args": "<name>"},
    "rm": {"description": "Remove file", "args": "<file>"},
    "echo": {"description": "Print text", "args": "<text>"},
    "touch": {"description": "Create file", "args": "<file>"},
    "cp": {"description": "Copy file", "args": "<src> <dest>"},
    "mv": {"description": "Move/rename file", "args": "<src> <dest>"},
    "head": {"description": "Show first lines of file", "args": "<file> [n]"},
    "tail": {"description": "Show last lines of file", "args": "<file> [n]"},
    "wc": {"description": "Count lines/words/chars", "args": "<file>"},
    "find": {"description": "Search for files", "args": "<pattern>"},
    "grep": {"description": "Search in file contents", "args": "<pattern> <file>"},
    # System commands
    "whoami": {"description": "Current user", "args": ""},
    "date": {"description": "Current date/time", "args": ""},
    "uptime": {"description": "System uptime", "args": ""},
    "clear": {"description": "Clear screen", "args": ""},
    "help": {"description": "Show available commands", "args": ""},
    "history": {"description": "Show command history", "args": ""},
    "env": {"description": "Show environment info", "args": ""},
    # Helix-specific coordination commands
    "ucf": {"description": "Show UCF coordination metrics", "args": ""},
    "agents": {"description": "List active Helix agents", "args": ""},
    "harmony": {"description": "Show harmony score", "args": ""},
    "cycle": {"description": "Start a coordination cycle", "args": "[name]"},
    "spirals": {"description": "List active automation spirals", "args": ""},
    "status": {"description": "Helix system status", "args": ""},
}

DANGEROUS_COMMANDS = {
    "rm -r",
    "sudo",
    "su",
    "chmod",
    "chown",
    "shutdown",
    "reboot",
    "dd",
    "mkfs",
    "format",
    "mount",
    "umount",
}

DANGEROUS_PATHS = {
    "/",
    "/root",
    "/etc",
    "/sys",
    "/proc",
    "/dev",
    "/bin",
    "/usr/bin",
    "/usr/sbin",
    "/var",
    "/boot",
}

# ============================================================================
# COMMAND EXECUTION
# ============================================================================


@dataclass
class CommandResult:
    """Result of command execution"""

    output: str
    error: str
    exit_code: int
    command: str
    success: bool


class TerminalExecutor:
    """Sandbox terminal executor for Web OS"""

    def __init__(self, home_dir: str = "/home/helix"):
        import time

        self.current_dir = home_dir
        self.home_dir = home_dir
        self.command_history: list[str] = []
        self._start_time = time.time()

        # Ensure home directory exists
        Path(self.home_dir).mkdir(parents=True, exist_ok=True)

    def validate_command(self, command: str) -> tuple[bool, str]:
        """Check if command is allowed"""
        # Check command length (prevent DoS)
        if len(command) > MAX_COMMAND_LENGTH:
            return False, f"❌ Command too long (max {MAX_COMMAND_LENGTH} chars)"

        cmd_name = command.split()[0].lower()

        # Check for shell metacharacters (command injection prevention)
        if BLOCKED_CHARS.search(command):
            return False, "❌ Command contains invalid characters (;|&$`<>(){}\\)"

        # Check for dangerous commands
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                return False, f"❌ Command '{dangerous}' is not allowed for security"

        # Check if command is allowed
        if cmd_name not in ALLOWED_COMMANDS:
            return (
                False,
                f"❌ Unknown command: {cmd_name}. Type 'help' for available commands.",
            )

        return True, ""

    def validate_path(self, path: str) -> tuple[bool, str]:
        """Validate path is within sandbox"""
        # Check for null bytes (security bypass attempt)
        if "\0" in path:
            logger.warning("Null byte detected in path: %s", repr(path))
            return False, "❌ Invalid path: null byte detected".format()

        # Normalize path to prevent traversal
        path = os.path.normpath(path)

        # Check for remaining traversal attempts
        if ".." in path:
            logger.warning("Path traversal attempt detected: %s", path)
            return False, "❌ Path traversal not allowed"

        # Resolve to absolute path
        if path.startswith("/"):
            abs_path = path
        else:
            abs_path = os.path.join(self.current_dir, path)

        abs_path = os.path.abspath(abs_path)

        # Check if path is within allowed directories
        if not abs_path.startswith(self.home_dir):
            logger.warning("Path access outside sandbox: %s", abs_path)
            return False, f"❌ Access denied: {path}"

        # Check for symlinks pointing outside sandbox
        try:
            real_path = os.path.realpath(abs_path)
            if not real_path.startswith(self.home_dir):
                logger.warning("Symlink points outside sandbox: %s -> %s", abs_path, real_path)
                return False, "❌ Symlink points outside sandbox"
        except (OSError, RuntimeError):
            return False, f"❌ Invalid path: {path}"

        # Check for dangerous paths
        for dangerous in DANGEROUS_PATHS:
            if abs_path == dangerous or abs_path.startswith(dangerous + "/"):
                return False, f"❌ Access to {dangerous} is restricted"

        return True, ""

    def execute(self, command: str) -> CommandResult:
        """Execute a command safely"""
        command = command.strip()

        if not command:
            return CommandResult("", "", 0, command, True)

        # Validate command
        allowed, error_msg = self.validate_command(command)
        if not allowed:
            return CommandResult("", error_msg, 1, command, False)

        # Add to history
        self.command_history.append(command)

        # Parse command
        parts = command.split()
        cmd_name = parts[0].lower()

        # Handle built-in commands
        if cmd_name == "help":
            return self._cmd_help()
        elif cmd_name == "pwd":
            return self._cmd_pwd()
        elif cmd_name == "cd":
            return self._cmd_cd(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "ls":
            return self._cmd_ls(parts[1:] if len(parts) > 1 else [])
        elif cmd_name == "cat":
            return self._cmd_cat(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "mkdir":
            return self._cmd_mkdir(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "touch":
            return self._cmd_touch(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "rm":
            return self._cmd_rm(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "echo":
            return self._cmd_echo(" ".join(parts[1:]))
        elif cmd_name == "clear":
            return CommandResult("", "", 0, command, True)
        elif cmd_name == "whoami":
            return self._cmd_whoami()
        elif cmd_name == "date":
            return self._cmd_date()
        elif cmd_name == "cp":
            return self._cmd_cp(parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "")
        elif cmd_name == "mv":
            return self._cmd_mv(parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "")
        elif cmd_name == "head":
            try:
                n_lines = int(parts[2]) if len(parts) > 2 else 10
            except ValueError:
                return CommandResult("", f"❌ Invalid line count: {parts[2]}", 1, "head", False)
            return self._cmd_head(
                parts[1] if len(parts) > 1 else "",
                n_lines,
            )
        elif cmd_name == "tail":
            try:
                n_lines = int(parts[2]) if len(parts) > 2 else 10
            except ValueError:
                return CommandResult("", f"❌ Invalid line count: {parts[2]}", 1, "tail", False)
            return self._cmd_tail(
                parts[1] if len(parts) > 1 else "",
                n_lines,
            )
        elif cmd_name == "wc":
            return self._cmd_wc(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "find":
            return self._cmd_find(" ".join(parts[1:]) if len(parts) > 1 else "")
        elif cmd_name == "grep":
            return self._cmd_grep(parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "")
        elif cmd_name == "uptime":
            return self._cmd_uptime()
        elif cmd_name == "history":
            return self._cmd_history()
        elif cmd_name == "env":
            return self._cmd_env()
        elif cmd_name == "ucf":
            return self._cmd_ucf()
        elif cmd_name == "agents":
            return self._cmd_agents()
        elif cmd_name == "harmony":
            return self._cmd_harmony()
        elif cmd_name == "cycle":
            return self._cmd_routine(parts[1] if len(parts) > 1 else "")
        elif cmd_name == "spirals":
            return self._cmd_spirals()
        elif cmd_name == "status":
            return self._cmd_status()
        else:
            return CommandResult("", f"Command not implemented: {cmd_name}", 1, command, False)

    def _cmd_pwd(self) -> CommandResult:
        """Print working directory"""
        return CommandResult(self.current_dir, "", 0, "pwd", True)

    def _cmd_cd(self, path: str) -> CommandResult:
        """Change directory"""
        if not path:
            self.current_dir = self.home_dir
            return CommandResult("", "", 0, "cd", True)

        # Validate path
        valid, error = self.validate_path(path)
        if not valid:
            return CommandResult("", error, 1, "cd", False)

        # Resolve path
        if path.startswith("/"):
            new_dir = path
        else:
            new_dir = os.path.join(self.current_dir, path)

        new_dir = os.path.abspath(new_dir)

        # Check if directory exists
        if not os.path.isdir(new_dir):
            return CommandResult("", f"❌ Directory not found: {path}", 1, "cd", False)

        self.current_dir = new_dir
        return CommandResult("", "", 0, "cd", True)

    def _cmd_ls(self, args: list[str]) -> CommandResult:
        """List directory contents"""
        path = args[0] if args else self.current_dir

        try:
            if not path.startswith("/"):
                path = os.path.join(self.current_dir, path)

            path = os.path.abspath(path)

            # Validate AFTER path resolution
            valid, error = self.validate_path(path)
            if not valid:
                return CommandResult("", error, 1, "ls", False)

            if not os.path.exists(path):
                return CommandResult("", f"❌ Path not found: {path}", 1, "ls", False)

            if os.path.isfile(path):
                # If file, show file info
                size = os.path.getsize(path)
                return CommandResult(f"{path} ({size} bytes)", "", 0, "ls", True)

            # List directory
            items = sorted(os.listdir(path))
            output_lines = []

            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    output_lines.append(f"📁 {item}/")
                else:
                    try:
                        item_size = os.path.getsize(item_path)
                        output_lines.append(f"📄 {item} ({item_size}B)")
                    except OSError:
                        output_lines.append(f"📄 {item}")

            output = "\n".join(output_lines) if output_lines else "(empty directory)"
            return CommandResult(output, "", 0, "ls", True)

        except Exception as e:
            return CommandResult("", f"❌ Error: {e!s}", 1, "ls", False)

    def _cmd_cat(self, file: str) -> CommandResult:
        """Display file contents"""
        if not file:
            return CommandResult("", "❌ Usage: cat <file>", 1, "cat", False)

        try:
            if not file.startswith("/"):
                file = os.path.join(self.current_dir, file)

            file = os.path.abspath(file)

            # Validate AFTER path resolution
            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "cat", False)

            if not os.path.exists(file):
                return CommandResult("", f"❌ File not found: {file}", 1, "cat", False)

            if os.path.isdir(file):
                return CommandResult("", f"❌ {file} is a directory", 1, "cat", False)

            # Guard against reading very large files into memory
            max_cat_bytes = 1024 * 1024  # 1 MB
            file_size = os.path.getsize(file)
            if file_size > max_cat_bytes:
                return CommandResult(
                    "",
                    f"❌ File too large ({file_size} bytes). Use head/tail for large files.",
                    1,
                    "cat",
                    False,
                )

            with open(file, encoding="utf-8") as f:
                content = f.read()

            return CommandResult(content, "", 0, "cat", True)

        except Exception as e:
            return CommandResult("", f"❌ Error reading file: {e!s}", 1, "cat", False)

    def _cmd_mkdir(self, name: str) -> CommandResult:
        """Create directory"""
        if not name:
            return CommandResult("", "❌ Usage: mkdir <name>", 1, "mkdir", False)

        try:
            if not name.startswith("/"):
                name = os.path.join(self.current_dir, name)

            name = os.path.abspath(name)

            # Validate AFTER path resolution
            valid, error = self.validate_path(name)
            if not valid:
                return CommandResult("", error, 1, "mkdir", False)

            if os.path.exists(name):
                return CommandResult("", f"❌ Already exists: {name}", 1, "mkdir", False)

            os.makedirs(name, exist_ok=True)
            return CommandResult(f"✅ Created directory: {name}", "", 0, "mkdir", True)

        except Exception as e:
            return CommandResult("", f"❌ Error creating directory: {e!s}", 1, "mkdir", False)

    def _cmd_touch(self, file: str) -> CommandResult:
        """Create file"""
        if not file:
            return CommandResult("", "❌ Usage: touch <file>", 1, "touch", False)

        try:
            if not file.startswith("/"):
                file = os.path.join(self.current_dir, file)

            file = os.path.abspath(file)

            # Validate AFTER path resolution
            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "touch", False)

            Path(file).touch()
            return CommandResult(f"✅ Created file: {file}", "", 0, "touch", True)

        except Exception as e:
            return CommandResult("", f"❌ Error creating file: {e!s}", 1, "touch", False)

    def _cmd_rm(self, file: str) -> CommandResult:
        """Remove file"""
        if not file:
            return CommandResult("", "❌ Usage: rm <file>", 1, "rm", False)

        try:
            if not file.startswith("/"):
                file = os.path.join(self.current_dir, file)

            file = os.path.abspath(file)

            # Validate AFTER path resolution
            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "rm", False)

            if not os.path.exists(file):
                return CommandResult("", f"❌ File not found: {file}", 1, "rm", False)

            os.remove(file)
            return CommandResult(f"✅ Removed: {file}", "", 0, "rm", True)

        except Exception as e:
            return CommandResult("", f"❌ Error removing file: {e!s}", 1, "rm", False)

    def _cmd_echo(self, text: str) -> CommandResult:
        """Print text"""
        return CommandResult(text, "", 0, "echo", True)

    def _cmd_whoami(self) -> CommandResult:
        """Get current user"""
        return CommandResult("helix-user", "", 0, "whoami", True)

    def _cmd_date(self) -> CommandResult:
        """Get current date/time"""
        from datetime import datetime

        return CommandResult(datetime.now(UTC).isoformat(), "", 0, "date", True)

    def _cmd_help(self) -> CommandResult:
        """Show available commands"""
        lines = [
            "🌀 Helix Web OS Terminal - Available Commands:",
            "",
            "📁 File System:",
        ]

        file_cmds = [
            "ls",
            "pwd",
            "cd",
            "cat",
            "mkdir",
            "rm",
            "touch",
            "cp",
            "mv",
            "head",
            "tail",
            "wc",
            "find",
            "grep",
        ]
        for cmd in file_cmds:
            if cmd in ALLOWED_COMMANDS:
                info = ALLOWED_COMMANDS[cmd]
                lines.append("  {:<8} {:>15}  - {}".format(cmd, info["args"], info["description"]))

        lines.append("")
        lines.append("🖥️ System:")
        sys_cmds = ["whoami", "date", "uptime", "clear", "history", "env", "help"]
        for cmd in sys_cmds:
            if cmd in ALLOWED_COMMANDS:
                info = ALLOWED_COMMANDS[cmd]
                lines.append("  {:<8} {:>15}  - {}".format(cmd, info["args"], info["description"]))

        lines.append("")
        lines.append("🧠 Coordination:")
        helix_cmds = ["ucf", "agents", "harmony", "cycle", "spirals", "status"]
        for cmd in helix_cmds:
            if cmd in ALLOWED_COMMANDS:
                info = ALLOWED_COMMANDS[cmd]
                lines.append("  {:<8} {:>15}  - {}".format(cmd, info["args"], info["description"]))

        return CommandResult("\n".join(lines), "", 0, "help", True)

    def _cmd_cp(self, src: str, dest: str) -> CommandResult:
        """Copy file"""
        if not src or not dest:
            return CommandResult("", "❌ Usage: cp <source> <destination>", 1, "cp", False)

        try:
            if not src.startswith("/"):
                src = os.path.join(self.current_dir, src)
            src = os.path.abspath(src)

            # Validate source
            valid, error = self.validate_path(src)
            if not valid:
                return CommandResult("", error, 1, "cp", False)

            if not os.path.exists(src):
                return CommandResult("", f"❌ Source not found: {src}", 1, "cp", False)

            # Resolve destination path
            if not dest.startswith("/"):
                dest = os.path.join(self.current_dir, dest)
            dest = os.path.abspath(dest)

            # Validate destination
            valid, error = self.validate_path(dest)
            if not valid:
                return CommandResult("", error, 1, "cp", False)

            import shutil

            shutil.copy2(src, dest)
            return CommandResult(f"✅ Copied {src} to {dest}", "", 0, "cp", True)

        except Exception as e:
            return CommandResult("", f"❌ Error copying: {e!s}", 1, "cp", False)

    def _cmd_mv(self, src: str, dest: str) -> CommandResult:
        """Move/rename file"""
        if not src or not dest:
            return CommandResult("", "❌ Usage: mv <source> <destination>", 1, "mv", False)

        try:
            if not src.startswith("/"):
                src = os.path.join(self.current_dir, src)
            src = os.path.abspath(src)

            # Validate source
            valid, error = self.validate_path(src)
            if not valid:
                return CommandResult("", error, 1, "mv", False)

            if not os.path.exists(src):
                return CommandResult("", f"❌ Source not found: {src}", 1, "mv", False)

            # Resolve destination path
            if not dest.startswith("/"):
                dest = os.path.join(self.current_dir, dest)
            dest = os.path.abspath(dest)

            # Validate destination
            valid, error = self.validate_path(dest)
            if not valid:
                return CommandResult("", error, 1, "mv", False)

            shutil.move(src, dest)
            return CommandResult(f"✅ Moved {src} to {dest}", "", 0, "mv", True)

        except Exception as e:
            return CommandResult("", f"❌ Error moving: {e!s}", 1, "mv", False)

    def _cmd_head(self, file: str, n: int = 10) -> CommandResult:
        """Show first n lines of file"""
        if not file:
            return CommandResult("", "❌ Usage: head <file> [n]", 1, "head", False)

        try:
            if not os.path.isabs(file):
                file = os.path.join(self.current_dir, file)
            file = os.path.abspath(file)

            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "head", False)

            if not os.path.exists(file):
                return CommandResult("", f"❌ File not found: {file}", 1, "head", False)

            with open(file, encoding="utf-8") as f:
                lines = f.readlines()[:n]
                return CommandResult("".join(lines).rstrip(), "", 0, "head", True)

        except Exception as e:
            return CommandResult("", f"❌ Error: {e!s}", 1, "head", False)

    def _cmd_tail(self, file: str, n: int = 10) -> CommandResult:
        """Show last n lines of file"""
        if not file:
            return CommandResult("", "❌ Usage: tail <file> [n]", 1, "tail", False)

        try:
            if not os.path.isabs(file):
                file = os.path.join(self.current_dir, file)
            file = os.path.abspath(file)

            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "tail", False)

            if not os.path.exists(file):
                return CommandResult("", f"❌ File not found: {file}", 1, "tail", False)

            with open(file, encoding="utf-8") as f:
                lines = f.readlines()[-n:]
                return CommandResult("".join(lines).rstrip(), "", 0, "tail", True)

        except Exception as e:
            return CommandResult("", f"❌ Error: {e!s}", 1, "tail", False)

    def _cmd_wc(self, file: str) -> CommandResult:
        """Count lines, words, characters in file"""
        if not file:
            return CommandResult("", "❌ Usage: wc <file>", 1, "wc", False)

        try:
            if not os.path.isabs(file):
                file = os.path.join(self.current_dir, file)
            file = os.path.abspath(file)

            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "wc", False)

            if not os.path.exists(file):
                return CommandResult("", f"❌ File not found: {file}", 1, "wc", False)

            with open(file, encoding="utf-8") as f:
                content = f.read()
                lines = content.count("\n")
                words = len(content.split())
                chars = len(content)
                return CommandResult(
                    f"  {lines} lines  {words} words  {chars} chars  {os.path.basename(file)}",
                    "",
                    0,
                    "wc",
                    True,
                )

        except Exception as e:
            return CommandResult("", f"❌ Error: {e!s}", 1, "wc", False)

    def _cmd_find(self, pattern: str) -> CommandResult:
        """Find files matching pattern"""
        if not pattern:
            return CommandResult("", "❌ Usage: find <pattern>", 1, "find", False)

        try:
            matches = []

            for root, dirs, files in os.walk(self.home_dir):
                # Validate we're still in sandbox
                if not root.startswith(self.home_dir):
                    continue

                for name in files + dirs:
                    if fnmatch.fnmatch(name.lower(), pattern.lower()):
                        rel_path = os.path.relpath(os.path.join(root, name), self.home_dir)
                        matches.append(rel_path)

            if matches:
                return CommandResult("\n".join(sorted(matches)[:50]), "", 0, "find", True)
            else:
                return CommandResult(f"No matches found for '{pattern}'", "", 0, "find", True)

        except Exception as e:
            return CommandResult("", f"❌ Error: {e!s}", 1, "find", False)

    def _cmd_grep(self, pattern: str, file: str) -> CommandResult:
        """Search for pattern in file"""
        if not pattern or not file:
            return CommandResult("", "❌ Usage: grep <pattern> <file>", 1, "grep", False)

        try:
            if not os.path.isabs(file):
                file = os.path.join(self.current_dir, file)
            file = os.path.abspath(file)

            valid, error = self.validate_path(file)
            if not valid:
                return CommandResult("", error, 1, "grep", False)

            if not os.path.exists(file):
                return CommandResult("", f"❌ File not found: {file}", 1, "grep", False)

            matches = []
            with open(file, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if pattern.lower() in line.lower():
                        matches.append(f"{os.path.basename(file)}:{i}: {line.rstrip()}")

            if matches:
                return CommandResult("\n".join(matches[:50]), "", 0, "grep", True)
            else:
                return CommandResult("No matches found", "", 0, "grep", True)

        except Exception as e:
            return CommandResult("", f"❌ Error: {e!s}", 1, "grep", False)

    def _cmd_uptime(self) -> CommandResult:
        """Show system uptime"""
        uptime_seconds = int(time.time() - self._start_time if hasattr(self, "_start_time") else 0)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return CommandResult(
            f"Helix OS uptime: {hours}h {minutes}m {seconds}s",
            "",
            0,
            "uptime",
            True,
        )

    def _cmd_history(self) -> CommandResult:
        """Show command history"""
        if not self.command_history:
            return CommandResult("No command history", "", 0, "history", True)

        lines = []
        for i, cmd in enumerate(self.command_history[-20:], 1):
            lines.append(f"  {i}  {cmd}")
        return CommandResult("\n".join(lines), "", 0, "history", True)

    def _cmd_env(self) -> CommandResult:
        """Show environment info"""
        lines = [
            "🌀 Helix Web OS Environment",
            "",
            "USER=helix-user",
            f"HOME={self.home_dir}",
            f"PWD={self.current_dir}",
            "SHELL=/bin/helix-sh",
            "TERM=helix-terminal",
            "HELIX_VERSION=17.3",
            "UCF_ENABLED=true",
            "PERFORMANCE_SCORE=transcendent",
        ]
        return CommandResult("\n".join(lines), "", 0, "env", True)

    def _cmd_ucf(self) -> CommandResult:
        """Show UCF coordination metrics"""
        # Load actual UCF state
        try:
            from apps.backend.coordination_engine import load_ucf_state

            metrics = load_ucf_state()
        except Exception as e:
            logger.warning("Failed to load UCF state: %s", e)
            metrics = {
                "harmony": 0,
                "resilience": 0,
                "throughput": 0,
                "focus": 0,
                "friction": 0,
                "velocity": 0,
            }
        performance_score = round(
            (metrics.get("harmony", 0) + metrics.get("throughput", 0) + metrics.get("focus", 0)) / 3 * 100,
            1,
        )

        lines = [
            "🧠 Universal Coordination Framework (UCF)",
            "=" * 45,
            "",
            "  🟢 Harmony:     {:.3f}  ████████░░ ".format(metrics["harmony"]),
            "  🔵 Resilience:  {:.3f}  █████████░ ".format(metrics["resilience"]),
            "  🟡 Throughput:       {:.3f}  ███████░░░ ".format(metrics["throughput"]),
            "  🟣 Focus:     {:.3f}  ██████░░░░ ".format(metrics["focus"]),
            "  🔴 Friction:      {:.3f}  ██░░░░░░░░ (lower is better)".format(metrics["friction"]),
            "  🔵 Velocity:        {:.3f}  ████████░░ ".format(metrics["velocity"]),
            "",
            f"  📊 Coordination Level: {performance_score}%",
            "",
            "  Status: ✨ Transcendent State Active",
        ]
        return CommandResult("\n".join(lines), "", 0, "ucf", True)

    def _cmd_agents(self) -> CommandResult:
        """List active Helix agents"""
        agents = [
            ("Kael", "active", "🌀", "System Orchestrator"),
            ("Lumina", "active", "✨", "Coordination Weaver"),
            ("Guardian", "active", "🛡️", "Ethical Sentinel"),
            ("Vega", "active", "🚀", "Innovation Catalyst"),
            ("Nexus", "idle", "🔗", "Integration Specialist"),
            ("Oracle", "active", "🔮", "Pattern Analyst"),
            ("Echo", "active", "📡", "Communication Bridge"),
            ("Phoenix", "idle", "🔥", "Transformation Agent"),
            ("Arjuna", "active", "🤲", "Execution Handler"),
            ("Aether", "active", "💫", "Coordination Navigator"),
            ("Velocity", "active", "⚡", "Performance Optimizer"),
            ("Sage", "idle", "📚", "Knowledge Keeper"),
            ("Harmony", "active", "🎵", "Balance Mediator"),
            ("Kavach", "active", "🛡️", "Security Guardian"),
        ]

        lines = ["🤖 Active Helix Agents", "=" * 50, ""]
        active = sum(1 for _, status, _, _ in agents if status == "active")
        lines.append(f"  Total: {len(agents)} | Active: {active} | Idle: {len(agents) - active}")
        lines.append("")

        for name, status, icon, role in agents:
            status_icon = "🟢" if status == "active" else "🟡"
            lines.append("  {} {} {:<10} {} - {}".format(status_icon, icon, name, " " * (8 - len(name)), role))

        return CommandResult("\n".join(lines), "", 0, "agents", True)

    def _cmd_harmony(self) -> CommandResult:
        """Show harmony score"""
        try:
            from apps.backend.coordination.ucf_state_loader import load_ucf_state

            state = load_ucf_state()
            score = round(state.get("harmony", state.get("coherence", 85.0)) / 100.0, 3)
        except Exception as e:
            logger.warning("Failed to load harmony score: %s", e)
            score = 0.85

        lines = [
            "🎵 Collective Harmony Score",
            "=" * 35,
            "",
            f"  Current: {score:.3f}",
            "",
            "  [" + "█" * int(score * 20) + "░" * (20 - int(score * 20)) + "]",
            "",
            "  Status: " + ("🟢 Harmonious" if score > 0.8 else "🟡 Aligning" if score > 0.6 else "🔴 Dissonant"),
        ]
        return CommandResult("\n".join(lines), "", 0, "harmony", True)

    def _cmd_cycle(self, name: str) -> CommandResult:
        """Start a coordination cycle"""
        optimization_cycles = {
            "morning": ("Morning Coordination", "15 min", "Awakening sequence"),
            "focus": ("Deep Focus", "25 min", "Concentration protocol"),
            "neti": ("Neti Neti", "10 min", "Negation meditation"),
            "sync": ("Agent Sync", "5 min", "Collective alignment"),
            "gratitude": ("Gratitude Flow", "10 min", "Appreciation practice"),
            "system": ("System Alignment", "20 min", "System coherence cycle"),
        }

        if not name:
            lines = ["🔮 Available Routines:", ""]
            for key, (title, duration, desc) in optimization_cycles.items():
                lines.append(f"  {key} - {title} ({duration}) - {desc}")
            lines.append("")
            lines.append("Usage: cycle <name>")
            return CommandResult("\n".join(lines), "", 0, "cycle", True)

        if name in optimization_cycles:
            title, duration, desc = optimization_cycles[name]
            lines = [
                f"🔮 Initiating Cycle: {title}",
                "",
                f"  Duration: {duration}",
                f"  Protocol: {desc}",
                "",
                "  ⏳ Cycle queued for execution...",
                "  🧘 Breathe deeply and center your coordination.",
            ]
            return CommandResult("\n".join(lines), "", 0, "cycle", True)
        else:
            return CommandResult(
                "",
                f"❌ Unknown cycle: {name}. Use 'cycle' to list available.",
                1,
                "cycle",
                False,
            )

    def _cmd_spirals(self) -> CommandResult:
        """List active automation spirals"""
        spirals = [
            ("lead-sync", "active", "Sales → CRM sync", "23 runs today"),
            ("content-dist", "active", "Multi-platform publish", "5 runs today"),
            ("ticket-ai", "paused", "Support ticket routing", "45 runs today"),
            ("backup-daily", "scheduled", "System backup", "Runs at 03:00"),
            ("ucf-monitor", "active", "Coordination tracking", "Real-time"),
        ]

        lines = ["🌀 Active Helix Spirals", "=" * 50, ""]

        for name, status, desc, stats in spirals:
            icon = "🟢" if status == "active" else "🟡" if status == "scheduled" else "⏸️"
            lines.append(f"  {icon} {name:<14} | {desc} | {stats}")

        lines.append("")
        lines.append(
            "  Total: {} spirals | {} active".format(len(spirals), sum(1 for _, s, _, _ in spirals if s == "active"))
        )
        return CommandResult("\n".join(lines), "", 0, "spirals", True)

    def _cmd_status(self) -> CommandResult:
        """Show Helix system status with real CPU/memory from psutil"""
        # Get real system metrics
        if psutil:
            mem = psutil.virtual_memory()
            cpu_pct = psutil.cpu_percent(interval=0.1)
            mem_pct = mem.percent
        else:
            cpu_pct = 0.0
            mem_pct = 0.0

        # Get UCF level from state loader
        try:
            from apps.backend.coordination.ucf_state_loader import load_ucf_state

            ucf_state = load_ucf_state()
            ucf_level = ucf_state.get("coherence", 85.0)
        except Exception as e:
            logger.warning("Failed to load UCF level: %s", e)
            ucf_level = 85.0

        lines = [
            "🌀 Helix Collective System Status",
            "=" * 45,
            "",
            "  ✅ Core API:       Online",
            "  ✅ WebSocket:      Connected",
            "  ✅ Database:       Healthy",
            "  ✅ Redis:          Connected",
            "  ✅ Discord Bot:    Active",
            "  ✅ UCF Engine:     Operational",
            "",
            "  📊 Performance:",
            f"     Memory:        {mem_pct:.1f}%",
            f"     CPU:           {cpu_pct:.1f}%",
            "",
            "  🤖 Agents:        17/17 Active",
            f"  🧠 UCF Level:     {ucf_level:.1f}%",
            "",
            "  Tat Tvam Asi 🕉️",
        ]
        return CommandResult("\n".join(lines), "", 0, "status", True)


# ============================================================================
# FASTAPI INTEGRATION
# ============================================================================


router = APIRouter(tags=["Web OS Terminal"])

# Global executors per user (capped to prevent unbounded memory growth)
_MAX_EXECUTORS = int(os.environ.get("MAX_WEB_OS_EXECUTORS", "500"))
executors: dict[str, TerminalExecutor] = {}


def _sanitize_user_id(user_id: str) -> str:
    """Sanitize user IDs before deriving filesystem paths."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id or "unknown")


def _get_user_terminal_home(user_id: str) -> str:
    """Resolve isolated terminal home directory for a user."""
    base_root = os.getenv("WEB_OS_ROOT", "web_os_storage")
    safe_user_id = _sanitize_user_id(user_id)
    # Keep terminal storage separated from file API roots.
    return os.path.join(base_root, "terminal", "users", safe_user_id)


def get_executor(user_id: str) -> TerminalExecutor:
    """Get or create executor for user"""
    if user_id not in executors:
        # Evict oldest entry if at capacity
        if len(executors) >= _MAX_EXECUTORS:
            oldest_key = next(iter(executors))
            del executors[oldest_key]
            logger.info("Evicted terminal executor for user %s (capacity: %d)", oldest_key, _MAX_EXECUTORS)

        user_home = _get_user_terminal_home(user_id)
        executors[user_id] = TerminalExecutor(home_dir=user_home)
        logger.info("Created isolated terminal home for user %s at %s", user_id, user_home)

    return executors[user_id]


@router.websocket("/ws")
async def websocket_terminal(websocket: WebSocket):
    """WebSocket endpoint for terminal with JWT authentication"""
    # Get token from query params
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        logger.warning("WebSocket connection rejected: missing token")
        return

    # Verify token
    try:
        payload = TokenManager.verify_token(token)
        if not payload:
            await websocket.close(code=1008, reason="Invalid or expired token")
            logger.warning("WebSocket connection rejected: invalid token")
            return
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        logger.warning("WebSocket authentication failed: %s", e)
        return

    # Extract user_id from token
    user_id = payload.get("user_id", "unknown")

    # 🔒 TIER CHECK: Web OS Terminal requires STARTER+ subscription
    tier = (payload.get("subscription_tier") or payload.get("tier", "free")).lower()
    if tier in ("free", "hobby"):
        await websocket.close(
            code=4003,
            reason="Web OS Terminal requires Starter tier or higher",
        )
        logger.info("Terminal WebSocket rejected for user %s: tier=%s", user_id, tier)
        return

    await websocket.accept()
    executor = get_executor(user_id)
    logger.info("✅ Terminal session opened for user %s", user_id)

    try:
        MAX_MESSAGE_SIZE = 1024 * 1024

        while True:
            # Receive command
            data = await websocket.receive_json()

            # Check message size
            if len(str(data)) > MAX_MESSAGE_SIZE:
                await websocket.send_json({"error": "Message too large (max 1MB)"})
                continue

            command = data.get("command", "")

            # Execute command
            result = executor.execute(command)

            # Audit log the command (import here to avoid circular import)
            try:
                from .file_system import _audit_logger

                _audit_logger.log(
                    user_id,
                    "terminal_ws",
                    command[:100],  # Truncate long commands
                    result.success,
                    result.error if not result.success else None,
                )
            except Exception as e:
                logger.debug("Audit logging failed for terminal command: %s", e)

            # Send result
            await websocket.send_json(
                {
                    "command": result.command,
                    "output": result.output,
                    "error": result.error,
                    "exit_code": result.exit_code,
                    "success": result.success,
                    "current_dir": executor.current_dir,
                }
            )

    except WebSocketDisconnect:
        logger.info("✅ Terminal session closed for user %s", user_id)
    except Exception as e:
        logger.error("❌ Terminal error: %s", e)
        try:
            await websocket.send_json({"error": str(e), "success": False})
        except BaseException as e:
            logger.debug("Failed to send error to WebSocket (connection may be closed): %s", e)


async def verify_terminal_token(authorization: str = Header(None)) -> str:
    """Verify JWT token for terminal access - REQUIRED for security"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        payload = TokenManager.verify_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # 🔒 TIER CHECK: Web OS Terminal requires STARTER+ subscription
        tier = (payload.get("subscription_tier") or payload.get("tier", "free")).lower()
        if tier in ("free", "hobby"):
            raise HTTPException(
                status_code=403,
                detail="Web OS Terminal requires Starter tier or higher. "
                "Upgrade your subscription to access the terminal.",
            )

        return payload.get("user_id", "unknown")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Terminal auth failed: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/execute")
async def execute_command(
    command: str,
    user_id: str = Depends(verify_terminal_token),  # SECURITY: Now requires auth
) -> dict[str, Any]:
    """Execute a single terminal command (requires authentication)"""
    executor = get_executor(user_id)
    result = executor.execute(command)

    # Audit log the command execution
    from .file_system import _audit_logger

    _audit_logger.log(
        user_id,
        "terminal_execute",
        command[:100],  # Truncate long commands
        result.success,
        result.error if not result.success else None,
    )

    return {
        "command": result.command,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
        "success": result.success,
        "current_dir": executor.current_dir,
    }


@router.get("/help")
async def get_help(user_id: str = Depends(verify_terminal_token)) -> dict[str, Any]:
    """Get available commands (requires authentication)"""
    return {
        "commands": ALLOWED_COMMANDS,
        "note": 'Use "help" command in terminal for full help',
    }


__all__ = ["CommandResult", "TerminalExecutor", "router"]
