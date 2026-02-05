# 🚀 QuantEdge Deployment Guide

Complete guide to deploy your trading bot on Ubuntu server with PM2 and access the dashboard.

## 📋 Prerequisites

- Ubuntu Server (18.04+)
- Python 3.8+
- Node.js & PM2
- Domain/IP address (optional, for remote access)

---

## 🔧 Server Setup

### 1. **Update System**

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. **Install Python & Dependencies**

```bash
sudo apt install python3 python3-pip python3-venv -y
```

### 3. **Install Node.js & PM2**

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2
sudo npm install -g pm2
```

---

## 📦 Project Setup

### 1. **Clone/Upload Your Project**

```bash
# Create project directory
mkdir -p ~/quantedge
cd ~/quantedge

# Upload your files here
# - trading_engine.py
# - backtester.py
# - paper_trader_api.py
# - requirements.txt
# - ecosystem.config.js
# - static/dashboard.html
```

### 2. **Create Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. **Install Python Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. **Create Directories**

```bash
mkdir -p logs static
```

### 5. **Test Single Bot**

```bash
# Test if bot runs (Ctrl+C to stop)
python paper_trader_api.py BTCUSDT 15m 5000
```

---

## 🚀 Deploy with PM2

### 1. **Start Bots**

```bash
# Start all configured bots (BTC, ETH, SOL)
pm2 start ecosystem.config.js

# Or start individually
pm2 start paper_trader_api.py --name quantedge-btc --interpreter python3 -- BTCUSDT 15m 5000
```

### 2. **Check Status**

```bash
pm2 status
pm2 logs quantedge-btc
```

### 3. **Save Configuration**

```bash
# Save PM2 process list
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Run the command it outputs
```

### 4. **Manage Processes**

```bash
# Stop bot
pm2 stop quantedge-btc

# Restart bot
pm2 restart quantedge-btc

# Delete bot
pm2 delete quantedge-btc

# Monitor in real-time
pm2 monit
```

---

## 🌐 Access Dashboard

### **Local Access (Same Machine)**

```
http://localhost:5000
```

### **Remote Access (From Another Computer)**

#### Option 1: Direct IP (Development)

```
http://YOUR_SERVER_IP:5000
```

#### Option 2: SSH Tunnel (Secure)

```bash
# On your local machine
ssh -L 5000:localhost:5000 user@YOUR_SERVER_IP

# Then access
http://localhost:5000
```

#### Option 3: Nginx Reverse Proxy (Production)

**Install Nginx:**

```bash
sudo apt install nginx -y
```

**Create Config:**

```bash
sudo nano /etc/nginx/sites-available/quantedge
```

**Add:**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or your IP

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable:**

```bash
sudo ln -s /etc/nginx/sites-available/quantedge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Access:**

```
http://your-domain.com
```

---

## 🔐 Firewall Setup

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP (if using Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow bot ports (if direct access)
sudo ufw allow 5000:5010/tcp

# Enable firewall
sudo ufw enable
```

---

## 📊 Multiple Bots

### **Run Multiple Trading Pairs**

Edit `ecosystem.config.js`:

```javascript
{
  name: 'quantedge-bnb',
  script: 'paper_trader_api.py',
  args: 'BNBUSDT 15m 5003',
  // ...
}
```

Then:

```bash
pm2 reload ecosystem.config.js
```

**Access dashboards:**

- BTC: `http://server:5000`
- ETH: `http://server:5001`
- SOL: `http://server:5002`
- BNB: `http://server:5003`

---

## 🔍 Monitoring & Logs

### **View Logs**

```bash
# Real-time logs
pm2 logs quantedge-btc

# Last 100 lines
pm2 logs quantedge-btc --lines 100

# Error logs only
pm2 logs quantedge-btc --err

# All bots
pm2 logs
```

### **Performance Monitoring**

```bash
# CPU/Memory usage
pm2 monit

# Detailed info
pm2 show quantedge-btc
```

### **Database**

```bash
# Check database size
ls -lh trading_data.db

# Backup database
cp trading_data.db trading_data_backup_$(date +%Y%m%d).db
```

---

## 🛠️ Troubleshooting

### **Bot Won't Start**

```bash
# Check Python version
python3 --version

# Test manually
source venv/bin/activate
python paper_trader_api.py BTCUSDT

# Check logs
pm2 logs quantedge-btc --err
```

### **Can't Access Dashboard**

```bash
# Check if bot is running
pm2 status

# Check port
sudo netstat -tulpn | grep 5000

# Check firewall
sudo ufw status

# Test locally first
curl http://localhost:5000/api/status
```

### **Database Locked**

```bash
# Stop all bots
pm2 stop all

# Remove lock
rm trading_data.db-journal

# Restart
pm2 restart all
```

---

## 📈 Performance Optimization

### **1. Increase Update Frequency**

In `paper_trader_api.py`, change:

```python
bot.start(update_interval=30)  # Update every 30s instead of 60s
```

### **2. Reduce Memory Usage**

```bash
# Limit equity curve history
# In paper_trader_api.py, modify SQL:
# SELECT * FROM equity_curve ORDER BY id DESC LIMIT 500
```

### **3. Log Rotation**

```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

---

## 🔄 Updates & Maintenance

### **Update Strategy**

```bash
# Stop bots
pm2 stop all

# Update code
git pull  # or upload new files

# Restart
pm2 restart all
```

### **Backup**

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
cp trading_data.db backups/trading_data_$DATE.db
cp trading_state.json backups/trading_state_$DATE.json
echo "Backup created: backups/trading_data_$DATE.db"
EOF

chmod +x backup.sh
./backup.sh
```

### **Scheduled Backups**

```bash
# Add to crontab
crontab -e

# Add this line (backup daily at 2 AM)
0 2 * * * /home/user/quantedge/backup.sh
```

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Start bot
pm2 start ecosystem.config.js

# View all bots
pm2 list

# Logs
pm2 logs

# Stop all
pm2 stop all

# Restart all
pm2 restart all

# Delete all
pm2 delete all

# Monitor
pm2 monit

# Save config
pm2 save
```

---

## 📱 Mobile Access

Access dashboard from phone:

```
http://YOUR_SERVER_IP:5000
```

The dashboard is fully responsive!

---

## 🆘 Support

If you encounter issues:

1. Check PM2 logs: `pm2 logs`
2. Test manually: `python paper_trader_api.py BTCUSDT`
3. Check firewall: `sudo ufw status`
4. Verify ports: `sudo netstat -tulpn | grep 5000`

---

## ✅ Final Checklist

- [ ] Python dependencies installed
- [ ] PM2 installed and configured
- [ ] Bots running (`pm2 status`)
- [ ] Dashboard accessible
- [ ] PM2 startup enabled
- [ ] Firewall configured
- [ ] Backups scheduled (optional)

---

🎉 **You're all set! Access your dashboard and watch your bot trade!**
