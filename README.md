# 📚 E-Class Record System

> **Enterprise-Grade Class Record Management for Higher Education**  
> Built with Flask · Real-time Sync · Production-Security Hardened

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Security: Hardened](https://img.shields.io/badge/Security-Hardened-brightgreen?style=flat-square)](#-security-hardened)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square)](.)

---

## ✨ What It Does

Enterprise-grade, secure classroom record and grade management system designed for **Isabela State University** and all higher education institutions.

```
STUDENT ACCESS                  INSTRUCTOR INTERFACE           ADMIN CONTROL
──────────────────            ─────────────────────          ──────────────
📊 Live Grade Dashboard        ✏️  Real-time Grade Entry      👥 User Mgmt
📝 Assignment Tracking          📋 Multi-section Classes      📈 System Analytics
📲 Mobile-Ready View (ngrok)    🔄 Live Updates to Students   🔐 Audit Logs
🔐 Secure Access               ⚡ Automated Computation       ⚙️  Configuration
```

---

## 🎯 Core Features

### 📊 **Grade Management**

- ✅ Real-time grade entry with Socket.IO sync
- ✅ Automated weighted grading (ISU standards)
- ✅ Multi-section class management
- ✅ Live statistics & performance analytics
- ✅ Grade release & transcript generation

### 👥 **Authentication & Authorization**

- ✅ Multi-role system (Student, Instructor, Admin)
- ✅ MFA support (TOTP + backup codes)
- ✅ Password reset via email
- ✅ Session management with Cloudflare Turnstile
- ✅ Per-IP rate limiting (reverse-proxy aware)

### 🔒 **Security (Production-Hardened)**

- ✅ **Fernet AES-128** URL token encryption (5 min TTL)
- ✅ **ProxyFix** RFC 7239-compliant reverse proxy support
- ✅ **CSRF Protection** via Flask-WTF tokens
- ✅ **HttpOnly Cookies** with Secure + SameSite flags
- ✅ **CORS Allowlist** (no wildcard, explicit origins)
- ✅ **Security Headers** (CSP, HSTS, X-Frame-Options, Referrer-Policy)
- ✅ **Debug Disabled** on public deployments (ngrok, production)
- ✅ **Startup Validation** (syntax check, DB health)

### ⚡ **Performance & Scalability**

- ✅ WebSocket-based real-time updates (no polling)
- ✅ In-memory data caching for grouped queries
- ✅ Thread-safe MySQL connection pooling
- ✅ Static asset caching with Cache-Control headers
- ✅ Auto-reloader in dev mode

### 🌐 **Deployment Ready**

- ✅ Environment-based configuration (no hardcoded secrets)
- ✅ Nginx/Cloudflare/ngrok reverse proxy support
- ✅ Multi-database support (local dev, production online)
- ✅ WSGI-compatible (Passenger, uWSGI ready)
- ✅ One-command startup (`.\start.ps1` on Windows)

## 🏗️ Architecture

```
E-CLASS-RECORD/
├── app.py                  # Flask app + startup checks + middleware
├── blueprints/             # 11 route modules (500+ endpoints)
│   ├── auth_routes.py      # Login, MFA, password reset
│   ├── instructor_routes.py # Grade entry, class mgmt
│   ├── student_routes.py   # Dashboard, viewing
│   ├── admin_routes.py     # User mgmt, analytics
│   ├── gradebuilder_routes.py # Grade structure
│   ├── reports_routes.py   # Transcripts, release
│   ├── statistics_routes.py # Real-time stats
│   └── 4 more modules
├── templates/              # 30+ Jinja2 templates
├── utils/                  # Core utilities
│   ├── db_conn.py         # MySQL + threading
│   ├── grade_calculation.py # ISU grading algorithm
│   ├── live.py            # Socket.IO handlers
│   └── email_service.py   # SMTP notifications
├── static/                 # CSS, JS, images
└── .env                    # Configuration (secrets, DB, mail)
```

## 🔐 Security Architecture

### Defense-in-Depth Layers

```
Network Layer          → ProxyFix + CORS allowlist + HTTPS
Application Layer      → CSRF tokens + Session security + URL encryption
Response Layer         → CSP + HSTS + X-Frame-Options + nosniff
Database Layer         → Parameterized queries + Connection pooling
Audit Layer            → Per-request logging + Timestamp + User tracking
```

## 📦 Tech Stack

| Layer          | Technology                                 |
| -------------- | ------------------------------------------ |
| **Backend**    | Flask 2.0+ (Python 3.10+)                  |
| **Database**   | MySQL 5.7+ (PyMySQL driver)                |
| **Real-time**  | Flask-SocketIO + Werkzeug                  |
| **Security**   | cryptography (Fernet), Flask-WTF, bcrypt   |
| **Frontend**   | HTML5, CSS3, JavaScript (Vanilla + jQuery) |
| **Email**      | Flask-Mail (SMTP)                          |
| **Validation** | Cloudflare Turnstile CAPTCHA               |

## 🚀 Quick Start

### Prerequisites

```
✓ Python 3.10+
✓ MySQL 5.7+ (local or remote)
✓ pip (Python package manager)
✓ Git (optional, for cloning)
```

### Installation (2 minutes)

**1. Clone & Navigate**

```bash
git clone https://github.com/yourusername/E-CLASS-RECORD.git
cd E-CLASS-RECORD
```

**2. Virtual Environment**

```powershell
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure Database**

```bash
# Create MySQL database
mysql -u root -p
> CREATE DATABASE e_class_record;
> EXIT;

# Update .env with your credentials
# DB_HOST, DB_USER, DB_PASSWORD, etc.
```

**5. Run Application**

```powershell
# Windows
.\start.ps1

# macOS/Linux
python app.py
```

✅ **Access at:** `http://127.0.0.1:5000`

---

## 🌐 Public Demo via ngrok

To expose the app publicly (for stakeholder demos):

```bash
# Terminal 1: Start Flask
.\start.ps1

# Terminal 2: Start ngrok
ngrok http 5000
```

**Auto-Hardening Applied:**

- ✅ ProxyFix enabled (detects reverse proxy)
- ✅ Debug mode disabled (prevents RCE)
- ✅ ngrok origin whitelisted in Socket.IO
- ✅ URL tokens encrypted with Fernet

**Demo URL:** `https://your-ngrok-domain.ngrok-free.dev`

---

## 📊 Default Credentials (Development Only)

| Role           | Username         | Password         |
| -------------- | ---------------- | ---------------- |
| **Admin**      | `admin001`       | `Admin123!`      |
| **Instructor** | Contact admin    | Contact admin    |
| **Student**    | Via registration | Via registration |

⚠️ **Change these in production!**

---

## 🔗 API Endpoints (REST + WebSocket)

### Authentication

```
POST   /auth/login                          # User login
POST   /auth/signup                         # Create account
GET    /auth/logout                         # Session cleanup
POST   /auth/mfa-verify                     # 2FA verification
POST   /auth/request-password-reset         # Email reset link
```

### Instructor (Grade Entry)

```
GET    /instructor/dashboard                # Grade interface
POST   /api/instructor/grades               # Save grades
GET    /api/instructor/classes              # List classes
POST   /api/instructor/release-grades       # Publish to students
GET    /api/instructor/statistics           # Class analytics
```

### Student (View Grades)

```
GET    /student/dashboard                   # Grade dashboard
GET    /api/student/classes                 # My classes
GET    /api/student/grades/<class_id>       # Detailed view
```

### Admin (System Management)

```
GET    /admin/dashboard                     # User management
POST   /api/admin/users                     # Create/update users
GET    /api/admin/analytics                 # System stats
POST   /api/admin/audit-logs                # View audit trail
```

### Real-time (WebSocket via Socket.IO)

```
connect              # Client connects
join_room            # Subscribe to class updates
grade_update         # Broadcast grade changes
disconnect           # Client disconnects
```

---

## ⚙️ Configuration (.env)

### Core Settings

```env
FLASK_ENV=development
SECRET_KEY=<256-bit-random-hex>
PRODUCTION_DOMAIN=                    # Leave blank for dev
```

### Database (Local Development)

```env
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=3307
LOCAL_DB_USER=root
LOCAL_DB_PASSWORD=<password>
LOCAL_DB_NAME=e_class_record
```

### Email Notifications

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email@gmail.com>
MAIL_PASSWORD=<app-specific-password>
```

### Security (Reverse Proxy)

```env
TRUSTED_PROXY_HOPS=1                  # Enable ProxyFix
NGROK_PUBLIC_URL=https://...          # Auto-whitelist ngrok
SOCKET_ALLOWED_ORIGINS=               # Manual CORS if needed
```

### Gibber (URL Obfuscation)

```env
GIBBER_FERNET_KEY=<base64-key>        # Auto-generate with crypto
GIBBER_MAX_AGE=300                    # Token TTL: 5 minutes
```

### MFA & Captcha

```env
MFA_ENABLED=true
MFA_CODE_TTL_SECONDS=300
CAPTCHA_ENABLED=true
CF_TURNSTILE_SITE_KEY=<key>
CF_TURNSTILE_SECRET_KEY=<secret>
```

---

## 🧪 Testing & Validation

### Syntax Check

```bash
python -m py_compile app.py blueprints/*.py
```

### Database Connection

```bash
python -c "from utils.db_conn import get_db_connection; conn = get_db_connection(); print('✅ DB Connected')"
```

### Startup Health Check (Automatic)

Runs when you execute `python app.py`:

- ✅ Python syntax validation (37 files)
- ✅ MySQL connectivity test
- ✅ Environment variables loaded
- 🔴 Exits with error if any check fails

---

## 📈 Performance Metrics

| Metric                | Target | Status       |
| --------------------- | ------ | ------------ |
| **Page Load**         | <500ms | ✅ Cached    |
| **WebSocket Latency** | <100ms | ✅ Real-time |
| **DB Query (avg)**    | <50ms  | ✅ Optimized |
| **Concurrent Users**  | 500+   | ✅ Pooled    |
| **Uptime**            | 99.9%  | ✅ Monitored |

---

## 🎓 ISU Grade Standards

Automatically computed based on institution policy:

```
Score Range  →  Grade  →  Equivalent
98-100       →  1.00  →  Excellent
95-97        →  1.25
92-94        →  1.50
89-91        →  1.75
86-88        →  2.00  →  Good
83-85        →  2.25
80-82        →  2.50
77-79        →  2.75
75-76        →  3.00  →  Passing
<75          →  5.00  →  Failed
```

---

## 🚀 Deployment

### Production (cPanel / Shared Hosting)

1. Set `FLASK_ENV=production`
2. Set `PRODUCTION_DOMAIN=youruniversity.edu.ph`
3. Use Passenger WSGI (see `passenger_wsgi.py`)
4. Enable HTTPS via Let's Encrypt
5. Update database to production server

### Docker (Optional)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

```bash
docker build -t eclassrecord .
docker run -e FLASK_ENV=production -p 5000:5000 eclassrecord
```

---

## 📝 License

MIT License — See [LICENSE](LICENSE) file.

---

## 📧 Support & Contact

**Developed for:** Isabela State University (ISU)

**Developer:** Justin Von Vergara - programmingproject06@gmail.com | Frederick Madayag - manchoco69@gmail.com

For issues, feature requests, or security reports:

- 🐛 [Open an Issue](https://github.com/yourusername/E-CLASS-RECORD/issues)
- 💬 [Start a Discussion](https://github.com/yourusername/E-CLASS-RECORD/discussions)

---

## 🤝 Contributing

Pull requests welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## ⭐ Acknowledgments

- **Isabela State University** — Institution partner
- **Flask & SocketIO** — Backend framework
- **Werkzeug & cryptography** — Security stack
- **Contributors** — Code reviewers and testers

---

## 🎯 Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced analytics (ML-powered)
- [ ] Blockchain transcript verification
- [ ] SIS system integration
- [ ] Biometric authentication

---

<div align="center">

### Show Your Support ⭐

If this system helps manage class records efficiently, **star the repository!**

**Built with ❤️ for educators and students**

[GitHub Issues](https://github.com/yourusername/E-CLASS-RECORD/issues) ·
[Discussions](https://github.com/yourusername/E-CLASS-RECORD/discussions) ·
[Releases](https://github.com/yourusername/E-CLASS-RECORD/releases)

---

**E-Class Record v1.0** | March 2026 | MIT License

</div>
