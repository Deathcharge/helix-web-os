"""
📁 Web OS File System
REST API for file operations with sandbox security
Supports: list, read, write, delete, create files/folders
Features: Per-user isolation, audit logging, storage quotas, binary file support
"""

import asyncio
import base64
import json
import logging
import os
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile

logger = logging.getLogger(__name__)


# ============================================================================
# AUDIT LOGGING
# ============================================================================


class AuditLogger:
    """Audit logger for file system operations"""

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.getenv("WEB_OS_AUDIT_DIR", "web_os_storage/audit")
        self.log_dir = log_dir
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)

    def log(
        self,
        user_id: str,
        operation: str,
        path: str,
        success: bool,
        details: str | None = None,
    ):
        """Log an audit event"""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "operation": operation,
            "path": path,
            "success": success,
            "details": details,
        }

        # Write to user-specific audit log
        # Sanitize user_id to prevent path injection
        import re

        safe_user_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id)
        log_file = os.path.join(self.log_dir, f"{safe_user_id}_audit.jsonl")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error("Failed to write audit log: %s", e)

        # Also log to standard logger
        log_msg = f"[AUDIT] user={user_id} op={operation} path={path} success={success}"
        if success:
            logger.info(log_msg)
        else:
            logger.warning("%s details=%s", log_msg, details)


# Global audit logger
_audit_logger = AuditLogger()


# ============================================================================
# STORAGE QUOTA MANAGEMENT
# ============================================================================


