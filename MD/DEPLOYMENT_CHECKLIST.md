# ✅ cPanel Deployment Quick Checklist

## Before Deployment
- [ ] Test application locally (all features working)
- [ ] Generate strong SECRET_KEY
- [ ] Get Gmail App Password or email credentials
- [ ] Prepare domain name
- [ ] Backup local database

## cPanel Setup (30 minutes)
- [ ] Create MySQL database in cPanel
- [ ] Create database user with strong password
- [ ] Grant ALL PRIVILEGES to user
- [ ] Import SQL files via phpMyAdmin
- [ ] Verify all tables created

## File Upload (20 minutes)
- [ ] Upload all project files to document root
- [ ] Extract if uploaded as ZIP
- [ ] Verify all files present

## Configuration (15 minutes)
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all values in `.env`:
  - [ ] Database credentials (with cPanel prefix)
  - [ ] SECRET_KEY (generated)
  - [ ] PRODUCTION_DOMAIN (your domain)
  - [ ] Email credentials (Gmail App Password)
  - [ ] FLASK_ENV=production
- [ ] Save `.env` file

## Python App Setup (20 minutes)
- [ ] Go to "Setup Python App" in cPanel
- [ ] Create new Python application
- [ ] Set Python version (3.9+)
- [ ] Set application root path
- [ ] Set startup file: `passenger_wsgi.py`
- [ ] Update `passenger_wsgi.py` with correct Python path
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start application

## SSL Certificate (5 minutes)
- [ ] Go to SSL/TLS Status in cPanel
- [ ] Run AutoSSL
- [ ] Wait for completion
- [ ] Verify HTTPS works

## Testing (20 minutes)
- [ ] Visit https://yourdomain.com
- [ ] Test login (admin, instructor, student)
- [ ] Test registration with photo uploads
- [ ] Test forgot password:
  - [ ] Request reset link
  - [ ] Check email received
  - [ ] Verify link is HTTPS (not localhost)
  - [ ] Reset password successfully
- [ ] Test class creation
- [ ] Test student join request
- [ ] Test grade entry

## Final Steps (10 minutes)
- [ ] Set file permissions (755 for web, 777 for uploads)
- [ ] Verify `.env` is not publicly accessible
- [ ] Set up automatic backups in cPanel
- [ ] Document admin credentials securely
- [ ] Test all email notifications

## Post-Deployment
- [ ] Monitor error logs for 24 hours
- [ ] Test on mobile devices
- [ ] Train users/staff
- [ ] Create user documentation
- [ ] Set up monitoring (UptimeRobot, etc.)

---

## Quick Commands

### Restart Application
```bash
touch ~/public_html/passenger_wsgi.py
```

### View Logs
```bash
tail -f ~/passenger.log
tail -f ~/logs/eclass_error.log
```

### Test Database
```bash
mysql -u username_eclass_user -p username_eclass
```

### Install Dependencies
```bash
source ~/virtualenv/public_html/3.9/bin/activate
pip install -r requirements.txt
```

---

## Troubleshooting

### Password Reset Shows Localhost
**Fix:** Check `.env` has:
```
FLASK_ENV=production
PRODUCTION_DOMAIN=yourdomain.com
```
Then restart: `touch passenger_wsgi.py`

### 500 Error
**Check:**
1. Error logs in cPanel
2. Python path in `passenger_wsgi.py`
3. All dependencies installed
4. Database credentials correct

### Email Not Sending
**Check:**
1. SMTP credentials in `.env`
2. Port 587 not blocked
3. Test with: `python -c "import smtplib; ..."`

---

## Support
- [Full Guide](CPANEL_DEPLOYMENT_GUIDE.md)
- cPanel Documentation: https://docs.cpanel.net/
- Contact hosting support if needed

**Estimated Total Time: ~2 hours**
