# 🚀 LIVE Deployment Guide - E-Class Record System

## Table of Contents
1. [Password Reset Feature Setup](#password-reset-feature-setup)
2. [Email Configuration for LIVE Environment](#email-configuration-for-live)
3. [Database Migration](#database-migration)
4. [Security Considerations for Production](#security-considerations)
5. [Domain & HTTPS Setup](#domain--https-setup)
6. [Environment Variables](#environment-variables)
7. [Testing Before Going Live](#testing-checklist)

---

## Password Reset Feature Setup

### ✅ What Was Implemented

The forgot password feature is now **fully functional** with:
- ✅ Email-based password reset for **Students** and **Instructors**
- ✅ Secure token generation (32-byte URL-safe tokens)
- ✅ 1-hour token expiration for security
- ✅ Beautiful HTML email templates
- ✅ Token usage tracking (one-time use)
- ✅ Email enumeration protection

### 🔧 Required Database Migration

**IMPORTANT:** Run this migration before deploying to LIVE:

```bash
mysql -u root -p e_class_record < db/add_password_reset_tokens.sql
```

Or manually in your database:

```sql
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    role ENUM('student', 'instructor') NOT NULL,
    expires_at DATETIME NOT NULL,
    used TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Email Configuration for LIVE

### Option 1: Gmail (Current Setup - For Testing/Small Scale)

**Current Configuration (Development):**
```python
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "programmingproject06@gmail.com"
SENDER_PASSWORD = "kttb wlay puqu mwup"  # App Password
```

**⚠️ CRITICAL: For LIVE Production, DO NOT hardcode credentials!**

### Option 2: Gmail with Environment Variables (Recommended for Small-Medium Scale)

**1. Enable 2-Factor Authentication on your Gmail:**
- Go to: https://myaccount.google.com/security
- Enable "2-Step Verification"

**2. Generate App Password:**
- Go to: https://myaccount.google.com/apppasswords
- Select "Mail" and "Windows Computer"
- Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

**3. Create `.env` file in your project root:**

```bash
# .env file (DO NOT COMMIT THIS TO GIT!)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-university-email@isu.edu.ph
SENDER_PASSWORD=your_app_password_here
SENDER_NAME=E-Class Record System - ISU Cauayan
```

**4. Update `utils/email_service.py` to use environment variables:**

The code already uses `os.getenv()`, so it will automatically read from environment variables:

```python
self.sender_email = os.getenv("SENDER_EMAIL", "programmingproject06@gmail.com")
self.sender_password = os.getenv("SENDER_PASSWORD", "kttb wlay puqu mwup")
```

**5. Install python-dotenv:**

```bash
pip install python-dotenv
```

**6. Load environment variables in `app.py`:**

Add at the top of `app.py`:

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file
```

### Option 3: University Email Server (Best for Production)

**Contact your ISU IT Department for:**
- SMTP server address (e.g., `mail.isu.edu.ph`)
- SMTP port (usually 587 or 465)
- Authentication credentials
- Sending limits and policies

**Example Configuration:**
```bash
SMTP_SERVER=mail.isu.edu.ph
SMTP_PORT=587
SENDER_EMAIL=eclass@isu.edu.ph
SENDER_PASSWORD=secure_password_here
SENDER_NAME=E-Class Record System - ISU Cauayan
```

### Option 4: Third-Party Email Service (Recommended for Large Scale)

For production systems with many users, consider professional email services:

#### **SendGrid** (Free: 100 emails/day, Paid: $19.95/month for 50k emails)
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SENDER_EMAIL=eclass@isu.edu.ph
SENDER_PASSWORD=your_sendgrid_api_key
```

#### **Mailgun** (Free: 5,000 emails/month)
```bash
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SENDER_EMAIL=eclass@isu.edu.ph
SENDER_PASSWORD=your_mailgun_smtp_password
```

#### **Amazon SES** (Free: 62,000 emails/month if hosted on AWS)
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SENDER_EMAIL=eclass@isu.edu.ph
SENDER_PASSWORD=your_ses_smtp_password
```

---

## Domain & HTTPS Setup

### Why This Matters

Password reset links use `url_for(..., _external=True)` which generates full URLs:
- Development: `http://localhost:5000/reset-password/token123`
- Production: `https://eclass.isu.edu.ph/reset-password/token123`

### Setting Up Your Domain

**1. Purchase/Use University Domain**
- Option A: Use subdomain: `eclass.isu.edu.ph`
- Option B: Buy custom domain: `isueclassrecord.com`

**2. Point Domain to Your Server**
- Get server IP address
- Create A Record in DNS settings
- Wait for DNS propagation (5-60 minutes)

**3. Install SSL Certificate (HTTPS)**

**Option A: Let's Encrypt (FREE):**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d eclass.isu.edu.ph
```

**Option B: Cloudflare (FREE + CDN + DDoS Protection):**
1. Sign up at cloudflare.com
2. Add your domain
3. Update nameservers
4. Enable "Full (Strict)" SSL mode
5. Automatic HTTPS redirect

### Configure Flask for Production

**Update `app.py` for production:**

```python
import os

# Production configuration
if os.getenv('FLASK_ENV') == 'production':
    app.config['SERVER_NAME'] = 'eclass.isu.edu.ph'  # Your domain
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

---

## Environment Variables

### Create Production `.env` File

```bash
# .env.production
# Database
DB_HOST=localhost
DB_USER=eclass_user
DB_PASSWORD=strong_secure_password_here
DB_NAME=e_class_record

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=eclass@isu.edu.ph
SENDER_PASSWORD=your_app_password
SENDER_NAME=E-Class Record System - ISU Cauayan

# Flask
FLASK_ENV=production
SECRET_KEY=generate_a_very_long_random_secret_key_here
SERVER_NAME=eclass.isu.edu.ph

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### Generate Strong Secret Key

```python
import secrets
print(secrets.token_hex(32))
# Output: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6...'
```

---

## Security Considerations

### 1. **NEVER Commit Sensitive Data**

Add to `.gitignore`:
```
.env
.env.production
*.log
__pycache__/
instance/
.vscode/
```

### 2. **Use Strong Passwords**

```sql
-- Create dedicated database user for production
CREATE USER 'eclass_user'@'localhost' IDENTIFIED BY 'VeryStr0ng!P@ssw0rd#2026';
GRANT ALL PRIVILEGES ON e_class_record.* TO 'eclass_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. **Rate Limiting for Password Reset**

Add to `utils/email_service.py`:

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")  # Max 5 reset requests per hour per IP
def forgot_password():
    # ... existing code
```

### 4. **Database Backup**

Schedule automatic backups:

```bash
# Create backup script
sudo nano /usr/local/bin/backup-eclass.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/eclass"
mkdir -p $BACKUP_DIR
mysqldump -u eclass_user -p'password' e_class_record > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -type f -mtime +7 -delete  # Keep 7 days of backups
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-eclass.sh

# Schedule daily backup (runs at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-eclass.sh
```

### 5. **Cleanup Expired Tokens**

Add to cron:

```bash
# Clean expired tokens daily
0 3 * * * mysql -u eclass_user -p'password' e_class_record -e "DELETE FROM password_reset_tokens WHERE expires_at < NOW() OR used = 1;"
```

---

## Testing Checklist

### Before Going Live:

#### Email Testing
- [ ] Test with Gmail account
- [ ] Test with student university email
- [ ] Test with instructor university email
- [ ] Verify email delivery time (should be < 1 minute)
- [ ] Check spam folder if not received
- [ ] Test password reset link expiration (wait 1 hour)
- [ ] Test used token rejection

#### Functionality Testing
- [ ] Student can request password reset
- [ ] Instructor can request password reset
- [ ] Invalid email shows generic message (security)
- [ ] Reset link works on mobile devices
- [ ] Password validation works (min 6 chars)
- [ ] Password mismatch shows error
- [ ] Successful reset redirects to login
- [ ] Old password no longer works
- [ ] New password works for login

#### Security Testing
- [ ] HTTPS enabled (padlock icon in browser)
- [ ] Session cookies are secure
- [ ] SQL injection protection (test with ' OR '1'='1)
- [ ] XSS protection (test with <script>alert('xss')</script>)
- [ ] Rate limiting works (try 10 reset requests quickly)
- [ ] Token cannot be reused
- [ ] Expired token shows proper error

#### Performance Testing
- [ ] Page load time < 2 seconds
- [ ] Email sends within 10 seconds
- [ ] Database queries optimized
- [ ] Server can handle 50+ concurrent users

---

## Deployment Options

### Option 1: Traditional VPS Hosting

**Providers:**
- DigitalOcean: $6/month
- Linode: $5/month
- Vultr: $6/month

**Setup:**
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip mysql-server nginx

# Clone your project
git clone https://github.com/yourusername/eclass.git
cd eclass

# Install Python packages
pip3 install -r requirements.txt

# Setup database
mysql -u root -p < db/setup.sql

# Configure Nginx
sudo nano /etc/nginx/sites-available/eclass

# Start with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Option 2: PythonAnywhere (Easiest for Beginners)

**FREE Plan Available!**
1. Sign up at pythonanywhere.com
2. Upload your code
3. Configure web app
4. Set environment variables
5. Done! Auto HTTPS included

### Option 3: Heroku (Easy Deployment)

```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create eclass-isu
git push heroku main
heroku config:set SENDER_EMAIL=eclass@isu.edu.ph
heroku config:set SENDER_PASSWORD=your_password
```

---

## Monitoring & Maintenance

### 1. Error Logging

Update `app.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/eclass.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 2. Email Delivery Monitoring

Check email logs regularly:
```bash
tail -f /var/log/mail.log
```

### 3. Database Health

```sql
-- Check password reset usage
SELECT 
    role,
    COUNT(*) as total_requests,
    SUM(used) as used_tokens,
    COUNT(*) - SUM(used) as expired_unused
FROM password_reset_tokens
WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY role;
```

---

## Troubleshooting

### Email Not Sending

**1. Check SMTP credentials:**
```bash
python3 -c "from utils.email_service import email_service; print('Email configured:', bool(email_service.sender_email))"
```

**2. Test Gmail connection:**
```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print("Success!")
```

**3. Check firewall:**
```bash
sudo ufw allow 587/tcp
```

### Reset Link Not Working

**1. Check token in database:**
```sql
SELECT * FROM password_reset_tokens WHERE token = 'your_token_here';
```

**2. Verify URL generation:**
```python
# In Flask shell
from flask import url_for
with app.test_request_context():
    print(url_for('auth.reset_password', token='test123', _external=True))
```

### HTTPS Issues

**1. Force HTTPS redirect in Nginx:**
```nginx
server {
    listen 80;
    server_name eclass.isu.edu.ph;
    return 301 https://$server_name$request_uri;
}
```

---

## Support & Contacts

### ISU IT Support
- Email: it@isu.edu.ph
- Phone: (078) XXX-XXXX

### Email Service Providers Support
- Gmail: https://support.google.com/mail
- SendGrid: https://support.sendgrid.com
- Mailgun: https://www.mailgun.com/support

---

## Summary Checklist

### Pre-Launch:
- [ ] Run database migration for password_reset_tokens
- [ ] Configure production email credentials
- [ ] Set up environment variables
- [ ] Enable HTTPS with SSL certificate
- [ ] Test forgot password flow completely
- [ ] Configure domain name
- [ ] Set up database backups
- [ ] Enable error logging
- [ ] Test on mobile devices
- [ ] Create admin documentation

### Post-Launch:
- [ ] Monitor email delivery rates
- [ ] Check error logs daily (first week)
- [ ] Verify backup system working
- [ ] Monitor server resources
- [ ] Collect user feedback
- [ ] Plan for scaling if needed

---

**🎉 Your forgot password feature is ready for production!**

For questions or issues, refer to this guide or contact your system administrator.