class StorageQuotaManager:
    """Manages per-user storage quotas"""

    DEFAULT_QUOTA_MB = 100  # 100MB default per user
    PRO_QUOTA_MB = 1024  # 1GB for pro users
    ENTERPRISE_QUOTA_MB = 10240  # 10GB for enterprise

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.quota_file = os.path.join(base_dir, ".quotas.json")
        self._load_quotas()

    def _load_quotas(self):
        """Load quota settings"""
        self.quotas = {}
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, encoding="utf-8") as f:
                    self.quotas = json.load(f)
            except Exception as e:
                logger.warning("Failed to load quotas from %s: %s", self.quota_file, e)

    def _save_quotas(self):
        """Save quota settings"""
        try:
            with open(self.quota_file, "w", encoding="utf-8") as f:
                json.dump(self.quotas, f)
        except Exception as e:
            logger.error("Failed to save quotas: %s", e)

    def get_user_quota(self, user_id: str) -> int:
        """Get quota for user in bytes"""
        if user_id in self.quotas:
            return self.quotas[user_id].get("quota_bytes", self.DEFAULT_QUOTA_MB * 1024 * 1024)
        return self.DEFAULT_QUOTA_MB * 1024 * 1024

    def set_user_quota(self, user_id: str, quota_mb: int):
        """Set quota for user"""
        if user_id not in self.quotas:
            self.quotas[user_id] = {}
        self.quotas[user_id]["quota_bytes"] = quota_mb * 1024 * 1024
        self._save_quotas()

    def get_user_usage(self, user_dir: str) -> int:
        """Calculate current storage usage for user"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(user_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except OSError:
                    logger.debug("Could not stat file during usage calculation: %s", filepath)
        return total

    def check_quota(self, user_id: str, user_dir: str, additional_bytes: int = 0) -> tuple[bool, str]:
        """Check if user is within quota"""
        quota = self.get_user_quota(user_id)
        usage = self.get_user_usage(user_dir)

        if usage + additional_bytes > quota:
            return (
                False,
                f"Storage quota exceeded. Used: {usage / 1024 / 1024:.1f}MB, Quota: {quota / 1024 / 1024:.1f}MB",
            )
        return True, ""

    def get_quota_info(self, user_id: str, user_dir: str) -> dict:
        """Get quota information for user"""
        quota = self.get_user_quota(user_id)
        usage = self.get_user_usage(user_dir)
        return {
            "quota_bytes": quota,
            "used_bytes": usage,
            "available_bytes": max(0, quota - usage),
            "quota_mb": quota / 1024 / 1024,
            "used_mb": usage / 1024 / 1024,
            "usage_percent": (usage / quota * 100) if quota > 0 else 0,
        }


# Global quota manager
_quota_manager: StorageQuotaManager | None = None


def get_quota_manager() -> StorageQuotaManager:
    """Get or create quota manager"""
    global _quota_manager
    if _quota_manager is None:
        base_storage = os.getenv("WEB_OS_ROOT", "web_os_storage")
        _quota_manager = StorageQuotaManager(base_storage)
    return _quota_manager


# ============================================================================
# FILE SYSTEM MODELS
# ============================================================================


@dataclass
class FileInfo:
    """File information"""

    name: str
    type: str  # 'file' | 'folder'
    path: str
    size: int
    created: str
    modified: str
    readable: bool = True
    writable: bool = True


class FileSystemManager:
    """Secure file system manager for Web OS"""

    def __init__(self, root_dir: str = None):
        if root_dir is None:
            # Use environment variable or default to a relative path
            root_dir = os.getenv("WEB_OS_ROOT", "web_os_storage")

        self.root_dir = root_dir
        self.max_file_size = 10 * 1024 * 1024  # 10MB

        # Create root if needed
        Path(self.root_dir).mkdir(parents=True, exist_ok=True)

        # Create sample structure
        self._create_sample_structure()

    def _create_sample_structure(self):
        """Create sample file structure"""
        # Create directories
        for dir_name in ["projects", "documents", "scripts", "data"]:
            dir_path = os.path.join(self.root_dir, dir_name)
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Create sample files
        sample_files = {
            "README.md": "# Helix Web OS\n\nBrowser-based operating system with file explorer, terminal, and code editor.",
            "projects/sample.py": '#!/usr/bin/env python\n# Sample project\nprint("Hello from Helix!")',
            "documents/notes.txt": "Quick notes and ideas",
            "scripts/backup.sh": "#!/bin/bash\n# Backup script",
        }

        for file_path, content in sample_files.items():
            full_path = os.path.join(self.root_dir, file_path)
            if not os.path.exists(full_path):
                Path(full_path).parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

    def _validate_path(self, path: str) -> tuple[bool, str]:
        """Validate path is within sandbox"""
        # Resolve to absolute path
        if path.startswith("/"):
            abs_path = path
        else:
            abs_path = os.path.join(self.root_dir, path)

        abs_path = os.path.normcase(os.path.abspath(abs_path))
        root = os.path.normcase(os.path.abspath(self.root_dir))

        # Use normcase comparison to handle Windows case-insensitivity
        if not abs_path.startswith(root + os.sep) and abs_path != root:
            return False, f"Access denied: {path}"

        return True, ""

    def list_directory(self, path: str = "") -> tuple[bool, list[FileInfo] | str]:
        """List directory contents"""
        if not path:
            path = self.root_dir

        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            if not os.path.exists(abs_path):
                return False, f"Path not found: {path}"

            if not os.path.isdir(abs_path):
                return False, f"Not a directory: {path}"

            files: list[FileInfo] = []

            for item in sorted(os.listdir(abs_path)):
                item_path = os.path.join(abs_path, item)

                try:
                    is_dir = os.path.isdir(item_path)
                    stat_info = os.stat(item_path)

                    file_info = FileInfo(
                        name=item,
                        type="folder" if is_dir else "file",
                        path=os.path.relpath(item_path, self.root_dir),
                        size=stat_info.st_size if not is_dir else 0,
                        created=datetime.fromtimestamp(stat_info.st_ctime, tz=UTC).isoformat(),
                        modified=datetime.fromtimestamp(stat_info.st_mtime, tz=UTC).isoformat(),
                        readable=os.access(item_path, os.R_OK),
                        writable=os.access(item_path, os.W_OK),
                    )
                    files.append(file_info)
                except Exception as e:
                    logger.warning("Error reading file info: %s", e)
                    continue

            return True, files

        except Exception as e:
            return False, f"Error listing directory: {e!s}"

    def read_file(self, path: str, binary: bool = False) -> tuple[bool, str | bytes | dict]:
        """Read file contents

        Args:
            path: Path to file
            binary: If True, return binary content as base64

        Returns:
            Tuple of (success, content or error message)
            For binary files, returns {"content": base64_string, "is_binary": True}
        """
        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            if not os.path.exists(abs_path):
                return False, f"File not found: {path}"

            if os.path.isdir(abs_path):
                return False, f"Is a directory: {path}"

            # Check file size
            file_size = os.path.getsize(abs_path)
            if file_size > self.max_file_size:
                return (
                    False,
                    f"File too large (max {self.max_file_size / 1024 / 1024}MB)",
                )

            # If binary mode requested, return base64 encoded
            if binary:
                with open(abs_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode("ascii")
                    return True, {
                        "content": content,
                        "is_binary": True,
                        "size": file_size,
                    }

            # Try reading as text first
            try:
                with open(abs_path, encoding="utf-8") as f:
                    return True, f.read()
            except UnicodeDecodeError:
                # File is binary - read as base64
                with open(abs_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode("ascii")
                    return True, {
                        "content": content,
                        "is_binary": True,
                        "size": file_size,
                    }

        except Exception as e:
            return False, f"Error reading file: {e!s}"

    def write_file(
        self,
        path: str,
        content: str | bytes,
        is_binary: bool = False,
        is_base64: bool = False,
    ) -> tuple[bool, str]:
        """Write file contents

        Args:
            path: Path to file
            content: File content (string, bytes, or base64-encoded string)
            is_binary: If True, write as binary
            is_base64: If True, content is base64-encoded and should be decoded

        Returns:
            Tuple of (success, message)
        """
        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            Path(abs_path).parent.mkdir(parents=True, exist_ok=True)

            # Handle base64-encoded content
            if is_base64:
                try:
                    content = base64.b64decode(content)
                    is_binary = True
                except Exception as e:
                    return False, f"Invalid base64 content: {e}"

            # Check size
            content_size = len(content) if isinstance(content, (str, bytes)) else 0
            if content_size > self.max_file_size:
                return (
                    False,
                    f"Content too large (max {self.max_file_size / 1024 / 1024:.1f}MB)",
                )

            # Write file
            if is_binary or isinstance(content, bytes):
                with open(abs_path, "wb") as f:
                    if isinstance(content, str):
                        f.write(content.encode("utf-8"))
                    else:
                        f.write(content)
            else:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return True, f"File written: {path}"

        except Exception as e:
            return False, f"Error writing file: {e!s}"

    def delete_file(self, path: str) -> tuple[bool, str]:
        """Delete file"""
        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            if not os.path.exists(abs_path):
                return False, f"Path not found: {path}"

            if os.path.isdir(abs_path):
                return (
                    False,
                    "Use folder deletion endpoint for directories".format(),
                )

            os.remove(abs_path)
            return True, f"File deleted: {path}"

        except Exception as e:
            return False, f"Error deleting file: {e!s}"

    def delete_folder(self, path: str) -> tuple[bool, str]:
        """Delete folder recursively"""
        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            if not os.path.exists(abs_path):
                return False, f"Path not found: {path}"

            if not os.path.isdir(abs_path):
                return False, f"Not a directory: {path}"

            import shutil

            shutil.rmtree(abs_path)
            return True, f"Folder deleted: {path}"

        except Exception as e:
            return False, f"Error deleting folder: {e!s}"

    def create_folder(self, path: str) -> tuple[bool, str]:
        """Create folder"""
        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            if os.path.exists(abs_path):
                return False, f"Already exists: {path}"

            Path(abs_path).mkdir(parents=True, exist_ok=True)
            return True, f"Folder created: {path}"

        except Exception as e:
            return False, f"Error creating folder: {e!s}"

    def get_file_info(self, path: str) -> tuple[bool, FileInfo | str]:
        """Get file information"""
        valid, error = self._validate_path(path)
        if not valid:
            return False, error

        if not path.startswith("/"):
            path = os.path.join(self.root_dir, path)

        abs_path = os.path.abspath(path)

        try:
            if not os.path.exists(abs_path):
                return False, f"Path not found: {path}"

            stat = os.stat(abs_path)
            is_dir = os.path.isdir(abs_path)

            file_info = FileInfo(
                name=os.path.basename(abs_path),
                type="folder" if is_dir else "file",
                path=os.path.relpath(abs_path, self.root_dir),
                size=stat.st_size if not is_dir else 0,
                created=datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat(),
                modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                readable=os.access(abs_path, os.R_OK),
                writable=os.access(abs_path, os.W_OK),
            )

            return True, file_info

        except Exception as e:
            return False, f"Error getting file info: {e!s}"

    def rename_file(self, old_path: str, new_path: str) -> tuple[bool, str]:
        """Rename or move a file/folder"""
        # Validate both paths
        valid_old, error_old = self._validate_path(old_path)
        if not valid_old:
            return False, error_old

        valid_new, error_new = self._validate_path(new_path)
        if not valid_new:
            return False, error_new

        # Resolve paths
        if not old_path.startswith("/"):
            old_path = os.path.join(self.root_dir, old_path)
        if not new_path.startswith("/"):
            new_path = os.path.join(self.root_dir, new_path)

        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)

        try:
            if not os.path.exists(old_abs):
                return False, f"Source not found: {old_path}"

            if os.path.exists(new_abs):
                return False, f"Destination already exists: {new_path}"

            # Create parent directory if needed
            Path(new_abs).parent.mkdir(parents=True, exist_ok=True)

            # Rename/move
            os.rename(old_abs, new_abs)
            return True, f"Renamed: {old_path} → {new_path}"

        except Exception as e:
            return False, f"Error renaming: {e!s}"


# ============================================================================
# FASTAPI INTEGRATION - PER-USER ISOLATION
# ============================================================================


router = APIRouter(tags=["Web OS Files"])

# Per-user file managers for isolation (capped to prevent unbounded memory growth)
_MAX_FILE_MANAGERS = int(os.getenv("MAX_WEB_OS_FILE_MANAGERS", "500"))
_user_file_managers: dict[str, FileSystemManager] = {}


async def verify_file_token(authorization: str = Header(None)) -> str:
    """Verify JWT token for file system access - REQUIRED for security"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        from apps.backend.saas.auth_service import TokenManager

        payload = TokenManager.verify_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # 🔒 TIER CHECK: Web OS File System requires STARTER+ subscription
        tier = (payload.get("subscription_tier") or payload.get("tier", "free")).lower()
        if tier in ("free", "hobby"):
            raise HTTPException(
                status_code=403,
                detail="Web OS requires Starter tier or higher. Upgrade your subscription to access the file system.",
            )

        return payload.get("user_id", "unknown")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("File system auth failed: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")


