#!/usr/bin/env python3
"""Test script to verify password hashes"""
import bcrypt
import sys

# Passwords
admin_password = 'admin123'
superadmin_password = 'superadmin123'

# Hashes from database
admin_hash = b'$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7CW'
superadmin_hash = b'$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'

print("Testing password verification...")
print("-" * 50)

# Test admin password
try:
    admin_match = bcrypt.checkpw(admin_password.encode('utf-8'), admin_hash)
    print(f"✅ Admin password 'admin123' matches: {admin_match}")
except Exception as e:
    print(f"❌ Admin password verification failed: {e}")

# Test superadmin password
try:
    superadmin_match = bcrypt.checkpw(superadmin_password.encode('utf-8'), superadmin_hash)
    print(f"✅ Superadmin password 'superadmin123' matches: {superadmin_match}")
except Exception as e:
    print(f"❌ Superadmin password verification failed: {e}")

print("-" * 50)

# Test with AuthService
print("\nTesting with AuthService...")
try:
    from app.services.auth_service import AuthService
    
    admin_verified = AuthService.verify_password(admin_password, admin_hash.decode('utf-8'))
    superadmin_verified = AuthService.verify_password(superadmin_password, superadmin_hash.decode('utf-8'))
    
    print(f"✅ AuthService admin verification: {admin_verified}")
    print(f"✅ AuthService superadmin verification: {superadmin_verified}")
except Exception as e:
    print(f"❌ AuthService verification failed: {e}")
    import traceback
    traceback.print_exc()
