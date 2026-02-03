# make_hash.py
import os, hashlib, getpass

def make_user():
    username = input("Username: ").strip()
    display = input("Display name: ").strip() or username
    role = input("Role (admin/user): ").strip() or "user"
    pwd = getpass.getpass("Password (hidden): ").strip()

    salt = os.urandom(8).hex()
    hash_hex = hashlib.sha256((salt + pwd).encode("utf-8")).hexdigest()

    print("\n--- Paste to secrets.toml ---")
    print(f"[users.{username}]")
    print(f'display_name = "{display}"')
    print(f'role = "{role}"')
    print(f'salt = "{salt}"')
    print(f'hash = "{hash_hex}"')
    print("-----------------------------")

if __name__ == "__main__":
    make_user()
