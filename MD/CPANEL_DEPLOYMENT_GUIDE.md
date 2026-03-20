# 🚀 cPanel Deployment Guide - E-Class Record System

## Complete Step-by-Step Guide for Live Deployment

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [cPanel Setup](#cpanel-setup)
3. [Database Configuration](#database-configuration)
4. [File Upload](#file-upload)
5. [Environment Configuration](#environment-configuration)
6. [Python Application Setup](#python-application-setup)
7. [SSL Certificate (HTTPS)](#ssl-certificate)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need:
- ✅ cPanel hosting account with Python support
- ✅ Domain name (e.g., `eclass.isu.edu.ph` or `yourproject.com`)
- ✅ Your project files ready
- ✅ Database credentials
- ✅ Email credentials for password reset

### Verify cPanel Has:
- Python 3.7+ support
- MySQL database
- SSH access (optional but recommended)
- File Manager or FTP access

---

## Step 1: cPanel Setup

### A. Access Your cPanel

1. Go to: `https://yourdomain.com:2083` or `https://yourhost.com/cpanel`
2. Login with your credentials

### B. Set Up Your Domain

**Option 1: Main Domain**
- Your site will be at: `https://yourdomain.com`
- Files go in: `public_html/` folder

**Option 2: Subdomain**
1. Go to **Domains** → **Subdomains**
2. Create: `eclass.yourdomain.com`
3. Document root: `/home/username/public_html/eclass`

**Option 3: Addon Domain**
1. Go to **Domains** → **Addon Domains**
2. New domain: `eclass-isu.com`
3. Document root: `/home/username/public_html/eclass-isu`

---

## Step 2: Database Configuration

### A. Create MySQL Database

1. **Go to MySQL® Databases**
2. **Create New Database:**
   ```
   Database Name: username_eclass
   ```
   (cPanel adds your username prefix automatically)

3. **Create Database User:**
   ```
   Username: username_eclass_user
   Password: [Generate strong password - SAVE THIS!]
   ```

4. **Add User to Database:**
   - Select database: `username_eclass`
   - Select user: `username_eclass_user`
   - Grant **ALL PRIVILEGES**

5. **Note Your Database Info:**
   ```
   Database Name: username_eclass
   Database User: username_eclass_user
   Database Password: [your password]
   Database Host: localhost
   ```

### B. Import Database Structure

1. **Go to phpMyAdmin**
2. Select your database: `username_eclass`
3. Click **Import** tab
4. Upload your SQL files in this order:
   ```
   1. db/e_class_record_backup.sql (main structure)
   2. db/add_student_class_join_approval.sql
   3. db/add_password_reset_tokens.sql
   4. db/add_grade_sheet_signatures.sql
   ```

5. **Verify Tables Created:**
   - Check you have tables like: `users`, `students`, `instructors`, `classes`, etc.

---

## Step 3: File Upload

### Option A: Using File Manager (Easiest)

1. **Go to File Manager** in cPanel
2. Navigate to your document root (e.g., `public_html/`)
3. **Upload your project:**
   - Click **Upload**
   - Select all your project files as ZIP
   - After upload, right-click → **Extract**

### Option B: Using FTP (FileZilla)

1. **Get FTP credentials** from cPanel → FTP Accounts
2. **Connect with FileZilla:**
   ```
   Host: ftp.yourdomain.com
   Username: your_ftp_user
   Password: your_ftp_password
   Port: 21
   ```
3. Upload all files to document root

### Option C: Using SSH (Advanced)

```bash
# Login to server
ssh username@yourdomain.com

# Navigate to web root
cd public_html

# Clone from Git (if using Git)
git clone https://github.com/yourusername/eclass.git

# Or upload via SCP from your computer
scp -r /path/to/project username@yourdomain.com:~/public_html/
```

---

## Step 4: Environment Configuration

### A. Create .env File

In your project root (via File Manager or SSH), create `.env`:

```bash
# Database Configuration
DB_HOST=localhost
DB_USER=username_eclass_user
DB_PASSWORD=your_database_password_here
DB_NAME=username_eclass

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=generate_very_long_random_string_here_at_least_50_chars
PRODUCTION_DOMAIN=yourdomain.com

# Email Configuration (IMPORTANT for Forgot Password!)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=eclass@yourdomain.com
SENDER_PASSWORD=your_gmail_app_password_here
SENDER_NAME=E-Class Record System - ISU Cauayan

# Optional: Production settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### B. Generate Secret Key

**On your local computer, run:**
```python
import secrets
print(secrets.token_hex(32))
```

Copy the output and use it as `SECRET_KEY` in `.env`

### C. Update db_conn.py for Production

Open `utils/db_conn.py` and ensure it uses environment variables:

```python
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'e_class_record'),
}
```

---

## Step 5: Python Application Setup

### A. Set Up Python App in cPanel

1. **Go to "Setup Python App"** in cPanel

2. **Create Application:**
   ```
   Python Version: 3.9 or higher
   Application Root: /home/username/public_html (or your path)
   Application URL: / (or your subdomain)
   Application Startup File: passenger_wsgi.py
   Application Entry Point: app
   ```

3. **Click "CREATE"**

### B. Create passenger_wsgi.py

In your project root, create `passenger_wsgi.py`:

```python
import sys
import os

# Add your project directory to the sys.path
INTERP = os.path.expanduser("~/virtualenv/public_html/3.9/bin/python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import your Flask app
from app import app as application
```

### C. Install Dependencies

**Via cPanel Terminal or SSH:**

```bash
# Enter virtual environment
source ~/virtualenv/public_html/3.9/bin/activate

# Navigate to project
cd ~/public_html

# Install requirements
pip install -r requirements.txt
```

**Add to requirements.txt if not present:**
```
python-dotenv==1.0.0
gunicorn==21.2.0
```

### D. Configure .htaccess

Create/update `.htaccess` in your document root:

```apache
# Force HTTPS
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Python Application
PassengerAppRoot /home/username/public_html
PassengerBaseURI /
PassengerPython /home/username/virtualenv/public_html/3.9/bin/python3

# Increase upload size for student photos
php_value upload_max_filesize 10M
php_value post_max_size 10M
```

---

## Step 6: SSL Certificate (HTTPS)

### Option A: Free SSL via cPanel (Let's Encrypt)

1. **Go to SSL/TLS Status** in cPanel
2. Click **Run AutoSSL**
3. Wait for completion (2-5 minutes)
4. Your site will now use HTTPS

### Option B: Cloudflare (Free + CDN)

1. **Sign up at cloudflare.com**
2. **Add your domain**
3. **Update nameservers** (provided by Cloudflare)
4. **Set SSL/TLS mode** to "Full (Strict)"
5. **Force HTTPS** in SSL/TLS settings

### Verify HTTPS Works

Visit: `https://yourdomain.com`
- Should see padlock icon
- No security warnings

---

## Step 7: Email Configuration for Forgot Password

### Option A: Gmail (Current Setup)

**Already configured in code!** Just add to `.env`:

```bash
SENDER_EMAIL=your-gmail@gmail.com
SENDER_PASSWORD=your_app_password_here
```

**Get Gmail App Password:**
1. Enable 2FA: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password

### Option B: cPanel Email

**Create email account in cPanel:**
1. Go to **Email Accounts**
2. Create: `noreply@yourdomain.com`
3. Set strong password

**Update .env:**
```bash
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
SENDER_EMAIL=noreply@yourdomain.com
SENDER_PASSWORD=your_email_password
```

### Option C: SendGrid (Recommended for Production)

**Free: 100 emails/day**

1. Sign up: https://sendgrid.com
2. Create API key
3. Update .env:
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SENDER_EMAIL=noreply@yourdomain.com
SENDER_PASSWORD=your_sendgrid_api_key
```

---

## Step 8: Testing

### A. Check Application Status

1. **Go to "Setup Python App"** in cPanel
2. Your app should show **"Running"**
3. If showing error, check logs

### B. Test Website

**1. Homepage:**
```
Visit: https://yourdomain.com
Should load: Login page
```

**2. Database Connection:**
```
Try logging in with test account
If error: Check database credentials in .env
```

**3. Forgot Password:**
```
1. Click "Forgot Password?"
2. Enter test email
3. Check email received
4. Click reset link - should go to HTTPS URL
```

**4. Student Registration:**
```
1. Try registering new student
2. Upload photos
3. Verify photos saved in static/uploads/
```

### C. Check Logs

**Application Logs:**
```bash
# Via SSH
tail -f ~/logs/eclass_access.log
tail -f ~/logs/eclass_error.log

# Or check in cPanel → Errors
```

**Python Errors:**
```bash
# Check passenger log
tail -f ~/passenger.log
```

---

## Step 9: Troubleshooting

### Issue: 500 Internal Server Error

**Fix:**
1. Check `.htaccess` syntax
2. Verify Python path in `passenger_wsgi.py`
3. Check error logs in cPanel
4. Ensure all dependencies installed

**Common causes:**
```bash
# Missing module
pip install flask flask-socketio pymysql

# Wrong Python path
which python3  # Use this path in passenger_wsgi.py

# Permission issues
chmod -R 755 ~/public_html
```

### Issue: Password Reset Shows localhost URL

**Fix:** Ensure in `.env`:
```bash
FLASK_ENV=production
PRODUCTION_DOMAIN=yourdomain.com  # NO http:// or https://
```

**Restart app:**
```bash
# Via cPanel: Setup Python App → Restart
# Or touch passenger_wsgi.py
touch ~/public_html/passenger_wsgi.py
```

### Issue: Database Connection Failed

**Check:**
```bash
# Test database connection
mysql -u username_eclass_user -p username_eclass

# If fails, verify:
1. Database name is correct (with cPanel prefix)
2. User has privileges
3. Password is correct in .env
```

### Issue: Email Not Sending

**Debug:**
```python
# Test SMTP connection via SSH Python
python3
>>> import smtplib
>>> server = smtplib.SMTP('smtp.gmail.com', 587)
>>> server.starttls()
>>> server.login('your-email@gmail.com', 'your-app-password')
>>> server.quit()
```

**If fails:**
- Verify SMTP credentials
- Check port 587 is not blocked
- Try port 465 with SSL

### Issue: Static Files (CSS/Images) Not Loading

**Fix:**
```bash
# Check file permissions
chmod -R 755 ~/public_html/static

# Verify .htaccess allows static files
# Add to .htaccess:
<FilesMatch "\.(css|js|png|jpg|gif|ico)$">
    Allow from all
</FilesMatch>
```

### Issue: Upload Folder Not Writable

**Fix:**
```bash
# Create upload directory
mkdir -p ~/public_html/static/uploads/student_photos

# Set permissions
chmod -R 777 ~/public_html/static/uploads
```

---

## Post-Deployment Checklist

### Security:
- [ ] HTTPS enabled (SSL certificate active)
- [ ] Strong secret key in .env
- [ ] Database user has strong password
- [ ] .env file is NOT accessible via web (add to .htaccess)
- [ ] File upload directory has proper permissions
- [ ] Admin accounts have strong passwords

### Functionality:
- [ ] Login works (admin, instructor, student)
- [ ] Registration works with photo uploads
- [ ] Forgot password sends email with HTTPS link
- [ ] Password reset works
- [ ] Classes can be created
- [ ] Students can join classes
- [ ] Grades can be entered and computed
- [ ] Email notifications work

### Performance:
- [ ] Static files load quickly
- [ ] Database queries are fast
- [ ] No memory issues
- [ ] Application logs show no errors

### Monitoring:
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Schedule database backups
- [ ] Monitor disk space
- [ ] Check error logs weekly

---

## Maintenance

### Daily Backups

**Via cPanel:**
1. Go to **Backup**
2. Enable **Automatic Backups**
3. Download weekly backups

**Via SSH (Automated):**
```bash
# Create backup script
nano ~/backup-eclass.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
mysqldump -u username_eclass_user -p'password' username_eclass > ~/backups/eclass_$DATE.sql
tar -czf ~/backups/eclass_files_$DATE.tar.gz ~/public_html
find ~/backups -type f -mtime +7 -delete
```

```bash
# Make executable
chmod +x ~/backup-eclass.sh

# Schedule daily via cron
crontab -e
# Add: 0 2 * * * ~/backup-eclass.sh
```

### Update Application

```bash
# Via SSH
cd ~/public_html
git pull origin main  # if using Git
pip install -r requirements.txt
touch passenger_wsgi.py  # Restart app
```

---

## Quick Reference

### Restart Application
```bash
# Method 1: Via cPanel
Setup Python App → Click "Restart"

# Method 2: Via SSH
touch ~/public_html/passenger_wsgi.py
```

### View Logs
```bash
# Application logs
tail -f ~/logs/eclass_error.log

# Passenger logs
tail -f ~/passenger.log

# Python print() output
tail -f ~/logs/passenger.log
```

### Database Access
```bash
# Via command line
mysql -u username_eclass_user -p username_eclass

# Via phpMyAdmin
cPanel → phpMyAdmin → Select database
```

### File Permissions
```bash
# Web files (read/execute)
chmod -R 755 ~/public_html

# Upload directory (read/write/execute)
chmod -R 777 ~/public_html/static/uploads

# .env file (read only)
chmod 600 ~/public_html/.env
```

---

## Support Resources

### cPanel Documentation
- https://docs.cpanel.net/

### Python on cPanel
- https://docs.cpanel.net/cpanel/software/python-selector/

### Flask Deployment
- https://flask.palletsprojects.com/en/latest/deploying/

### Email Issues
- Gmail: https://support.google.com/accounts/answer/185833
- SendGrid: https://docs.sendgrid.com/

---

## Summary

You now have a complete production deployment! Your E-Class Record System is:

✅ **Live** on your domain with HTTPS
✅ **Secure** with SSL and environment variables
✅ **Functional** with forgot password feature
✅ **Backed up** with automated backups
✅ **Monitored** with error logging

**Your forgot password links will now show:**
```
https://yourdomain.com/reset-password/abc123token
```
Instead of:
```
http://127.0.0.1:5000/reset-password/abc123token
```

**Need help?** Check the troubleshooting section or contact your hosting support!

🎉 **Congratulations on going live!**
