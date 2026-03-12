#!/usr/bin/env python3
"""
Fix RPS scores in the database.
This script converts any scores > 1 (old 0-100 format) to 0-1 format.
"""

from app.db import SessionLocal
from app.models.user import User
from app.models.toxicity_history import ToxicityHistory
from app.models.alert import ComplianceAlert
from sqlalchemy import text

def fix_rps_scores():
    db = SessionLocal()
    
    try:
        print("🔍 Checking for RPS scores that need fixing...\n")
        
        # Check Users table
        users_to_fix = db.query(User).filter(
            (User.current_rps_360 > 1) | (User.current_rps_not > 1)
        ).all()
        
        if users_to_fix:
            print(f"Found {len(users_to_fix)} users with scores > 1")
            for user in users_to_fix:
                if user.current_rps_360 and user.current_rps_360 > 1:
                    old_val = user.current_rps_360
                    user.current_rps_360 = user.current_rps_360 / 100
                    print(f"  User {user.user_id}: RPS 360: {old_val} → {user.current_rps_360}")
                
                if user.current_rps_not and user.current_rps_not > 1:
                    old_val = user.current_rps_not
                    user.current_rps_not = user.current_rps_not / 100
                    print(f"  User {user.user_id}: RPS NOT: {old_val} → {user.current_rps_not}")
            
            db.commit()
            print(f"✅ Fixed {len(users_to_fix)} users\n")
        else:
            print("✅ All user RPS scores are already in correct range (0-1)\n")
        
        # Check ToxicityHistory table
        history_to_fix = db.query(ToxicityHistory).filter(
            (ToxicityHistory.rps_360 > 1) | (ToxicityHistory.rps_not > 1)
        ).all()
        
        if history_to_fix:
            print(f"Found {len(history_to_fix)} toxicity history records with scores > 1")
            for record in history_to_fix:
                if record.rps_360 and record.rps_360 > 1:
                    record.rps_360 = record.rps_360 / 100
                
                if record.rps_not and record.rps_not > 1:
                    record.rps_not = record.rps_not / 100
            
            db.commit()
            print(f"✅ Fixed {len(history_to_fix)} toxicity history records\n")
        else:
            print("✅ All toxicity history RPS scores are already in correct range (0-1)\n")
        
        # Check ComplianceAlerts table
        alerts_to_fix = db.query(ComplianceAlert).filter(
            ComplianceAlert.rps360 > 1
        ).all()
        
        if alerts_to_fix:
            print(f"Found {len(alerts_to_fix)} alerts with rps360 > 1")
            for alert in alerts_to_fix:
                if alert.rps360 and alert.rps360 > 1:
                    old_val = alert.rps360
                    alert.rps360 = alert.rps360 / 100
                    print(f"  Alert {alert.id}: RPS360: {old_val} → {alert.rps360}")
            
            db.commit()
            print(f"✅ Fixed {len(alerts_to_fix)} alerts\n")
        else:
            print("✅ All alert rps360 scores are already in correct range (0-1)\n")
        
        # Verify the fixes
        print("=" * 60)
        print("📊 Final Statistics:")
        print("=" * 60)
        
        # User stats
        total_users = db.query(User).count()
        users_with_rps = db.query(User).filter(User.current_rps_360.isnot(None)).count()
        avg_rps_360 = db.query(User).filter(User.current_rps_360.isnot(None)).with_entities(
            text("AVG(current_rps_360)")
        ).scalar()
        
        print(f"Users: {total_users} total, {users_with_rps} with RPS scores")
        if avg_rps_360:
            print(f"  Average RPS 360: {float(avg_rps_360):.4f} (should be 0-1)")
            print(f"  Average RPS 360 as %: {float(avg_rps_360) * 100:.2f}%")
        
        # Check for any remaining issues
        still_bad = db.query(User).filter(User.current_rps_360 > 1).count()
        if still_bad > 0:
            print(f"⚠️  WARNING: {still_bad} users still have RPS 360 > 1")
        else:
            print("✅ All scores are now in valid range!")
        
        print("\n🎉 Database fix complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_rps_scores()
