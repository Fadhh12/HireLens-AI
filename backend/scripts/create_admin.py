"""
One-off bootstrap script: create the first Admin account.

FR-1.5 says role is always assigned by an Admin at account creation —
there is intentionally no public self-register endpoint. That leaves a
chicken-and-egg gap the docs don't address: how does the very first
Admin get created? This script is the answer — run it once against a
fresh database, then manage every other user through
POST /api/v1/users as that Admin.

Usage (from backend/, with the venv active):
    python scripts/create_admin.py --name "Nabil" --email admin@hirelens.ai --password "ChangeMe123"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.modules.auth.model import UserRole  # noqa: E402
from app.modules.auth.schema import UserCreate  # noqa: E402
from app.modules.auth.service import create_user, get_user_by_email  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True, help="Min 8 chars, at least 1 letter + 1 number")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if get_user_by_email(db, args.email) is not None:
            print(f"User with email {args.email} already exists — nothing to do.")
            return

        user = create_user(
            db,
            UserCreate(name=args.name, email=args.email, password=args.password, role=UserRole.admin),
        )
        print(f"Admin created: {user.email} ({user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
