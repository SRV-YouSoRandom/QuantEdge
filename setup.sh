#!/bin/bash

echo "=================================="
echo "🚀 QuantEdge Setup Script"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}❌ Please don't run as root${NC}"
   exit 1
fi

# Check Python
echo -e "\n${YELLOW}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Installing...${NC}"
    sudo apt update
    sudo apt install python3 python3-pip python3-venv -y
fi
echo -e "${GREEN}✓ Python3 found${NC}"

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check PM2
echo -e "\n${YELLOW}Checking PM2...${NC}"
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}❌ PM2 not found. Installing...${NC}"
    sudo npm install -g pm2
fi
echo -e "${GREEN}✓ PM2 found${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate and install dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p logs static
echo -e "${GREEN}✓ Directories created${NC}"

# Test import
echo -e "\n${YELLOW}Testing installation...${NC}"
python3 -c "import ccxt, pandas, flask; print('All imports OK')" && echo -e "${GREEN}✓ Installation test passed${NC}" || echo -e "${RED}❌ Import test failed${NC}"

echo -e "\n${GREEN}=================================="
echo "✅ Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Test single bot:  python paper_trader_api.py BTCUSDT 15m 5000"
echo "2. Start with PM2:   pm2 start ecosystem.config.js"
echo "3. View dashboard:   http://localhost:5000"
echo "4. Check logs:       pm2 logs"
echo ""
echo "Read DEPLOYMENT.md for full guide!"