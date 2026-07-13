# CIOTX — Production Deployment Guide

This guide assumes a fresh Ubuntu 24.04 LTS server with nothing installed. Every command is included exactly as it should be run. Copy, paste, deploy.

---

## 1. Server Setup

### 1.1 Create an Ubuntu Server

Minimum specs: 2 vCPU, 4GB RAM, 40GB SSD.

Use any provider: AWS EC2 (t3.medium), DigitalOcean, Linode, Hetzner, or your private Indian hosting provider.

### 1.2 SSH Into the Server

```bash
ssh root@<YOUR_SERVER_IP>
```

### 1.3 Update System Packages

```bash
apt update && apt upgrade -y
```

### 1.4 Install Essential Tools

```bash
apt install -y curl wget git build-essential ufw
```

---

## 2. Install Docker

### 2.1 Docker Engine

```bash
curl -fsSL https://get.docker.com | bash
```

This downloads and runs Docker's official install script. It adds the Docker APT repository and installs `docker-ce`, `docker-ce-cli`, and `containerd.io`.

### 2.2 Add Your User to the Docker Group

```bash
usermod -aG docker $USER
```

Log out and back in for this to take effect, or run `newgrp docker`.

### 2.3 Verify Docker

```bash
docker --version
docker run hello-world
```

The second command should print "Hello from Docker!" and exit cleanly.

### 2.4 Install Docker Compose (Plugin)

```bash
apt install -y docker-compose-plugin
```

Verify:

```bash
docker compose version
```

---

## 3. Firewall Configuration

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp       # SSH
ufw allow 80/tcp       # HTTP
ufw allow 443/tcp      # HTTPS
ufw enable
ufw status verbose
```

Port 22 should be restricted to your IP in production:

```bash
ufw delete allow 22/tcp
ufw allow from <YOUR_STATIC_IP> to any port 22 proto tcp
```

---

## 4. Clone the Repository

### 4.1 Generate a GitHub Personal Access Token (if private repo)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Copy the generated token (starts with `ghp_`)

### 4.2 Clone

```bash
cd /opt
git clone https://github.com/ciotx/CiotxAI.git ciotx
cd ciotx
```

If the repo is private and you're not using SSH keys:

```bash
git clone https://<TOKEN>@github.com/ciotx/CiotxAI.git ciotx
```

Alternatively with SSH:

```bash
git clone git@github.com:ciotx/CiotxAI.git ciotx
```

---

## 5. Configure Environment

### 5.1 Create .env from .env.example

```bash
cp .env.example .env
```

### 5.2 Generate Secrets

```bash
# Generate a secure JWT secret
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Generate database password
echo "DB_PASSWORD=$(openssl rand -hex 16)" >> .env

# Generate Redis password
echo "REDIS_PASSWORD=$(openssl rand -hex 16)" >> .env

# Generate internal API key
echo "INTERNAL_API_KEY=$(openssl rand -hex 16)" >> .env
```

### 5.3 Edit .env With Real Values

```bash
nano .env
```

Set these values:

```
DEV_MODE=false
API_BASE_URL=https://api.ciotx.com        # Your actual domain
DASHBOARD_URL=https://ciotx.com           # Your actual domain
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 32)  # Generate this
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
DEEPSEEK_API_KEY=your_deepseek_api_key
```

---

## 6. Build & Start

### 6.1 Build Images

```bash
docker compose build
```

This builds three images: `ciotx-api`, `ciotx-worker`, and `ciotx-dashboard`.

### 6.2 Start All Services

```bash
docker compose up -d
```

The `-d` flag runs containers in the background (detached mode).

### 6.3 Check All Containers Are Running

```bash
docker compose ps
```

Expected output — all five services with Status "Up" and "healthy":

```
NAME               STATUS
ciotx-db           Up (healthy)
ciotx-redis        Up (healthy)
ciotx-api          Up
ciotx-worker       Up
ciotx-dashboard    Up
```

### 6.4 View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f worker
```

Press Ctrl+C to stop following logs.

### 6.5 Verify Health

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","version":"0.1.0","dev_mode":false}`

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

Expected: `200`

---

## 7. SSL & Reverse Proxy (nginx)

### 7.1 Install nginx

```bash
apt install -y nginx certbot python3-certbot-nginx
```

### 7.2 Create nginx Config

```bash
nano /etc/nginx/sites-available/ciotx
```

