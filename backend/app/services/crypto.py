"""Prescription files are encrypted at rest (DPDP Act 2023: sensitive health data)."""
import base64
import hashlib
import os
import uuid
from pathlib import Path

from cryptography.fernet import Fernet

from ..config import settings


def _fernet() -> Fernet:
    if settings.fernet_key:
        return Fernet(settings.fernet_key.encode())
    if settings.app_env != "dev":
        raise RuntimeError("FERNET_KEY must be set outside dev")
    # Dev only: deterministic key so local restarts can still read old uploads.
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret.encode()).digest()))


def save_encrypted(data: bytes) -> str:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.enc"
    Path(settings.upload_dir, name).write_bytes(_fernet().encrypt(data))
    return name


def read_decrypted(name: str) -> bytes:
    return _fernet().decrypt(Path(settings.upload_dir, os.path.basename(name)).read_bytes())
