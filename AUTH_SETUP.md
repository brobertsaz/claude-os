# Claude OS Authentication Setup

Simple email/password authentication to keep strangers out of your Claude OS frontend.

## Features

✅ **Optional Authentication** - Disabled by default, enable when needed
✅ **Environment-based** - No database required for user management
✅ **JWT Tokens** - 7-day token expiration
✅ **Secure** - Bcrypt password hashing
✅ **Simple** - Single user account via environment variables

## Quick Start

### 1. Enable Authentication

Set environment variables in your `.env` file or server environment:

```bash
# Required: Email for login
CLAUDE_OS_EMAIL=admin@example.com

# Option 1: Plain password (development only - will be hashed automatically)
CLAUDE_OS_PASSWORD=your_secure_password_here

# Option 2: Pre-hashed password (recommended for production)
CLAUDE_OS_PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5hhA82jdg8jpu

# Optional: Custom secret key for JWT (auto-generated if not set)
CLAUDE_OS_SECRET_KEY=your-super-secret-key-min-32-chars
```

### 2. Generate Password Hash (Production)

For production, use a pre-hashed password instead of plain text:

```bash
# Install dependencies first
cd ~/Projects/claude-os
source venv/bin/activate
pip install -r requirements.txt

# Generate hash
python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_password_here'))"
```

Copy the output and use it as `CLAUDE_OS_PASSWORD_HASH` in your `.env` file.

### 3. Restart Claude OS

```bash
# Local (Mac)
./stop.sh
./start.sh

# Production Server
sudo systemctl restart claude-os
```

### 4. Login

Visit your Claude OS frontend:
- Local: http://localhost:5173/login
- Production: https://your-domain.com/login

Use the email and password you configured.

## Production Deployment

### Server Environment Variables

Add to `/opt/claude-os/.env`:

```bash
CLAUDE_OS_EMAIL=admin@pistn.com
CLAUDE_OS_PASSWORD_HASH=$2b$12$xyz...  # Generated hash
CLAUDE_OS_SECRET_KEY=your-32-char-secret
```

Restart the service:

```bash
sudo systemctl restart claude-os
```

## Disable Authentication

To disable authentication (open access):

```bash
# Remove or comment out these variables in .env:
# CLAUDE_OS_EMAIL=...
# CLAUDE_OS_PASSWORD=...
# CLAUDE_OS_PASSWORD_HASH=...
```

Restart Claude OS. The frontend will allow access without login.

## How It Works

### Backend (FastAPI)

- **`/api/auth/login`** - Login endpoint, returns JWT token
- **`/api/auth/me`** - Get current user info
- **`/api/auth/status`** - Check if authentication is enabled

### Frontend (React)

- **Login Page** - Beautiful gradient login form
- **Auth Context** - Manages authentication state
- **Protected Routes** - Automatically redirects to login if not authenticated
- **Token Storage** - JWT stored in localStorage (7-day expiration)

### Security Features

✅ **Bcrypt hashing** - Industry-standard password encryption
✅ **JWT tokens** - Stateless authentication
✅ **Automatic expiration** - Tokens expire after 7 days
✅ **HTTPS recommended** - Use SSL in production
✅ **No database needed** - Single user, environment-based

## Troubleshooting

### "Authentication is not configured"

You haven't set the `CLAUDE_OS_EMAIL` environment variable. Set it and restart.

### "Incorrect email or password"

Check your `.env` file:
- Email matches exactly (case-sensitive)
- If using `CLAUDE_OS_PASSWORD`, make sure it's correct
- If using `CLAUDE_OS_PASSWORD_HASH`, regenerate the hash

### Login page doesn't appear

Make sure your Claude OS frontend is running:

```bash
# Local development
cd frontend
npm run dev

# Production (should be served by Nginx)
curl http://localhost:5173
```

### Token expired

Tokens last 7 days. Just login again to get a new token.

## Multiple Users

This system is designed for single-user access. For multiple users:

1. **Simple approach**: Share one account with your team
2. **Advanced approach**: Extend the auth system to use a database (requires custom implementation)

For most teams deploying Claude OS internally, a single shared account is sufficient since it's:
- Behind your firewall
- For trusted team members only
- Just to keep strangers out (not enterprise-grade auth)

## Security Best Practices

### Development (Local)

```bash
CLAUDE_OS_EMAIL=dev@localhost
CLAUDE_OS_PASSWORD=dev123
```

Fine for local development. Password is hashed automatically.

### Production (Server)

```bash
CLAUDE_OS_EMAIL=admin@yourcompany.com
CLAUDE_OS_PASSWORD_HASH=$2b$12$xyz...  # Pre-hashed
CLAUDE_OS_SECRET_KEY=randomly-generated-32-char-secret
```

✅ **Use hashed passwords**
✅ **Use strong secret keys**
✅ **Use HTTPS/SSL**
✅ **Rotate passwords periodically**

---

**Questions?** Check the main Claude OS README or open an issue on GitHub.