```nginx
server {
    listen 80;
    server_name ciotx.com www.ciotx.com;

    # Dashboard
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

server {
    listen 80;
    server_name api.ciotx.com;

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

### 7.3 Enable Site

```bash
ln -s /etc/nginx/sites-available/ciotx /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 7.4 SSL Certificates (Let's Encrypt)

```bash
certbot --nginx -d ciotx.com -d www.ciotx.com -d api.ciotx.com
```

Follow the prompts. Certbot automatically modifies the nginx config to use SSL and sets up auto-renewal.

### 7.5 Verify Auto-Renewal

```bash
certbot renew --dry-run
```

Certbot renews certificates automatically via a systemd timer. No manual intervention needed.

---

## 8. Database Migrations

Migrations run automatically at startup (`init_db()` calls `alembic upgrade head`). If you need to run them manually:

```bash
docker compose exec api alembic upgrade head
```

To create a new migration after model changes:

```bash
docker compose exec api alembic revision --autogenerate -m "description"
docker compose exec api alembic upgrade head
```

---

## 9. Restarting Services

```bash
# Restart everything
docker compose restart

# Restart a specific service
docker compose restart api
docker compose restart worker

# Full rebuild after code changes
docker compose down
docker compose up -d --build
```

---

## 10. Updating the Application

```bash
cd /opt/ciotx
git pull origin main
docker compose down
docker compose up -d --build
docker compose logs -f  # Watch for errors for 5 minutes
```

### If something breaks — Rollback:

```bash
git checkout <LAST_KNOWN_GOOD_TAG>   # e.g., v0.3.0
docker compose down
docker compose up -d --build
```

---

## 11. Backups

### 11.1 Database Backup

```bash
# Create backup
docker compose exec postgres pg_dump -U ciotx ciotx > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_*.sql
```

### 11.2 Automated Daily Backup (cron)

```bash
crontab -e
```

Add:

```
0 2 * * * docker compose -f /opt/ciotx/docker-compose.yml exec -T postgres pg_dump -U ciotx ciotx | gzip > /opt/backups/ciotx_$(date +\%Y\%m\%d).sql.gz
```

### 11.3 Restore from Backup

```bash
gunzip backup_20260713.sql.gz
docker compose exec -T postgres psql -U ciotx ciotx < backup_20260713.sql
docker compose restart
```

### 11.4 Verify Backups

Test restoration monthly. A backup you haven't tested is not a backup.

---

## 12. Monitoring

### 12.1 Check Container Health

```bash
docker compose ps
```

### 12.2 Resource Usage

```bash
docker stats
```

### 12.3 Disk Space

```bash
df -h
docker system df
```

### 12.4 Clean Up Old Docker Data

```bash
docker system prune -a --volumes
```

Only run this when you need to free space. It removes unused containers, images, networks, and volumes.

---

## 13. Troubleshooting

### 13.1 Container won't start

```bash
docker compose logs <service_name>
docker compose ps  # Check for "Restarting" status
```

### 13.2 Database connection errors

```bash
# Check if postgres is running
docker compose ps postgres

# Check postgres logs
docker compose logs postgres

# Verify .env DATABASE_URL
grep DATABASE_URL .env
```

### 13.3 API returns 500 errors

```bash
docker compose logs api --tail=50
```

### 13.4 Dashboard shows "Network Error"

The dashboard can't reach the API. Check that `NEXT_PUBLIC_API_URL` in `.env` points to the correct API URL (use the public URL, not localhost/127.0.0.1).

### 13.5 Redis connection errors

```bash
# Redis health check
docker compose exec redis redis-cli -a $REDIS_PASSWORD ping
# Expected: PONG
```

### 13.6 Scans never complete

Check the worker:

```bash
docker compose logs worker --tail=50
```

Common causes: no LLM API key configured, or LLM provider unreachable.

### 13.7 SSL certificate expired

```bash
certbot renew --force-renewal
systemctl reload nginx
```

---

## 14. Security Checklist (Production)

```
☐ .env not committed to git (verify: git ls-files | grep .env returns nothing)
☐ SECRET_KEY is 64+ character random string (not "change-me-in-production")
☐ DEV_MODE=false
☐ All passwords are 32+ character random strings
☐ SSH: root login disabled, password auth disabled
☐ Firewall: ufw enabled, only ports 22/80/443 open
☐ fail2ban installed and configured for SSH
☐ SSL certificates active (https:// works)
☐ HSTS header present (curl -I https://ciotx.com)
☐ Database not exposed to internet (docker compose ps shows no 5432 on 0.0.0.0)
☐ Redis not exposed to internet
☐ Backups configured and tested (restore verified)
☐ Docker runs as non-root user
☐ GitHub webhook secret is set (not empty in production)
☐ Razorpay webhook secret is set (not empty in production)
```

---

## 15. Quick Reference

| Task | Command |
|---|---|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Restart | `docker compose restart` |
| Rebuild | `docker compose up -d --build` |
| Logs | `docker compose logs -f` |
| Status | `docker compose ps` |
| Update | `git pull && docker compose up -d --build` |
| Rollback | `git checkout <tag> && docker compose up -d --build` |
| Backup DB | `docker compose exec postgres pg_dump -U ciotx ciotx \| gzip > backup.sql.gz` |
| Restore DB | `gunzip -c backup.sql.gz \| docker compose exec -T postgres psql -U ciotx ciotx` |