def get_user_file_manager(user_id: str) -> FileSystemManager:
    """Get or create a file manager for a specific user"""
    import re

    # Sanitize user_id to prevent path injection
    safe_user_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id)

    if safe_user_id not in _user_file_managers:
        # Evict oldest entry if at capacity to prevent unbounded memory growth
        if len(_user_file_managers) >= _MAX_FILE_MANAGERS:
            oldest_key = next(iter(_user_file_managers))
            del _user_file_managers[oldest_key]
            logger.info("Evicted file manager for user %s (capacity: %d)", oldest_key, _MAX_FILE_MANAGERS)

        # Create user-specific storage directory
        base_storage = os.getenv("WEB_OS_ROOT", "web_os_storage")
        user_root = os.path.join(base_storage, "users", safe_user_id)
        _user_file_managers[safe_user_id] = FileSystemManager(root_dir=user_root)
        logger.info("Created file manager for user: %s", safe_user_id)

    return _user_file_managers[safe_user_id]


@router.get("/list")
def list_files(
    path: str = Query(""),
    user_id: str = Depends(verify_file_token),
):
    """List directory contents (per-user isolated)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.list_directory(path)

    _audit_logger.log(user_id, "list", path or "/", success)

    if not success:
        raise HTTPException(status_code=400, detail=result)

    return {
        "path": path or file_manager.root_dir,
        "files": [
            {
                "name": f.name,
                "type": f.type,
                "path": f.path,
                "size": f.size,
                "created": f.created,
                "modified": f.modified,
            }
            for f in result
        ],
    }


@router.get("/read")
def read_file_endpoint(
    path: str = Query(...),
    binary: bool = Query(False, description="Return binary content as base64"),
    user_id: str = Depends(verify_file_token),
):
    """Read file contents (per-user isolated, supports binary files)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.read_file(path, binary=binary)

    _audit_logger.log(user_id, "read", path, success)

    if not success:
        safe_error = "Failed to read file" if "Error" in str(result) else result
        raise HTTPException(status_code=400, detail=safe_error)

    # Handle binary response
    if isinstance(result, dict) and result.get("is_binary"):
        return {
            "path": path,
            "content": result["content"],
            "is_binary": True,
            "size": result["size"],
        }

    return {"path": path, "content": result, "is_binary": False}


