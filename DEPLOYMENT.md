# TTS Backend - Production Deployment Guide

This guide covers deploying the TTS Backend on a fresh Ubuntu 22.04/24.04 server using modern best practices.

## Prerequisites

- Fresh Ubuntu 22.04 LTS or 24.04 LTS server
- Root or sudo access
- Domain name pointing to your server (api.voicetexta.com)
- Cloudinary account credentials
- Resend API key for email services

## 1. Initial Server Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

### Create Application User
```bash
sudo adduser --system --group --shell /bin/bash ttsapp
sudo usermod -aG docker ttsapp
```

### Setup Firewall (UFW)
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 2. Install Docker & Docker Compose

### Install Docker (Official Method)
```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### Verify Installation
```bash
sudo docker --version
sudo docker compose version
```

## 3. Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 4. Setup Application

### Clone Repository
```bash
cd /root
git clone <your-repo-url> voicetexta-backend
cd voicetexta-backend
```

### Setup Piper Models Directory
```bash
mkdir -p /root/voicetexta-backend/piper_models
cd /root/voicetexta-backend/piper_models

# If you have model archives, extract them:
# unzip -o /root/Archive.zip -d /root/voicetexta-backend/piper_models/
# unzip -o "/root/Archive 2.zip" -d /root/voicetexta-backend/piper_models/
```

### Create Production Environment File
```bash
tee /root/voicetexta-backend/.env.prod << 'EOF'
# Production environment variables for the TTS app

# --- JWT Authentication (for email-based auth) ---------------------------
JWT_SECRET_KEY=prod_secure_jwt_key_a8f5c7d9e2b1f4a6c9e8d7b3f1a9c5e7d2b8f6a4c9e7d5b3f1a8c6e9d7b5f3a1c

# --- Email Service (Resend) ----------------------------------------------
RESEND_API_KEY=re_XGd6FAcM_Jf6KEsmt7Qf7pgE76zy2zknF

# --- File Storage (Cloudinary) -------------------------------------------
CLOUDINARY_CLOUD_NAME=voicetexta
CLOUDINARY_API_KEY=536972572585976
CLOUDINARY_API_SECRET=gb_T8dzCEXoZhY8KPVm1plxFLdA

# --- Production Settings -------------------------------------------------
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# --- Database / storage / services ----------------------------------------
DATABASE_URL=sqlite:///./data/production.db
PIPER_URL=http://piper:5000/
REDIS_URL=redis://redis:6379/0

# --- Performance Settings ------------------------------------------------
MAX_CACHED_VOICES=10
WORKER_CONCURRENCY=2
CELERY_MAX_TASKS_PER_CHILD=1000

# --- Security Settings ---------------------------------------------------
ALLOWED_HOSTS=api.voicetexta.com,localhost,127.0.0.1
CORS_ORIGINS=https://voicetexta.com,https://www.voicetexta.com,https://app.voicetexta.com
SECURE_SSL_REDIRECT=true
EOF
```

### Use Existing Production Docker Compose
The production docker-compose.prod.yml file is already created in your repository with the following key features:
- Redis with persistence and health checks
- Backend API with resource limits
- Celery worker with optimized concurrency
- Piper TTS service
- Named volumes for data persistence
- Custom network configuration
- Comprehensive health checks
```

## 5. Configure Nginx Reverse Proxy

First, add rate limiting configuration to the main nginx config inside the http block:

```bash
# Backup the original nginx.conf
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Add rate limiting configuration manually
sudo tee /tmp/rate_limit.conf << 'EOF'
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
EOF

# Insert the rate limiting config after the http { line
sudo awk '
/^[[:space:]]*http[[:space:]]*{/ { print; getline < "/tmp/rate_limit.conf"; print; next }
{ print }
' /etc/nginx/nginx.conf.backup > /tmp/nginx.conf.new

sudo mv /tmp/nginx.conf.new /etc/nginx/nginx.conf
sudo rm /tmp/rate_limit.conf
```

