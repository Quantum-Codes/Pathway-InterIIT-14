#!/usr/bin/env python3
"""
Helper script to generate bcrypt password hashes for admin users
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_hash(password: str) -> str:
    """Generate bcrypt hash for a password"""
    return pwd_context.hash(password)


def verify_hash(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(password, hashed)


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Password Hash Generator")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("\nEnter password to hash: ")
    
    print(f"\nGenerating hash for password: {password}")
    hashed = generate_hash(password)
    print(f"\nBcrypt hash:\n{hashed}")
    
    # Verify it works
    if verify_hash(password, hashed):
        print("\n✅ Hash verified successfully!")
    else:
        print("\n❌ Hash verification failed!")
    
    print("\n" + "=" * 60)
    print("Use this hash in your SQL INSERT statement:")
    print("=" * 60)
    print(f"\nINSERT INTO admins (username, email, hashed_password, role)")
    print(f"VALUES ('your_username', 'your_email@example.com', '{hashed}', 'admin');")
    print()
