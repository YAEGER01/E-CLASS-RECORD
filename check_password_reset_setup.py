"""
Quick Setup Script for Password Reset Feature
Run this after installing the feature to verify everything is configured correctly.
"""

import os
import sys


def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking Environment Configuration...")
    print("-" * 50)
    
    required_vars = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SENDER_EMAIL': os.getenv('SENDER_EMAIL'),
        'SENDER_PASSWORD': os.getenv('SENDER_PASSWORD'),
    }
    
    all_set = True
    for var, value in required_vars.items():
        if value:
            if 'PASSWORD' in var:
                print(f"✅ {var}: {'*' * len(str(value))}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    print("-" * 50)
    return all_set


def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing Database Connection...")
    print("-" * 50)
    
    try:
        from utils.db_conn import get_db_connection
        
        with get_db_connection().cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Database connected: MySQL {version['VERSION()']}")
            
            # Check if password_reset_tokens table exists
            cursor.execute("SHOW TABLES LIKE 'password_reset_tokens'")
            if cursor.fetchone():
                print("✅ password_reset_tokens table exists")
                
                # Check table structure
                cursor.execute("DESCRIBE password_reset_tokens")
                columns = cursor.fetchall()
                print(f"✅ Table has {len(columns)} columns")
                return True
            else:
                print("❌ password_reset_tokens table NOT FOUND")
                print("   Run: mysql -u root -p e_class_record < db/add_password_reset_tokens.sql")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False
    finally:
        print("-" * 50)


def test_email_service():
    """Test email service configuration"""
    print("\n🔍 Testing Email Service...")
    print("-" * 50)
    
    try:
        from utils.email_service import email_service
        
        if not email_service.sender_email or not email_service.sender_password:
            print("❌ Email credentials not configured")
            print("   Set SENDER_EMAIL and SENDER_PASSWORD in environment variables")
            return False
        
        print(f"✅ Email service configured")
        print(f"   Server: {email_service.smtp_server}:{email_service.smtp_port}")
        print(f"   Sender: {email_service.sender_email}")
        
        # Test SMTP connection
        import smtplib
        try:
            server = smtplib.SMTP(email_service.smtp_server, email_service.smtp_port)
            server.starttls()
            server.login(email_service.sender_email, email_service.sender_password)
            server.quit()
            print("✅ SMTP connection successful")
            return True
        except Exception as e:
            print(f"❌ SMTP connection failed: {str(e)}")
            print("   Check your email credentials and firewall settings")
            return False
            
    except Exception as e:
        print(f"❌ Email service test failed: {str(e)}")
        return False
    finally:
        print("-" * 50)


def test_routes():
    """Test if forgot password routes are registered"""
    print("\n🔍 Testing Routes...")
    print("-" * 50)
    
    try:
        from app import app
        
        routes = []
        for rule in app.url_map.iter_rules():
            if 'forgot' in rule.rule or 'reset' in rule.rule:
                routes.append(f"{rule.rule} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
        
        if routes:
            print("✅ Password reset routes registered:")
            for route in routes:
                print(f"   {route}")
            return True
        else:
            print("❌ No password reset routes found")
            return False
            
    except Exception as e:
        print(f"❌ Route test failed: {str(e)}")
        return False
    finally:
        print("-" * 50)


def main():
    """Run all checks"""
    print("\n" + "=" * 50)
    print("🚀 Password Reset Feature Setup Check")
    print("=" * 50)
    
    results = {
        'Environment': check_environment(),
        'Database': test_database_connection(),
        'Email Service': test_email_service(),
        'Routes': test_routes(),
    }
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check:.<30} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n🎉 All checks passed! Forgot password feature is ready!")
        print("\n📝 Next Steps:")
        print("   1. Test the feature by visiting /forgot-password")
        print("   2. Try resetting a test account password")
        print("   3. Check email delivery")
        print("   4. Review LIVE_DEPLOYMENT_GUIDE.md for production setup")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\n📖 Refer to LIVE_DEPLOYMENT_GUIDE.md for detailed setup instructions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