Then create the site configuration:

```bash
sudo tee /etc/nginx/sites-available/voicetexta-api << 'EOF'
server {
    listen 80;
    server_name api.voicetexta.com;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Large file uploads for audio
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8002/;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/voicetexta-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 6. SSL Certificate with Certbot

```bash
# Install Certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Get SSL certificate
sudo certbot --nginx -d api.voicetexta.com

# Auto-renewal is enabled by default with snap
sudo certbot renew --dry-run
```

## 7. Create Systemd Service

```bash
sudo tee /etc/systemd/system/voicetexta-backend.service << 'EOF'
[Unit]
Description=VoiceTexta TTS Backend Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/voicetexta-backend
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.prod.yml restart
TimeoutStartSec=300
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable voicetexta-backend.service
```

## 8. Setup Logging with Rsyslog

```bash
# Create log directory
sudo mkdir -p /var/log/voicetexta-backend
sudo chown syslog:adm /var/log/voicetexta-backend

# Configure rsyslog
sudo tee /etc/rsyslog.d/30-voicetexta-backend.conf << 'EOF'
# VoiceTexta Backend logging
:programname,isequal,"voicetexta-backend" /var/log/voicetexta-backend/app.log
& stop
EOF

# Logrotate configuration
sudo tee /etc/logrotate.d/voicetexta-backend << 'EOF'
/var/log/voicetexta-backend/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 syslog adm
    postrotate
        systemctl reload rsyslog
    endscript
}
EOF

sudo systemctl restart rsyslog
```

## 9. Monitoring Setup

### Install Node Exporter (for Prometheus monitoring)
```bash
sudo useradd --no-create-home --shell /bin/false node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvf node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter

sudo tee /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

## 10. Security Hardening

### Fail2ban Setup
```bash
sudo apt install -y fail2ban

sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Update Nginx Configuration for Additional Security
```bash
sudo tee -a /etc/nginx/nginx.conf << 'EOF'
# Hide Nginx version
server_tokens off;

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
EOF
```

## 11. Deployment Commands

### Initial Deployment
```bash
cd /root/voicetexta-backend

# Update environment file with actual values
nano .env.prod

# Build and start services
docker compose -f docker-compose.prod.yml build
systemctl start voicetexta-backend
```

**If service fails to start, debug with these commands:**

```bash
# Check detailed service logs
journalctl -xeu voicetexta-backend.service

# Try running Docker Compose manually for better error visibility
cd /root/voicetexta-backend
docker compose -f docker-compose.prod.yml up

# Check individual container logs
docker compose -f docker-compose.prod.yml logs backend-api
docker compose -f docker-compose.prod.yml logs redis
docker compose -f docker-compose.prod.yml logs worker
docker compose -f docker-compose.prod.yml logs piper

# Check if containers are running
docker compose -f docker-compose.prod.yml ps

# Common issues to check:
# 1. Port conflicts
netstat -tlnp | grep -E ':(8002|5000|6379)'

# 2. Environment file
cat .env.prod

# 3. Piper models directory
ls -la piper_models/

# 4. Docker logs for specific error
docker logs voicetexta-backend-backend-api-1
```

**Common Fixes for Issues:**

```bash
# Fix 1: Health check endpoint issue (backend returns 404 on /)
# Edit docker-compose.prod.yml to fix health check endpoint
sed -i 's|http://localhost:8000/|http://localhost:8000/health|g' docker-compose.prod.yml

# Fix 2: Piper worker module not found
# Remove or comment out the piper service if the module doesn't exist
# OR change the command to a simple server
sed -i 's|command: python -m app.workers.piper_worker|command: python -m http.server 5000|g' docker-compose.prod.yml

# Fix 3: Remove version warning
sed -i '/version:/d' docker-compose.prod.yml

# After making these changes, restart:
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

