# Zenglow — Deployment Guide

## Target Environment

Zenglow is designed for **on-premises Linux deployment** using Docker Compose. It has no hard dependency on AWS or Azure, though it can run on any cloud provider's VMs.

**Minimum server requirements:**

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 40 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

---

## Prerequisites on Server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose plugin
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify
docker --version
docker compose version
```

---

## Initial Server Setup

```bash
# Create deployment directory
sudo mkdir -p /opt/zenglow
sudo chown $USER:$USER /opt/zenglow
cd /opt/zenglow

# Clone the repository
git clone https://github.com/your-org/zenglow.git .

# Copy and configure environment
cp .env.example .env
nano .env   # fill in all production values
```

### Critical `.env` values to change for production

```bash
# Generate a strong random secret
python3 -c "import secrets; print(secrets.token_hex(64))"

JWT_SECRET_KEY=<64-char-random-hex>
SECRET_KEY=<64-char-random-hex>

DATABASE_URL=postgresql://zenglow:<strong-password>@postgres:5432/zenglow_db
ENVIRONMENT=production
DEBUG=false

# Set your actual domains
ALLOWED_ORIGINS=https://app.yourdomain.com,https://business.yourdomain.com,https://admin.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

---

## First Deployment

```bash
cd /opt/zenglow

# Pull images / build
docker compose pull
# or build from source:
docker compose build

# Start infrastructure first
docker compose up -d postgres redis

# Wait for postgres to be healthy
docker compose ps

# Run migrations
docker compose run --rm backend alembic upgrade head

# Seed initial data (optional but recommended for first setup)
docker compose run --rm backend python scripts/seed.py

# Start all services
docker compose up -d

# Check all services are healthy
docker compose ps
docker compose logs --tail=50 backend
```

---

## Subsequent Deployments (CI/CD)

The `deploy.yml` GitHub Actions workflow handles this automatically on push to `main`. Manually:

```bash
cd /opt/zenglow

# Pull latest images (pushed by CI)
docker compose pull

# Run any new migrations
docker compose run --rm backend alembic upgrade head

# Rolling restart
docker compose up -d --remove-orphans

# Verify
docker compose ps
curl http://localhost:8000/health
```

---

## Nginx Reverse Proxy (Recommended)

Install Nginx and configure virtual hosts to expose all services on standard ports:

```bash
sudo apt-get install nginx certbot python3-certbot-nginx
```

Example `/etc/nginx/sites-available/zenglow`:

```nginx
# API Backend
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }
}

# Customer Web
server {
    listen 80;
    server_name app.yourdomain.com;
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Business Web
server {
    listen 80;
    server_name business.yourdomain.com;
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Admin Web
server {
    listen 80;
    server_name admin.yourdomain.com;
    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/zenglow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL with Let's Encrypt
sudo certbot --nginx -d api.yourdomain.com -d app.yourdomain.com \
  -d business.yourdomain.com -d admin.yourdomain.com
```

---

## Database Backups

```bash
# Manual backup
docker compose exec postgres pg_dump -U zenglow zenglow_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
docker compose exec -T postgres psql -U zenglow zenglow_db < backup.sql

# Automated backup (add to crontab)
0 2 * * * cd /opt/zenglow && docker compose exec -T postgres \
  pg_dump -U zenglow zenglow_db | gzip > /backups/zenglow_$(date +\%Y\%m\%d).sql.gz
```

---

## Environment Variable Reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `SECRET_KEY` | Yes | App secret key |
| `ENVIRONMENT` | Yes | `production` / `development` / `test` |
| `ALLOWED_ORIGINS` | Yes | Comma-separated CORS origins |
| `RAZORPAY_KEY_ID` | For payments | Razorpay public key |
| `RAZORPAY_KEY_SECRET` | For payments | Razorpay secret key |
| `RAZORPAY_WEBHOOK_SECRET` | For webhooks | Razorpay webhook signature secret |
| `SMTP_HOST` | For email | SMTP server hostname |
| `SMTP_USER` | For email | SMTP username |
| `SMTP_PASSWORD` | For email | SMTP password |
| `SENTRY_DSN` | Optional | Sentry error tracking DSN |
| `S3_ENDPOINT_URL` | For storage | S3-compatible storage endpoint |
| `S3_ACCESS_KEY_ID` | For storage | Storage access key |
| `S3_SECRET_ACCESS_KEY` | For storage | Storage secret key |

---

## Monitoring

### Check service health
```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### View logs
```bash
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs --tail=100 postgres
```

### Celery monitoring
```bash
# Start with monitoring profile
docker compose --profile monitoring up -d flower
# Visit http://your-server:5555
```

### Resource usage
```bash
docker stats
docker compose ps
```

---

## Scaling

To run multiple backend workers on a single server:

```yaml
# In docker-compose.yml, change backend service:
deploy:
  replicas: 2
```

For horizontal scaling across multiple servers, use:
- An external PostgreSQL cluster (e.g. Patroni)
- An external Redis cluster
- A load balancer (HAProxy or Nginx upstream)
- Shared S3-compatible object storage (MinIO)

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Backend won't start | `docker compose logs backend` — check DB connection |
| Migrations fail | Ensure DB is healthy: `docker compose ps postgres` |
| Redis connection refused | `docker compose ps redis` — check port 6379 |
| 401 on all requests | Verify `JWT_SECRET_KEY` matches across restarts |
| Emails not sending | Set `EMAIL_PROVIDER=console` to log to stdout in dev |
| Bookings not confirming | Check `PAYMENT_PROVIDER=mock` in dev, verify webhook signing in prod |
