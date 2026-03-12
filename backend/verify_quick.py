#!/usr/bin/env python3
import bcrypt
import sys

# Get hashes from database
admin_hash = b'$2b$12$59eTBBWas35DPLuXgofjYuHG/FBu0U8zxi8mt1St00qEJe.6zI6WW'
superadmin_hash = b'$2b$12$n7Xga/w9lPweeEvsP.up/u32UzL8oeTdjf2XKEu6Ifgr87on2MzxC'

# Test passwords
admin_verify = bcrypt.checkpw(b'admin123', admin_hash)
superadmin_verify = bcrypt.checkpw(b'superadmin123', superadmin_hash)

print(f"Admin verified: {admin_verify}")
print(f"Superadmin verified: {superadmin_verify}")

if admin_verify and superadmin_verify:
    print("✅ All passwords work!")
    sys.exit(0)
else:
    print("❌ Password verification failed")
    sys.exit(1)
