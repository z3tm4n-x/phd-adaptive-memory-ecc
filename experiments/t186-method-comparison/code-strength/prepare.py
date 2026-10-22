"""Compatibility entry point; the preparatory table is now the numerical table.

Historical v1/v2 preparation remains in Git. Use reproduce.py directly for
new runs. No old preliminary table can overwrite the current three rows.
"""
from reproduce import main

if __name__ == "__main__":
    raise SystemExit(main())