@router.post("/write")
def write_file_endpoint(
    path: str = Query(...),
    content: str = "",
    is_base64: bool = Query(False, description="Content is base64 encoded binary"),
    user_id: str = Depends(verify_file_token),
):
    """Write file contents (per-user isolated, supports binary via base64)"""
    file_manager = get_user_file_manager(user_id)

    # Check quota before writing
    quota_manager = get_quota_manager()
    content_size = len(content) if not is_base64 else len(content) * 3 // 4  # Estimate decoded size
    quota_ok, quota_error = quota_manager.check_quota(user_id, file_manager.root_dir, content_size)

    if not quota_ok:
        _audit_logger.log(user_id, "write", path, False, f"Quota exceeded: {quota_error}")
        raise HTTPException(status_code=413, detail=quota_error)

    success, result = file_manager.write_file(path, content, is_base64=is_base64)

    _audit_logger.log(user_id, "write", path, success, result if not success else None)

    if not success:
        safe_error = "Failed to write file" if "Error" in result else result
        raise HTTPException(status_code=400, detail=safe_error)

    return {"path": path, "message": result}


@router.delete("/file")
def delete_file_endpoint(
    path: str = Query(...),
    user_id: str = Depends(verify_file_token),
):
    """Delete file (per-user isolated)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.delete_file(path)

    _audit_logger.log(user_id, "delete_file", path, success, result if not success else None)

    if not success:
        safe_error = "Failed to delete file" if "Error" in result else result
        raise HTTPException(status_code=400, detail=safe_error)

    return {"message": result}


@router.delete("/folder")
def delete_folder_endpoint(
    path: str = Query(...),
    user_id: str = Depends(verify_file_token),
):
    """Delete folder (per-user isolated)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.delete_folder(path)

    _audit_logger.log(user_id, "delete_folder", path, success, result if not success else None)

    if not success:
        safe_error = "Failed to delete folder" if "Error" in result else result
        raise HTTPException(status_code=400, detail=safe_error)

    return {"message": result}


