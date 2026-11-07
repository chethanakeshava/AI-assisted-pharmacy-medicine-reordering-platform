from fastapi import HTTPException, UploadFile

from ..config import settings

MAGIC = [(b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG\r\n\x1a\n", "image/png")]


def sniff(data: bytes) -> str | None:
    for sig, mime in MAGIC:
        if data.startswith(sig):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def read_image(file: UploadFile) -> tuple[bytes, str]:
    """Validate by file content, not by the client-supplied name or type."""
    data = await file.read(settings.max_upload_bytes + 1)
    if not data:
        raise HTTPException(422, "The file is empty")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "File is too large (max 5 MB)")
    mime = sniff(data)
    if not mime:
        raise HTTPException(415, "Please upload a JPG, PNG or WEBP photo of the prescription")
    return data, mime
