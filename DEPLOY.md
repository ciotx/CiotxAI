# CIOTX — Complete Production Deployment Guide

This guide takes you from zero to a fully deployed CIOTX platform. Every single step is included — GitHub setup, server provisioning, CLI distribution, and GitHub integration. Nothing is skipped.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [GitHub Setup](#2-github-setup)
3. [Server Setup](#3-server-setup)
4. [Environment Configuration](#4-environment-configuration)
5. [Deploy the Platform](#5-deploy-the-platform)
6. [SSL & Domain Setup](#6-ssl--domain-setup)
7. [CLI Distribution](#7-cli-distribution)
8. [Verification](#8-verification)
9. [Ongoing Operations](#9-ongoing-operations)

---

## 1. Prerequisites

Before starting, you need:

- A **domain name** (e.g., `ciotx.com`) with DNS access
- A **GitHub account** for the CIOTX organization
- An **Ubuntu 24.04 LTS server** (min 2 vCPU, 4GB RAM, 40GB SSD)
- A **DeepSeek API key** (or OpenAI, or Anthropic) for the AI scanning engine
- A **Razorpay account** (optional — for payment processing)

---

## 2. GitHub Setup

### 2.1 Create the GitHub Organization

1. Go to https://github.com and sign in
2. Click your avatar → **Settings** → **Organizations** → **New organization**
3. Choose **Free** plan
4. Name: `ciotx`
5. Invite your personal account as an owner

### 2.2 Create the Repository

1. Go to https://github.com/ciotx
2. Click **Repositories** → **New repository**
3. Name: `CiotxAI`
4. Description: "AI-powered code security platform"
5. Keep it **Private**
6. Do NOT initialize with README, .gitignore, or license
7. Click **Create repository**

### 2.3 Clone and Push the Codebase

On your local machine (PowerShell):

```powershell
cd C:\Users\adversary\Desktop\CiotxAI
git remote set-url origin https://github.com/ciotx/CiotxAI.git
git push origin main
```

If pushing asks for credentials, use your GitHub username and a **Personal Access Token** as the password (see next step).

### 2.4 Generate Personal Access Tokens

**For yourself (to push code):**

1. Go to https://github.com/settings/tokens
2. Click **Generate new token** → **Classic**
3. Note: "CIOTX Deployment"
4. Scopes: `repo` (full control), `workflow`
5. Click **Generate token**
6. **Copy the token NOW.** It starts with `ghp_`. You won't see it again.
7. Use this token as your password when `git push` asks for credentials

**For CIOTX CLI users (to give CLI access to private repos):**

Same steps as above. Each team member who uses the CLI with private repos needs their own token.

### 2.5 Create the GitHub OAuth App (for user login)

This lets users sign up with "Continue with GitHub."

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Fill in:
   - **Application name:** `CIOTX`
   - **Homepage URL:** `https://ciotx.com`
   - **Authorization callback URL:** `https://api.ciotx.com/v1/auth/github/callback`
4. Click **Register application**
5. Click **Generate a new client secret**
6. Save these values — you'll need them for `.env`:
   - `GITHUB_CLIENT_ID` = the Client ID (shown on the page)
   - `GITHUB_CLIENT_SECRET` = the Client Secret (generated in step 5)

### 2.6 Create the GitHub App (for repo access and PR scanning)

This is separate from the OAuth App. It lets CIOTX access repositories, set webhooks, and post PR comments.

1. Go to https://github.com/settings/apps
2. Click **New GitHub App**
3. Fill in:
   - **GitHub App name:** `CIOTX Scanner`
   - **Homepage URL:** `https://ciotx.com`
   - **Callback URL:** `https://api.ciotx.com/v1/github/callback`
   - **Webhook URL:** `https://api.ciotx.com/v1/webhooks/github`
   - **Webhook secret:** Generate one with `openssl rand -hex 32` on your server
4. **Permissions:**
   - Repository **Contents:** `Read-only`
   - Repository **Metadata:** `Read-only`
   - Repository **Pull requests:** `Read & write`
   - Repository **Commit statuses:** `Read & write`
   - Repository **Webhooks:** `Read & write`
5. **Subscribe to events:**
   - `Push`
   - `Pull request`
6. **Where can this GitHub App be installed?** → `Any account`
7. Click **Create GitHub App**
8. Scroll down to **Private keys** → **Generate a private key**
9. Save the `.pem` file to your server at `/opt/ciotx/github-app.pem`
10. Save these values:
    - `GITHUB_APP_ID` = shown at the top of the app page (a number)
    - `GITHUB_WEBHOOK_SECRET` = the secret you generated in step 3
    - `GITHUB_PRIVATE_KEY_PATH` = `/opt/ciotx/github-app.pem`

### 2.7 Razorpay Setup (for payments)

1. Go to https://dashboard.razorpay.com — create an account or log in
2. Go to **Settings** → **API Keys**
3. Copy the **Key ID** and **Key Secret**
4. Go to **Settings** → **Webhooks** → **Add New Webhook**
5. URL: `https://api.ciotx.com/v1/billing/webhook`
6. Events: `payment.captured`
7. Generate a webhook secret → save it
8. Save these values for `.env`:
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `RAZORPAY_WEBHOOK_SECRET`

### 2.8 DeepSeek API Key

1. Go to https://platform.deepseek.com — create an account or log in
2. Go to **API Keys** → **Create new key**
3. Copy the key (starts with `sk-`)
4. Save for `.env`: `DEEPSEEK_API_KEY`

---

## 3. Server Setup

### 3.1 Provision a Server

Use any provider (AWS, DigitalOcean, Linode, Hetzner, or private Indian hosting). Create an Ubuntu 24.04 LTS instance with at least 2 vCPU, 4GB RAM, 40GB SSD.

### 3.2 SSH into the Server

```bash
ssh root@<YOUR_SERVER_IP>
```

### 3.3 Update System

```bash
apt update && apt upgrade -y
```

### 3.4 Install Essential Packages

```bash
apt install -y curl wget git build-essential ufw
```

### 3.5 Install Docker

```bash
curl -fsSL https://get.docker.com | bash
```

This downloads and runs Docker's official install script. It adds the Docker APT repository and installs Docker Engine.

Add your user to the docker group:

```bash
usermod -aG docker $USER
```

Log out and back in (or run `newgrp docker`) for this to take effect.

Verify:

```bash
docker --version
docker run hello-world
```

### 3.6 Install Docker Compose Plugin

```bash
apt install -y docker-compose-plugin
docker compose version
```

### 3.7 Configure Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
ufw status verbose
```

For production, restrict SSH to your IP only:

```bash
ufw delete allow 22/tcp
ufw allow from <YOUR_STATIC_IP> to any port 22 proto tcp
```

### 3.8 Setup DNS

In your domain provider's DNS settings, create these records:

| Type | Name | Value |
|------|------|-------|
| A | `ciotx.com` | `<YOUR_SERVER_IP>` |
| A | `api.ciotx.com` | `<YOUR_SERVER_IP>` |
| CNAME | `www.ciotx.com` | `ciotx.com` |

---

## 4. Environment Configuration

### 4.1 Clone the Repository

```bash
cd /opt
git clone https://github.com/ciotx/CiotxAI.git ciotx
cd ciotx
```

If the repo is private and you haven't set up SSH keys:

```bash
git clone https://<YOUR_GITHUB_TOKEN>@github.com/ciotx/CiotxAI.git ciotx
```

### 4.2 Generate All Secrets

Run these commands to generate secure random values:

```bash
cd /opt/ciotx
cp .env.example .env

# Generate each secret and append to .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "DB_PASSWORD=$(openssl rand -hex 16)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -hex 16)" >> .env
echo "INTERNAL_API_KEY=$(openssl rand -hex 16)" >> .env
echo "GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 32)" >> .env
echo "RAZORPAY_WEBHOOK_SECRET=$(openssl rand -hex 32)" >> .env
```

### 4.3 Edit .env with Real Values

```bash
nano .env
```

Fill in every value. Here is every variable you need to set:

```bash
# ── MUST SET THESE ────────────────────────────

DEV_MODE=false                                # MUST be false in production
API_BASE_URL=https://api.ciotx.com           # Your API domain
DASHBOARD_URL=https://ciotx.com              # Your dashboard domain
DB_PASSWORD=<from step 4.2>
REDIS_PASSWORD=<from step 4.2>
SECRET_KEY=<from step 4.2>
INTERNAL_API_KEY=<from step 4.2>

# LLM Provider — pick one
DEEPSEEK_API_KEY=sk-xxxxxxxx                 # From step 2.8

# GitHub
GITHUB_CLIENT_ID=Ov23li...                   # From step 2.5
GITHUB_CLIENT_SECRET=...                     # From step 2.5
GITHUB_APP_ID=1234567                        # From step 2.6
GITHUB_WEBHOOK_SECRET=<from step 4.2>
GITHUB_PRIVATE_KEY_PATH=/opt/ciotx/github-app.pem  # From step 2.6

# Razorpay
RAZORPAY_KEY_ID=rzp_live_...                 # From step 2.7
RAZORPAY_KEY_SECRET=...                      # From step 2.7
RAZORPAY_WEBHOOK_SECRET=<from step 4.2>

# ── KEEP DEFAULTS (change only if needed) ────

DATABASE_URL=postgresql+asyncpg://ciotx:${DB_PASSWORD}@postgres:5432/ciotx
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
TRIAL_DAYS=7
TRIAL_SCAN_LIMIT=10
STARTER_SCAN_LIMIT=20
LLM_PROVIDER=auto
```

Save the file: `Ctrl+O`, `Enter`, `Ctrl+X`.

### 4.4 Place the GitHub App Private Key

```bash
# Copy your github-app.pem file to the server
nano /opt/ciotx/github-app.pem
# Paste the contents of the .pem file from step 2.6
# Ctrl+O, Enter, Ctrl+X
chmod 600 /opt/ciotx/github-app.pem
```

---

## 5. Deploy the Platform

### 5.1 Build and Start Everything

```bash
cd /opt/ciotx
docker compose build
docker compose up -d
```

This builds 3 images and starts 5 containers: postgres, redis, api, worker, dashboard.

### 5.2 Verify All Containers Are Running

```bash
docker compose ps
```

All five services should show `Up` or `Up (healthy)`:

```
NAME               STATUS
ciotx-db           Up (healthy)
ciotx-redis        Up (healthy)
ciotx-api          Up
ciotx-worker       Up
ciotx-dashboard    Up
```

### 5.3 Check Logs

```bash
docker compose logs -f
```

Press `Ctrl+C` to stop watching. Look for any ERROR lines. There should be none after a clean start.

### 5.4 Verify the API

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","version":"0.1.0","dev_mode":false}
```

### 5.5 Verify the Dashboard

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

Expected: `200`

---

## 6. SSL & Domain Setup

### 6.1 Install nginx and certbot

```bash
apt install -y nginx certbot python3-certbot-nginx
```

### 6.2 Create nginx Configuration

```bash
nano /etc/nginx/sites-available/ciotx
```

Paste this entire configuration:

```nginx
# Dashboard — ciotx.com
server {
    listen 80;
    server_name ciotx.com www.ciotx.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API — api.ciotx.com
server {
    listen 80;
    server_name api.ciotx.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Save and exit.

### 6.3 Enable the Site

```bash
ln -s /etc/nginx/sites-available/ciotx /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default   # Remove default site
nginx -t                               # Test configuration
systemctl reload nginx
```

### 6.4 Get SSL Certificates

```bash
certbot --nginx -d ciotx.com -d www.ciotx.com -d api.ciotx.com
```

Follow the prompts:
- Enter your email address
- Agree to the terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: yes)

### 6.5 Verify SSL Auto-Renewal

```bash
certbot renew --dry-run
```

Certbot sets up a systemd timer that auto-renews certificates. No manual intervention needed.

### 6.6 Test SSL

```bash
curl -I https://ciotx.com
curl https://api.ciotx.com/health
```

Both should return successful responses with HTTPS.

---

## 7. CLI Distribution

### 7.1 How the CLI Works

The CIOTX CLI is a **single Go binary**. Users download it to their laptop and run it locally. It talks to your production API at `api.ciotx.com`.

Two scanning modes:
- **Local scan** (`ciotx scan --path ./`): Code stays on their machine. Only findings are pushed to the cloud.
- **Cloud scan** (`ciotx scan <repo-url>`): The cloud clones and scans the repo on their behalf.

### 7.2 Build the CLI for Distribution

On your development machine:

```bash
cd /opt/ciotx/cli

# Build for Linux
GOOS=linux GOARCH=amd64 go build -o ciotx-linux-amd64 .

# Build for macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -o ciotx-darwin-amd64 .

# Build for macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o ciotx-darwin-arm64 .

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o ciotx-windows-amd64.exe .
```

### 7.3 Upload to GitHub Releases

1. Go to https://github.com/ciotx/CiotxAI/releases
2. Click **Create a new release**
3. Tag: `v0.1.0`
4. Title: `v0.1.0 — Initial Release`
5. Attach the 4 binary files from step 7.2
6. Click **Publish release**

### 7.4 User Install Instructions

Users install the CLI in 10 seconds:

**macOS / Linux:**
```bash
curl -sSL https://ciotx.com/install | bash
```

**Windows (PowerShell):**
```powershell
irm https://ciotx.com/install.ps1 | iex
```

### 7.5 CLI User Flow

Once installed:

```bash
$ ciotx login
# Opens browser to https://ciotx.com/verify?code=XXXXXX
# User signs in on the website
# CLI receives token

$ ciotx scan --path ./my-project
# Runs local scan (code never leaves machine)
# Pushes findings to dashboard

$ ciotx scan https://github.com/user/repo
# Triggers cloud scan
# Results appear on dashboard

$ ciotx status
# Shows recent scan history
```

### 7.6 Setting CLI Default API URL

The CLI needs to know where your production API is. Users set this once:

```bash
export CIOTX_API_URL=https://api.ciotx.com
export CIOTX_DASHBOARD_URL=https://ciotx.com
```

Or add to their `~/.bashrc` or `~/.zshrc` for persistence.

---

## 8. Verification

### 8.1 End-to-End Test

Run through the complete user flow:

1. **Visit** https://ciotx.com — landing page loads ✅
2. **Click** "Start free trial" → signup page loads ✅
3. **Sign up** with email + password → redirected to dashboard ✅
4. **Connect GitHub** in Settings → authorize → repos appear ✅
5. **Select a repo** → click "Scan Now" → scan runs ✅
6. **View results** — vulnerabilities appear with severity badges ✅
7. **Click a finding** — code viewer + fix suggestion loads ✅

### 8.2 CLI End-to-End Test

```bash
# Install CLI
curl -sSL https://ciotx.com/install | bash

# Authenticate
ciotx login
# Opens browser, sign in, come back to terminal

# Local scan
ciotx scan --path ./my-project

# Cloud scan
ciotx scan https://github.com/ciotx/test-repo

# Check status
ciotx status

# Open dashboard
ciotx dashboard
```

### 8.3 GitHub PR Test

1. Push a commit to a connected repo
2. A webhook fires → scan runs automatically
3. Check the dashboard — a new scan appears
4. (When PR scanning is built) — PR comment is posted

### 8.4 Billing Test

1. Go to https://ciotx.com/billing
2. Click "Subscribe Monthly" on a plan
3. Complete Razorpay payment
4. After payment, the plan status updates to "active"
5. Scan counter resets

---

## 9. Ongoing Operations

### 9.1 Quick Reference

| Task | Command |
|---|---|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Restart | `docker compose restart` |
| Rebuild after code changes | `docker compose down && docker compose up -d --build` |
| View logs | `docker compose logs -f` |
| View specific service logs | `docker compose logs -f api` |
| Check status | `docker compose ps` |
| Resource usage | `docker stats` |

### 9.2 Update the Application

```bash
cd /opt/ciotx
git pull origin main
docker compose down
docker compose up -d --build
docker compose logs -f   # Watch for 5 minutes for errors
```

### 9.3 Rollback

```bash
cd /opt/ciotx
git checkout <LAST_KNOWN_GOOD_TAG>   # e.g., v0.2.0
docker compose down
docker compose up -d --build
```

### 9.4 Database Backups

**Manual backup:**
```bash
docker compose exec postgres pg_dump -U ciotx ciotx | gzip > /opt/backups/ciotx_$(date +%Y%m%d).sql.gz
```

**Automated daily backup:**
```bash
mkdir -p /opt/backups
crontab -e
```

Add this line:
```
0 2 * * * docker compose -f /opt/ciotx/docker-compose.yml exec -T postgres pg_dump -U ciotx ciotx | gzip > /opt/backups/ciotx_$(date +\%Y\%m\%d).sql.gz
```

**Restore from backup:**
```bash
gunzip -c /opt/backups/ciotx_20260713.sql.gz | docker compose exec -T postgres psql -U ciotx ciotx
docker compose restart
```

**Test restores monthly.** A backup you haven't tested is not a backup.

### 9.5 Troubleshooting

| Problem | Command |
|---|---|
| API 500 errors | `docker compose logs api --tail=50` |
| Scans never complete | `docker compose logs worker --tail=50` |
| Database connection errors | `docker compose logs postgres` |
| Redis connection errors | `docker compose exec redis redis-cli -a $REDIS_PASSWORD ping` |
| Container won't start | `docker compose ps` (check for Restarting) |
| Dashboard can't reach API | Check `NEXT_PUBLIC_API_URL` in `.env` |
| SSL certificate expired | `certbot renew --force-renewal && systemctl reload nginx` |
| Disk full | `docker system prune -a` (cleans old images) |

### 9.6 Security Checklist (Re-run Before Going Live)

```
☐ DEV_MODE=false in .env
☐ SECRET_KEY is a 64-char random string (not "change-me-in-production")
☐ All passwords are randomly generated (not defaults)
☐ GitHub webhook secret is set (not empty)
☐ Razorpay webhook secret is set (not empty)
☐ SSL certificates active (https:// works)
☐ Firewall enabled (only 22/80/443 open)
☐ Database not exposed to internet (run: docker compose ps, check no 5432 on 0.0.0.0)
☐ Redis not exposed to internet
☐ Backups configured and tested
☐ Health check endpoint returns {"status":"ok"}
☐ .env is NOT committed to git (verify: git ls-files | grep .env returns nothing)
```
