"""Minimal imghdr shim for environments missing the stdlib imghdr.

This provides a subset of the stdlib imghdr.what() function based on file
signatures (magic numbers). It supports common image types used by the
bing_image_downloader package: jpeg, png, gif, bmp, webp, tiff.

It accepts either a filename or raw header bytes like the stdlib function.
This is intentionally small and defensive.
"""
from __future__ import annotations
import typing

_SIGNATURES = [
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"BM", "bmp"),
    (b"RIFF", "webp"),  # RIFF....WEBP in header
    (b"II*\x00", "tiff"),
    (b"MM\x00*", "tiff"),
]


def _read_header_from_file(file: str, n: int = 32) -> bytes:
    try:
        with open(file, "rb") as f:
            return f.read(n)
    except Exception:
        return b""


def what(file: typing.Union[str, bytes, bytearray, None], h: typing.Optional[bytes] = None) -> typing.Optional[str]:
    """Determine the image type based on header bytes or file path.

    Mirrors the stdlib imghdr.what behaviour sufficiently for downloader use.
    Returns a string like 'jpeg', 'png', ... or None if unknown.
    """
    header = b""
    if h is not None:
        header = h[:32]
    elif isinstance(file, (bytes, bytearray)):
        header = bytes(file)[:32]
    elif isinstance(file, str):
        header = _read_header_from_file(file, 32)
    else:
        return None

    if not header:
        return None

    # Check signatures
    for sig, typ in _SIGNATURES:
        if header.startswith(sig):
            if typ == "webp":
                # RIFFxxxxWEBP - ensure WEBP appears later
                if b"WEBP" in header[8:16]:
                    return "webp"
                continue
            return typ

    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            print(path, what(path))
    else:
        print("Usage: imghdr.py <image-file>...")
