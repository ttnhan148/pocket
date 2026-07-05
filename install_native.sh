#!/bin/bash

# --- Pocket 1-Click Native Deployment Script for Linux (No Docker) ---
# Deploy Path: /var/www/pocket
# Deploy Port: 14080

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}    Pocket 1-Click Native Installer & Deployer     ${NC}"
echo -e "${BLUE}===================================================${NC}"

DEPLOY_DIR="/var/www/pocket"
CURRENT_DIR=$(pwd)

# 1. Install System Dependencies
echo -e "\n${BLUE}[1/6] Installing system dependencies (Requires sudo)...${NC}"
if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv sqlite3 curl git
elif [ -x "$(command -v yum)" ]; then
    sudo yum install -y python3 python3-pip sqlite3 curl git
else
    echo -e "${YELLOW}Warning: Unknown package manager. Please ensure Python3, venv, and sqlite3 are installed.${NC}"
fi
echo -e "${GREEN}✓ System dependencies resolved.${NC}"

# 2. Install Bun (Next.js bundler)
echo -e "\n${BLUE}[2/6] Setting up Bun environment...${NC}"
if ! [ -x "$(command -v bun)" ]; then
    echo -e "Installing Bun..."
    curl -fsSL https://bun.sh/install | bash
    # Source bun environment for current script execution
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
else
    echo -e "${GREEN}✓ Bun is already installed.${NC}"
fi

# 3. Setup Directories & Copy Code
echo -e "\n${BLUE}[3/6] Setting up target folder at $DEPLOY_DIR...${NC}"
sudo mkdir -p "$DEPLOY_DIR"
sudo chown -R $USER:$USER "$DEPLOY_DIR"

echo -e "Copying code to $DEPLOY_DIR..."
cp -r backend "$DEPLOY_DIR/"
cp -r frontend "$DEPLOY_DIR/"
cp build_single_deploy.py "$DEPLOY_DIR/"

# 4. Build and Bundle Frontend Next.js
echo -e "\n${BLUE}[4/6] Installing dependencies and building static frontend...${NC}"
cd "$DEPLOY_DIR/frontend"
bun install
bun run build

# Copy build files to backend static serving folder
echo -e "Copying static assets to backend serving directory..."
mkdir -p "$DEPLOY_DIR/backend/app/static"
rm -rf "$DEPLOY_DIR/backend/app/static/*"
cp -r out/* "$DEPLOY_DIR/backend/app/static/"
echo -e "${GREEN}✓ Frontend compilation and binding completed.${NC}"

# 5. Setup Python Virtual Environment
echo -e "\n${BLUE}[5/6] Setting up Python virtual environment and installing backend...${NC}"
cd "$DEPLOY_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install uvicorn python-multipart
deactivate
echo -e "${GREEN}✓ Python packages installed successfully.${NC}"

# 6. Configure Systemd Service for Auto-start
echo -e "\n${BLUE}[6/6] Creating systemd service file...${NC}"
SERVICE_FILE="/etc/systemd/system/pocket.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Pocket Personal Context Engineering Platform
After=network.target

[Service]
User=$USER
WorkingDirectory=$DEPLOY_DIR/backend
ExecStart=$DEPLOY_DIR/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 14080
Restart=always
RestartSec=5
Environment=DATABASE_URL=sqlite+aiosqlite:////$DEPLOY_DIR/backend/pocket.db
Environment=ENV_MODE=production

[Install]
WantedBy=multi-user.target
EOF

echo -e "Reloading systemd, starting and enabling pocket service..."
sudo systemctl daemon-reload
sudo systemctl start pocket
sudo systemctl enable pocket

# Final completion report
IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDR" ]; then
    IP_ADDR="localhost"
fi

echo -e "\n${GREEN}===================================================${NC}"
echo -e "${GREEN}    NATIVE DEPLOYMENT COMPLETED SUCCESSFULLY!      ${NC}"
echo -e "${GREEN}===================================================${NC}"
echo -e "📍 App URL:      ${YELLOW}http://$IP_ADDR:14080${NC}"
echo -e "📂 Storage Path:  ${YELLOW}$DEPLOY_DIR/backend/pocket.db${NC}"
echo -e "⚙️ Systemd Service: ${YELLOW}pocket.service${NC}"
echo -e "\nUseful Commands:"
echo -e "  - View Logs:    ${BLUE}sudo journalctl -u pocket -f${NC}"
echo -e "  - Stop App:     ${BLUE}sudo systemctl stop pocket${NC}"
echo -e "  - Start App:    ${BLUE}sudo systemctl start pocket${NC}"
echo -e "==================================================="
