# CIOTX — Deployment Guide

## Requirements

- Ubuntu 24.04 server (2 vCPU, 4 GB RAM minimum)
- Domain with DNS access (e.g. `yourdomain.com`)
- Docker + Docker Compose installed on the server
- A DeepSeek / OpenAI / Anthropic API key

---

## 1. Install Docker (if not already installed)

```bash
curl -fsSL https://get.docker.com | sh
```

---

## 2. Get the code on the server

```bash
git clone https://github.com/your-repo/CiotxAI.git /opt/ciotx
cd /opt/ciotx
```

---

## 3. Configure environment

```bash
cp .env.example .env
nano .env
```

The only values you **must** set:

| Variable | What to put |
|----------|-------------|
| `DOMAIN_NAME` | `yourdomain.com` |
| `API_BASE_URL` | `https://api.yourdomain.com` |
| `DASHBOARD_URL` | `https://yourdomain.com` |
| `SECRET_KEY` | Run: `openssl rand -hex 32` |
| `DB_PASSWORD` | Any strong password |
| `REDIS_PASSWORD` | Any strong password |
| `INTERNAL_API_KEY` | Run: `openssl rand -hex 16` |
| `DEEPSEEK_API_KEY` | Your DeepSeek key (or OpenAI/Anthropic) |

Everything else has working defaults.

---

## 4. Point DNS

Add two A records at your DNS provider:

```
A   yourdomain.com       →  <server IP>
A   api.yourdomain.com   →  <server IP>
```

---

## 5. Deploy

```bash
docker compose up -d --build
```

That's it. This starts:
- **postgres** — database
- **redis** — queue
- **api** — FastAPI backend on port 8000
- **worker** — background scan jobs
- **dashboard** — Next.js frontend on port 3000
- **nginx** — reverse proxy on port 80, routes traffic to the above

---

## 6. SSL (HTTPS)

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

Auto-renews via systemd. Done.

---

## 7. GitHub OAuth (optional — for "Connect GitHub" feature)

1. Go to https://github.com/settings/developers → **OAuth Apps** → **New OAuth App**
2. Set:
   - Homepage URL: `https://yourdomain.com`
   - Callback URL: `https://api.yourdomain.com/v1/auth/github/callback`
3. Copy **Client ID** and **Client Secret** into `.env`:
   ```env
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```
4. Restart: `docker compose up -d --build api`

---

## 8. CLI Binaries

Built automatically during `docker compose up -d --build`. Binaries appear in `./bin/`:

```
bin/ciotx-linux-amd64
bin/ciotx-darwin-amd64
bin/ciotx-darwin-arm64
bin/ciotx-windows-amd64.exe
```

Each binary has your `API_BASE_URL` baked in. Distribute to users — they just run:

```bash
ciotx login   # opens browser, done
ciotx scan    # scans current directory
```

---

## 9. Changing domain later

Update three lines in `.env`:

```env
DOMAIN_NAME=newdomain.com
API_BASE_URL=https://api.newdomain.com
DASHBOARD_URL=https://newdomain.com
```

Then rebuild:

```bash
docker compose up -d --build
```

CORS, nginx routing, CLI binary URLs, and Next.js API calls all update automatically.

---

## Daily operations

```bash
# View logs
docker compose logs -f

# Restart everything
docker compose restart

# Update to latest code
git pull && docker compose up -d --build

# Stop everything
docker compose down
```
