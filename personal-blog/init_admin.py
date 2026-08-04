"""
Run this once to create your admin account (or again later to change your
username/password). This blog only ever has ONE account: you.

Usage:
    python init_admin.py
"""
import getpass
import sqlite3
import os

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "blog.db")


def main():
    # Make sure tables exist
    from app import init_db
    init_db()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    existing = db.execute("SELECT * FROM user LIMIT 1").fetchone()
    if existing:
        print(f"An account already exists (username: {existing['username']}).")
        choice = input("Overwrite it with a new username/password? [y/N]: ").strip().lower()
        if choice != "y":
            print("Cancelled.")
            return

    username = input("Choose a username: ").strip()
    while not username:
        username = input("Username can't be empty. Choose a username: ").strip()

    password = getpass.getpass("Choose a password: ")
    while len(password) < 6:
        password = getpass.getpass("Password should be at least 6 characters. Choose a password: ")

    password_hash = generate_password_hash(password)

    if existing:
        db.execute(
            "UPDATE user SET username=?, password_hash=? WHERE id=?",
            (username, password_hash, existing["id"]),
        )
    else:
        db.execute(
            "INSERT INTO user (username, password_hash, display_name, bio, avatar_url) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, "Your Name", "Write something about yourself here.", ""),
        )
    db.commit()
    db.close()
    print("\nDone! You can now log in at /login with that username and password.")


if __name__ == "__main__":
    main()