**Quick temporary fix to get it running:**

```bash
# Stop current containers
docker compose -f docker-compose.prod.yml down

# Run without the problematic piper service
docker compose -f docker-compose.prod.yml up -d redis backend-api worker

# Check if it works
curl http://localhost:8002/
```

**If you get YAML syntax errors:**

```bash
# Check YAML syntax around the error line
sed -n '85,95p' docker-compose.prod.yml

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('docker-compose.prod.yml'))"

# Common YAML fixes:
# 1. Check indentation (use spaces, not tabs)
# 2. Check for missing colons or incorrect nesting
# 3. Ensure proper key-value formatting

# Quick fix - recreate the docker-compose.prod.yml file:
cp docker-compose.prod.yml docker-compose.prod.yml.backup

# Use the working version from your repository
git checkout docker-compose.prod.yml

# Or manually fix common issues:
# Remove version line if it exists
sed -i '/^version:/d' docker-compose.prod.yml

# Fix any malformed lines around line 91
# You can edit manually: nano docker-compose.prod.yml
```
```
```
```

### Check Status
```bash
# Service status
systemctl status voicetexta-backend

# Container status
docker compose -f docker-compose.prod.yml ps

# Logs
docker compose -f docker-compose.prod.yml logs -f
```

### Update Deployment
```bash
cd /root/voicetexta-backend
git pull
docker compose -f docker-compose.prod.yml build --no-cache
systemctl restart voicetexta-backend
```

## 12. Backup Strategy

### Database Backup Script
```bash
tee /root/voicetexta-backend/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups/voicetexta-backend"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup application data volume
docker run --rm -v voicetexta-backend_app_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/app_data_$DATE.tar.gz -C /data .

# Backup Redis data
docker run --rm -v voicetexta-backend_redis_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/redis_data_$DATE.tar.gz -C /data .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /root/voicetexta-backend/backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /root/voicetexta-backend/backup.sh" | crontab -
```

## 13. Health Checks and Monitoring

### Create Health Check Script
```bash
tee /root/voicetexta-backend/health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8002/"

if curl -f -s $HEALTH_URL > /dev/null; then
    echo "TTS Backend is healthy"
    exit 0
else
    echo "TTS Backend is unhealthy"
    # Restart service
    systemctl restart voicetexta-backend
    exit 1
fi
EOF

chmod +x /root/voicetexta-backend/health_check.sh

# Add to crontab for every 5 minutes
echo "*/5 * * * * /root/voicetexta-backend/health_check.sh" | crontab -
```

## Quick Reference

### Useful Commands
```bash
# Check logs
journalctl -u voicetexta-backend.service -f

# Restart application
systemctl restart voicetexta-backend

# Update application
cd /root/voicetexta-backend && git pull && systemctl restart voicetexta-backend

# Check container status
docker compose -f docker-compose.prod.yml ps

# Access Redis CLI
docker compose -f docker-compose.prod.yml exec redis redis-cli
```

### Troubleshooting
- **Service won't start**: Check `journalctl -u voicetexta-backend.service`
- **502 Bad Gateway**: Check if backend container is running
- **SSL issues**: Run `certbot renew`
- **High memory usage**: Check worker concurrency in docker-compose.prod.yml
- **Domain not resolving**: Ensure DNS A record points to your server IP
- **CORS errors**: Check CORS_ORIGINS in .env.prod

## Security Notes

1. **Environment Variables**: Never commit `.env.prod` to version control
2. **Cloudinary Credentials**: Keep API secrets secure and rotate periodically
3. **Regular Updates**: Keep Docker, Nginx, and Ubuntu updated
4. **Monitoring**: Set up proper monitoring and alerting
5. **Backups**: Test backup restoration regularly
6. **SSL/TLS**: Ensure HTTPS is properly configured and auto-renewing

This deployment setup provides a production-ready environment with security, monitoring, and maintenance considerations built-in.