"""Non-destructive, repeatable archive of tracked legacy data."""
import hashlib
import sqlite3
import subprocess
from pathlib import Path

def archive(root, db):
    root = Path(root)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", revision, "state", "reports"], cwd=root).decode().split("\0")
    with sqlite3.connect(db) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS blobs (sha TEXT PRIMARY KEY, content BLOB NOT NULL);
        CREATE TABLE IF NOT EXISTS snapshots (revision TEXT, path TEXT, sha TEXT NOT NULL REFERENCES blobs(sha), PRIMARY KEY(revision,path));
        """)
        for path in filter(None, paths):
            data = subprocess.check_output(["git", "show", revision + ":" + path], cwd=root)
            sha = hashlib.sha256(data).hexdigest()
            con.execute("INSERT OR IGNORE INTO blobs VALUES (?,?)", (sha,data))
            con.execute("INSERT OR IGNORE INTO snapshots VALUES (?,?,?)", (revision,path,sha))
    return revision

if __name__ == "__main__":
    import sys
    print(archive(Path(__file__).resolve().parents[1], sys.argv[1]))
