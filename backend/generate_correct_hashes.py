#!/usr/bin/env python3
"""Generate correct bcrypt hashes for admin passwords"""
import bcrypt

# Generate hashes
admin_password = 'admin123'
superadmin_password = 'superadmin123'

admin_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
superadmin_hash = bcrypt.hashpw(superadmin_password.encode('utf-8'), bcrypt.gensalt())

print("Generated password hashes:")
print("-" * 80)
print(f"Admin (admin123): {admin_hash.decode('utf-8')}")
print(f"Superadmin (superadmin123): {superadmin_hash.decode('utf-8')}")
print("-" * 80)

# Verify they work
admin_verify = bcrypt.checkpw(admin_password.encode('utf-8'), admin_hash)
superadmin_verify = bcrypt.checkpw(superadmin_password.encode('utf-8'), superadmin_hash)

print(f"\nVerification:")
print(f"Admin password matches: {admin_verify}")
print(f"Superadmin password matches: {superadmin_verify}")

# Generate SQL update statements
print("\n" + "=" * 80)
print("SQL UPDATE STATEMENTS:")
print("=" * 80)
print(f"UPDATE admins SET hashed_password = '{admin_hash.decode('utf-8')}' WHERE username = 'admin';")
print(f"UPDATE admins SET hashed_password = '{superadmin_hash.decode('utf-8')}' WHERE username = 'superadmin';")
