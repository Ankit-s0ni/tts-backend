# TTS Backend - Production Deployment Guide

This guide covers deploying the TTS Backend on a fresh Ubuntu 22.04/24.04 server using modern best practices.

## Prerequisites

- Fresh Ubuntu 22.04 LTS or 24.04 LTS server
- Root or sudo access
- Domain name pointing to your server (for SSL)
- AWS credentials (Access Key, Secret Key)
- S3 bucket and DynamoDB tables created

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
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your_s3_bucket_name

# DynamoDB Tables
DYNAMODB_TABLE_USERS=users
DYNAMODB_TABLE_NAME=jobs

# Redis
REDIS_URL=redis://redis:6379/0

# Application
DATABASE_URL=sqlite:///./production.db
PIPER_URL=http://piper-service:5000/

# Production Settings
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=your-domain.com,localhost
CORS_ORIGINS=https://your-frontend-domain.com
EOF
```

### Create Production Docker Compose
```bash
tee /root/voicetexta-backend/docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - tts_network

  backend:
    build: .
    restart: unless-stopped
    ports:
      - "127.0.0.1:8002:8000"
    volumes:
      - ./piper_models:/app/piper_models:ro
      - app_data:/app/data
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.prod
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - tts_network

  worker:
    build: .
    restart: unless-stopped
    command: celery -A celery_worker.celery_app worker --loglevel=info -Q celery,default,parler_gpu_queue --concurrency=2
    volumes:
      - ./piper_models:/app/piper_models:ro
      - app_data:/app/data
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.prod
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - tts_network

  piper-service:
    build: .
    restart: unless-stopped
    command: python -m app.workers.piper_worker
    ports:
      - "127.0.0.1:5000:5000"
    volumes:
      - ./piper_models:/app/piper_models:ro
    environment:
      - ENVIRONMENT=production
    networks:
      - tts_network

volumes:
  redis_data:
  app_data:

networks:
  tts_network:
    driver: bridge
EOF
```

## 5. Configure Nginx Reverse Proxy

```bash
sudo tee /etc/nginx/sites-available/tts-backend << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

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
sudo ln -sf /etc/nginx/sites-available/tts-backend /etc/nginx/sites-enabled/
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
sudo certbot --nginx -d your-domain.com

# Auto-renewal is enabled by default with snap
sudo certbot renew --dry-run
```

## 7. Create Systemd Service

```bash
sudo tee /etc/systemd/system/tts-backend.service << 'EOF'
[Unit]
Description=TTS Backend Application
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
sudo systemctl enable tts-backend.service
```

## 8. Setup Logging with Rsyslog

```bash
# Create log directory
sudo mkdir -p /var/log/tts-backend
sudo chown syslog:adm /var/log/tts-backend

# Configure rsyslog
sudo tee /etc/rsyslog.d/30-tts-backend.conf << 'EOF'
# TTS Backend logging
:programname,isequal,"tts-backend" /var/log/tts-backend/app.log
& stop
EOF

# Logrotate configuration
sudo tee /etc/logrotate.d/tts-backend << 'EOF'
/var/log/tts-backend/*.log {
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
systemctl start tts-backend
```

### Check Status
```bash
# Service status
systemctl status tts-backend

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
systemctl restart tts-backend
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
    systemctl restart tts-backend
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
journalctl -u tts-backend.service -f

# Restart application
systemctl restart tts-backend

# Update application
cd /root/voicetexta-backend && git pull && systemctl restart tts-backend

# Check container status
docker compose -f docker-compose.prod.yml ps

# Access Redis CLI
docker compose -f docker-compose.prod.yml exec redis redis-cli
```

### Troubleshooting
- **Service won't start**: Check `journalctl -u tts-backend.service`
- **502 Bad Gateway**: Check if backend container is running
- **SSL issues**: Run `certbot renew`
- **High memory usage**: Check worker concurrency in docker-compose.prod.yml

## Security Notes

1. **Environment Variables**: Never commit `.env.prod` to version control
2. **AWS Credentials**: Use IAM roles when possible instead of access keys
3. **Regular Updates**: Keep Docker, Nginx, and Ubuntu updated
4. **Monitoring**: Set up proper monitoring and alerting
5. **Backups**: Test backup restoration regularly

This deployment setup provides a production-ready environment with security, monitoring, and maintenance considerations built-in.