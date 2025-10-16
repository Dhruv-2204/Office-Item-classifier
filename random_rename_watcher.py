"""Watch a directory and rename newly added image files to random names.

Usage examples:
  python random_rename_watcher.py --dir dataset
  python random_rename_watcher.py --dir dataset --dry-run

The script uses a simple polling loop (no external dependencies) and checks
that a file's size is stable for a short duration before renaming to avoid
colliding with files still being written.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from typing import Optional

# Import the local imghdr shim if available; fall back to stdlib if present.
try:
    # Local version in the repo
    import imghdr as local_imghdr  # file shipped in this repo
except Exception:
    import imghdr as local_imghdr  # type: ignore


def generate_random_name(directory: str, extension: str) -> str:
    """Generate a unique random filename in `directory` with `extension`."""
    for _ in range(10_000):
        name = uuid.uuid4().hex
        fname = f"{name}{extension}"
        path = os.path.join(directory, fname)
        if not os.path.exists(path):
            return fname
    raise FileExistsError("Unable to generate a unique random filename")


def infer_extension(path: str) -> str:
    """Infer a reasonable file extension for an image file at `path`.

    Uses the repo's `imghdr.what` shim which returns types like 'jpeg', 'png',
    etc. Falls back to the original extension on disk.
    """
    kind = local_imghdr.what(path)
    if kind:
        mapping = {
            "jpeg": ".jpg",
            "png": ".png",
            "gif": ".gif",
            "bmp": ".bmp",
            "webp": ".webp",
            "tiff": ".tif",
        }
        return mapping.get(kind, f".{kind}")
    # fallback: preserve existing extension if any
    _, ext = os.path.splitext(path)
    return ext.lower() or ".img"


def is_image_file(path: str) -> bool:
    """Return True if the file at path appears to be an image.

    This uses header checks (imghdr) rather than trusting the extension.
    """
    try:
        return local_imghdr.what(path) is not None
    except Exception:
        # If imghdr fails for any reason, fall back to extension-based check
        _, ext = os.path.splitext(path)
        return ext.lower() in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}


def wait_for_stable_file(path: str, timeout: float = 10.0, interval: float = 0.5, stable_checks: int = 3) -> bool:
    """Wait until file size is stable for `stable_checks` consecutive checks or timeout.

    This is more robust than relying on a single unchanged read because some writers
    flush in bursts. Returns True if the file was observed unchanged for the
    requested number of consecutive checks before `timeout` seconds elapsed.
    """
    start = time.time()
    try:
        last_size = os.path.getsize(path)
    except OSError:
        return False

    consecutive = 0
    # First check counts as the first measurement; we need stable_checks consecutive
    # equal sizes after subsequent sleeps.
    while time.time() - start < timeout:
        time.sleep(interval)
        try:
            size = os.path.getsize(path)
        except OSError:
            return False
        if size == last_size:
            consecutive += 1
            if consecutive >= stable_checks:
                return True
        else:
            consecutive = 0
        last_size = size
    return False


def rename_file_safely(src_path: str, dest_dir: str, dry_run: bool = False) -> Optional[str]:
    """Rename `src_path` into `dest_dir` using a random name; return new name or None.

    Preserves an inferred extension. Performs a final existence check to avoid
    overwriting existing files.
    """
    ext = infer_extension(src_path)
    new_name = generate_random_name(dest_dir, ext)
    dest_path = os.path.join(dest_dir, new_name)
    if dry_run:
        print(f"[dry-run] Would rename: {src_path} -> {dest_path}")
        return new_name
    try:
        os.rename(src_path, dest_path)
        print(f"Renamed: {src_path} -> {dest_path}")
        return new_name
    except Exception as exc:
        print(f"Failed to rename {src_path} -> {dest_path}: {exc}")
        return None


def watch_directory(directory: str, poll_interval: float = 1.0, stability_timeout: float = 10.0, stable_checks: int = 3, dry_run: bool = False) -> None:
    """Main loop: poll `directory` for new files and rename them.

    This is intentionally simple: it keeps an in-memory set of seen filenames
    and handles new items as they're discovered.
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(directory)

    seen = set()
    # seed seen with existing files to avoid renaming old files
    for entry in os.scandir(directory):
        if entry.is_file():
            seen.add(entry.name)

    print(f"Watching directory: {directory}")
    try:
        while True:
            for entry in os.scandir(directory):
                if not entry.is_file():
                    continue
                name = entry.name
                if name in seen:
                    continue
                # ignore hidden and temporary files
                if name.startswith(".") or name.startswith("~"):
                    seen.add(name)
                    continue
                path = os.path.join(directory, name)

                # Wait until file appears stable (not being written). This ensures
                # we don't run imghdr on a partial file which would often return
                # False and cause the file to be marked "seen" and never retried.
                stable = wait_for_stable_file(path, timeout=stability_timeout, interval=min(0.5, poll_interval), stable_checks=stable_checks)
                if not stable:
                    # skip this round; we'll see it again on next poll
                    print(f"Skipping (not stable yet): {path}")
                    continue

                # Now that the file appears stable, check if it's an image and
                # rename it. If it's not an image, mark it seen so we don't
                # repeatedly check non-image files.
                if not is_image_file(path):
                    print(f"Not an image after stability check, skipping: {path}")
                    seen.add(name)
                    continue

                new_name = rename_file_safely(path, directory, dry_run=dry_run)
                # mark as seen either way to avoid repeated attempts
                seen.add(name)
                if new_name:
                    seen.add(new_name)

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("Stopped by user")


def parse_args():
    p = argparse.ArgumentParser(description="Watch a directory and rename new image files to random names")
    p.add_argument("--dir", default=r"C:\Users\dylan\Documents\Computer science\Computer Science Year 3\temp", help="Directory to watch")
    p.add_argument("--poll-interval", type=float, default=0.5, help="Polling interval in seconds")
    p.add_argument("--stability-timeout", type=float, default=1.0, help="Seconds to wait (total) for a file to become stable before renaming")
    p.add_argument("--stable-checks", type=int, default=3, help="Number of consecutive unchanged size checks required to consider a file stable")
    p.add_argument("--dry-run", action="store_true", help="Do not actually rename files; just print what would happen")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        watch_directory(args.dir, poll_interval=args.poll_interval, stability_timeout=args.stability_timeout, stable_checks=args.stable_checks, dry_run=args.dry_run)
    except Exception as exc:
        print(f"Error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
