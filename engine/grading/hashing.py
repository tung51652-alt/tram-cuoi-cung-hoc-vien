"""Hash source theo quy tắc thiết kế §5.4."""

import hashlib
from pathlib import Path


def level_source_hash(submission_dir, entry_name, all_entry_names):
    """sha256 của entry + mọi student/*.py cấp gốc không phải entry màn khác."""
    root = Path(submission_dir)
    digest = hashlib.sha256()
    files = [root / entry_name]
    for path in sorted(root.glob("*.py")):
        if path.name != entry_name and path.name not in all_entry_names:
            files.append(path)
    for path in files:
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes() if path.exists() else b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()