@router.post("/folder")
def create_folder_endpoint(
    path: str = Query(...),
    user_id: str = Depends(verify_file_token),
):
    """Create folder (per-user isolated)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.create_folder(path)

    _audit_logger.log(user_id, "create_folder", path, success, result if not success else None)

    if not success:
        safe_error = "Failed to create folder" if "Error" in result else result
        raise HTTPException(status_code=400, detail=safe_error)

    return {"message": result}


@router.get("/info")
def get_file_info_endpoint(
    path: str = Query(...),
    user_id: str = Depends(verify_file_token),
):
    """Get file information (per-user isolated)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.get_file_info(path)

    if not success:
        raise HTTPException(status_code=400, detail=result)

    return {
        "name": result.name,
        "type": result.type,
        "path": result.path,
        "size": result.size,
        "created": result.created,
        "modified": result.modified,
        "readable": result.readable,
        "writable": result.writable,
    }


@router.get("/quota")
def get_quota_info(
    user_id: str = Depends(verify_file_token),
):
    """Get storage quota information for current user"""
    file_manager = get_user_file_manager(user_id)
    quota_manager = get_quota_manager()
    quota_info = quota_manager.get_quota_info(user_id, file_manager.root_dir)

    return {
        "user_id": user_id,
        "quota_mb": round(quota_info["quota_mb"], 2),
        "used_mb": round(quota_info["used_mb"], 2),
        "available_mb": round(quota_info["available_bytes"] / 1024 / 1024, 2),
        "usage_percent": round(quota_info["usage_percent"], 1),
    }


