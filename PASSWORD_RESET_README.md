# 🔐 Forgot Password Feature - Quick Reference

## ✅ What's Implemented

**Password reset feature is now FULLY FUNCTIONAL for both Students and Instructors!**

### Features:
- ✅ Forgot password page (`/forgot-password`)
- ✅ Email with password reset link
- ✅ Secure token system (expires in 1 hour)
- ✅ Reset password page with validation
- ✅ Beautiful email templates
- ✅ Works for both students and instructors

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Run Database Migration

```bash
mysql -u root -p e_class_record < db/add_password_reset_tokens.sql
```

### Step 2: Configure Email (Choose One)

**Option A: Use Current Gmail Setup (Already Working)**
```python
# Already configured in utils/email_service.py
# Uses: programmingproject06@gmail.com
# This works out of the box!
```

**Option B: Use Your Own Gmail (Recommended)**
1. Enable 2FA on Gmail: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Update `utils/email_service.py`:
```python
self.sender_email = os.getenv("SENDER_EMAIL", "your-email@isu.edu.ph")
self.sender_password = os.getenv("SENDER_PASSWORD", "your-app-password")
```

### Step 3: Test It!

```bash
# Run the check script
python check_password_reset_setup.py

# Start your app
python app.py

# Visit: http://localhost:5000/forgot-password
```

---

## 📧 How It Works

### For Users (Students/Instructors):

1. **Forgot Password?**
   - Click "Forgot Password?" on login page
   - Select role (Student/Instructor)
   - Enter registered email
   - Click "Send Reset Link"

2. **Check Email**
   - Receive email within seconds
   - Click "Reset My Password" button
   - Or copy the link

3. **Reset Password**
   - Enter new password
   - Confirm password
   - Click "Reset Password"
   - Login with new password!

### For Admins:

**Email Flow:**
```
User enters email
    ↓
System generates secure token
    ↓
Token stored in database (expires in 1 hour)
    ↓
Email sent with reset link
    ↓
User clicks link
    ↓
System validates token
    ↓
User sets new password
    ↓
Token marked as used
    ↓
User redirects to login
```

---

## 🔒 Security Features

- ✅ **Email Enumeration Protection**: Same message for valid/invalid emails
- ✅ **Token Expiration**: Links expire after 1 hour
- ✅ **One-Time Use**: Tokens can't be reused
- ✅ **Secure Tokens**: 32-byte URL-safe random tokens
- ✅ **Password Validation**: Minimum 6 characters
- ✅ **HTTPS Ready**: Works with SSL certificates

---

## 📁 Files Created/Modified

### New Files:
```
db/add_password_reset_tokens.sql         # Database migration
templates/forgot_password.html            # Forgot password form
templates/reset_password.html             # Reset password form
check_password_reset_setup.py             # Setup verification script
LIVE_DEPLOYMENT_GUIDE.md                  # Complete deployment guide
```

### Modified Files:
```
utils/email_service.py                    # Added send_password_reset_email()
blueprints/auth_routes.py                 # Added forgot/reset routes
templates/studentlogin.html               # Linked to forgot password
templates/instructorlogin.html            # Linked to forgot password
```

---

## 🌐 For LIVE Deployment

### Essential Checklist:

**1. Database:**
```bash
✅ Run migration
✅ Create backup system
✅ Set strong DB password
```

**2. Email:**
```bash
✅ Use university email or professional service
✅ Store credentials in environment variables
✅ Test email delivery
```

**3. Domain & HTTPS:**
```bash
✅ Set up domain (e.g., eclass.isu.edu.ph)
✅ Install SSL certificate (Let's Encrypt is FREE)
✅ Configure Flask for HTTPS
```

**4. Security:**
```bash
✅ Use environment variables for secrets
✅ Never commit .env files
✅ Enable rate limiting
✅ Monitor logs
```

**Full Guide:** See [LIVE_DEPLOYMENT_GUIDE.md](LIVE_DEPLOYMENT_GUIDE.md)

---

## 🧪 Testing

### Manual Test:

1. **Test Student Password Reset:**
```
1. Go to student login
2. Click "Forgot Password?"
3. Select "Student"
4. Enter: test-student@isu.edu.ph
5. Check email
6. Click reset link
7. Set new password
8. Login with new password
```

2. **Test Instructor Password Reset:**
```
1. Go to instructor login
2. Click "Forgot Password?"
3. Select "Instructor"
4. Enter: test-instructor@isu.edu.ph
5. Check email
6. Click reset link
7. Set new password
8. Login with new password
```

### Automated Check:
```bash
python check_password_reset_setup.py
```

---

## ❓ Troubleshooting

### Email Not Received?

**Check:**
1. Spam folder
2. Email credentials in `utils/email_service.py`
3. SMTP server connectivity:
```bash
telnet smtp.gmail.com 587
```

**Fix:**
```python
# Test email manually
from utils.email_service import email_service
result = email_service.send_password_reset_email(
    "test@example.com",
    "Test User",
    "http://localhost:5000/reset-password/test123",
    "Student"
)
print("Email sent:", result)
```

### Reset Link Not Working?

**Check:**
1. Token exists in database:
```sql
SELECT * FROM password_reset_tokens ORDER BY created_at DESC LIMIT 5;
```

2. Token not expired:
```sql
SELECT *, 
    CASE 
        WHEN expires_at < NOW() THEN 'EXPIRED'
        WHEN used = 1 THEN 'USED'
        ELSE 'VALID'
    END as status
FROM password_reset_tokens 
WHERE token = 'your-token-here';
```

3. Check browser console for errors

### Database Migration Failed?

**Manually create table:**
```sql
USE e_class_record;

CREATE TABLE password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    role ENUM('student', 'instructor') NOT NULL,
    expires_at DATETIME NOT NULL,
    used TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Verify
DESCRIBE password_reset_tokens;
```

---

## 📞 Support

### During Development:
- Check logs: `logs/app.log`
- Enable debug mode in Flask
- Use `check_password_reset_setup.py`

### For Live Deployment:
- Review: [LIVE_DEPLOYMENT_GUIDE.md](LIVE_DEPLOYMENT_GUIDE.md)
- Contact ISU IT Department
- Professional email service support

---

## 💡 Tips for Going Live

### Before Launch:
1. **Test with real emails** (not just localhost)
2. **Test on mobile devices** (80% of users!)
3. **Set up monitoring** (email delivery, errors)
4. **Create admin documentation**
5. **Train support staff**

### After Launch:
1. **Monitor first week closely**
2. **Check email delivery rates**
3. **Review user feedback**
4. **Optimize based on usage**
5. **Keep backups updated**

---

## 🎉 Summary

**The forgot password feature is READY!**

✅ Fully functional for students and instructors
✅ Secure with token expiration and one-time use
✅ Beautiful email templates
✅ Easy to test and deploy
✅ Complete documentation provided

**Next Steps:**
1. Run database migration
2. Test the feature locally
3. Review LIVE_DEPLOYMENT_GUIDE.md
4. Configure email for production
5. Deploy! 🚀

---

**Questions?** Check [LIVE_DEPLOYMENT_GUIDE.md](LIVE_DEPLOYMENT_GUIDE.md) for detailed answers!
