# Web-Based Debug Terminal

## Overview

The E-Class Record System includes a built-in web-based terminal for debugging and system administration when CLI access is unavailable (e.g., cPanel deployments).

## Access

**URL**: `http://127.0.0.1:5000/terminal`

**Requirements**: Admin login required

## Features

✅ Execute system commands through web interface  
✅ Real-time command output display  
✅ Command history navigation (↑/↓ arrow keys)  
✅ Quick access buttons for common commands  
✅ System information display  
✅ Security: Dangerous commands automatically blocked  
✅ Admin-only access control  
✅ Live log viewer (auto-refresh every 2s)

## Usage

### Basic Commands

```bash
pwd                          # Show current directory
dir                          # List directory contents
cd [path]                    # Change directory
cls / clear                  # Clear terminal screen
help                         # Show available commands
```

### Python Commands

```bash
python --version             # Check Python version
python app.py                # Start Flask app (not recommended in terminal)
python scripts\list_classes.py  # List all classes
pip list                     # Show installed packages
pip install [package]        # Install package
```

### Git Commands

```bash
git status                   # Check repository status
git branch                   # List branches
git log --oneline -10        # Show recent commits
git diff                     # Show changes
```

### Database Commands

## Live Logs

The terminal includes a live log viewer that shows the tail of `app.log` and refreshes every 2 seconds.

- Location: Logs panel below the terminal output
- Source: `app.log` in the project root
- Endpoint: `/terminal/logs`
- If `app.log` is missing, it will display a notice.

Tip: Ensure logging is configured in `app.py` via `logging.basicConfig(level=logging.INFO)` and that logs write to `app.log` (current setup uses a console handler and a file handler through `app.log`).

```bash
mysql -u root -p             # Connect to MySQL (interactive)
python create_admin\create_admin.py  # Create admin user
```

## Keyboard Shortcuts

- **↑ / ↓**: Navigate command history
- **Ctrl + L**: Clear terminal
- **Enter**: Execute command

## Quick Command Buttons

The terminal includes pre-configured quick command buttons for:

- `pwd` - Show current directory
- `dir` - List files
- `python --version` - Python version
- `pip list` - Installed packages
- `git status` - Git repository status
- `git branch` - Git branches
- `python scripts\list_classes.py` - List classes

## Security Features

### Blocked Commands

For safety, the following dangerous commands are automatically blocked:

- `rm -rf` - Recursive force delete (Linux)
- `del /f` - Force delete (Windows)
- `format` - Format disk
- `shutdown` - System shutdown
- `reboot` - System reboot
- `mkfs` - Make filesystem

### Access Control

- Only users with admin role can access the terminal
- In production, requires `session['role'] == 'admin'`
- All commands are logged for security auditing
- 30-second timeout for long-running commands

## Common Use Cases

### 1. Check System Status

```bash
python --version
pip list
git status
pwd
```

### 2. Database Operations

```bash
python scripts\list_classes.py
mysql -u root -p e_class_record -e "SELECT COUNT(*) FROM classes"
```

### 3. View Logs

```bash
type app.log
dir db
```

### 4. Package Management

```bash
pip list
pip show flask
pip install package-name
```

### 5. File Operations

```bash
dir templates
type requirements.txt
cd utils
```

## Troubleshooting

### Terminal Not Loading

1. Ensure you're logged in as admin
2. Check browser console for errors
3. Verify Flask server is running

### Commands Not Executing

1. Check if command is blocked for security
2. Verify command syntax is correct
3. Check terminal info shows correct directory

### Permission Denied Errors

1. Some operations require elevated permissions
2. Try running app with appropriate privileges
3. Check file/directory permissions

### Timeout Errors

- Commands timeout after 30 seconds
- For long-running operations, use background processes
- Consider running intensive tasks outside the web terminal

## Best Practices

1. **Use for Debugging Only**: Not a replacement for SSH/CLI access
2. **Keep Sessions Short**: Don't leave terminal open unnecessarily
3. **Be Cautious**: You have direct system access
4. **Check Working Directory**: Use `pwd` before file operations
5. **Test Commands**: Verify command syntax before execution
6. **Logout When Done**: Close session after debugging

## Limitations

- No interactive command support (e.g., `vim`, `nano`)
- 30-second timeout for all commands
- No persistent shell state (each command runs in new shell)
- No piping or complex shell scripting
- Limited environment variable support

## Alternative Access

If the web terminal is insufficient for your needs, consider:

1. **SSH Access**: Request SSH access from hosting provider
2. **File Manager**: Use cPanel file manager for file operations
3. **phpMyAdmin**: For database operations
4. **Scheduled Tasks**: Use cron jobs for automated tasks

## Support

For issues with the web terminal:

1. Check the Flask application logs (`app.log`)
2. Review browser console for JavaScript errors
3. Verify admin authentication is working
4. Test with simple commands first (`pwd`, `dir`)

---

**⚠️ Warning**: This terminal provides direct system access. Use responsibly and only for debugging purposes.