@router.put("/rename")
def rename_file_endpoint(
    old_path: str = Query(...),
    new_path: str = Query(...),
    user_id: str = Depends(verify_file_token),
):
    """Rename or move a file/folder (per-user isolated)"""
    file_manager = get_user_file_manager(user_id)
    success, result = file_manager.rename_file(old_path, new_path)

    _audit_logger.log(
        user_id,
        "rename",
        f"{old_path} -> {new_path}",
        success,
        result if not success else None,
    )

    if not success:
        safe_error = "Failed to rename" if "Error" in result else result
        raise HTTPException(status_code=400, detail=safe_error)

    return {"message": result, "old_path": old_path, "new_path": new_path}


@router.post("/upload", response_model=None)
async def upload_file_endpoint(
    path: str = Query(""),
    file: UploadFile = File(...),
    user_id: str = Depends(verify_file_token),
):
    """Upload a file (per-user isolated, supports binary files)"""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    file_manager = get_user_file_manager(user_id)

    try:
        content = await file.read()

        # Check quota
        quota_manager = get_quota_manager()
        quota_ok, quota_error = quota_manager.check_quota(user_id, file_manager.root_dir, len(content))

        if not quota_ok:
            _audit_logger.log(
                user_id,
                "upload",
                file.filename,
                False,
                f"Quota exceeded: {quota_error}",
            )
            raise HTTPException(status_code=413, detail=quota_error)

        # Determine target path — sanitize filename to prevent path traversal
        safe_filename = os.path.basename(file.filename) if file.filename else "upload"
        if path:
            target_path = os.path.join(path, safe_filename)
        else:
            target_path = safe_filename

        # Write file - handle both text and binary (run in thread to avoid blocking)
        try:
            # Try as text first
            text_content = content.decode("utf-8")
            success, result = await asyncio.to_thread(file_manager.write_file, target_path, text_content)
        except UnicodeDecodeError:
            # Binary file - write directly
            success, result = await asyncio.to_thread(file_manager.write_file, target_path, content, True)

        _audit_logger.log(
            user_id,
            "upload",
            target_path,
            success,
            result if not success else f"size={len(content)}",
        )

        if not success:
            raise HTTPException(status_code=400, detail=result)

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "path": target_path,
            "size": len(content),
        }

    except HTTPException:
        raise
    except Exception as e:
        _audit_logger.log(user_id, "upload", file.filename if file else "unknown", False, str(e))
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/download")
def download_file_endpoint(
    path: str = Query(...),
    user_id: str = Depends(verify_file_token),
):
    """Download a file (per-user isolated, supports binary files)"""
    from fastapi.responses import Response

    file_manager = get_user_file_manager(user_id)
    success, content = file_manager.read_file(path, binary=True)

    _audit_logger.log(user_id, "download", path, success)

    if not success:
        raise HTTPException(status_code=400, detail=content)

    # Get filename
    filename = os.path.basename(path)

    # Handle binary content (returned as dict with base64)
    if isinstance(content, dict) and content.get("is_binary"):
        binary_content = base64.b64decode(content["content"])
    elif isinstance(content, bytes):
        binary_content = content
    else:
        binary_content = content.encode("utf-8")

    # Return file as downloadable response
    return Response(
        content=binary_content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''{}".format(urllib.parse.quote(filename, safe=""))
        },
    )


__all__ = ["FileInfo", "FileSystemManager", "router"]
