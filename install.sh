#!/bin/bash

# --- Pocket 1-Click Deployment Script for Linux ---
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
echo -e "${BLUE}       Pocket 1-Click Installer & Deployer        ${NC}"
echo -e "${BLUE}===================================================${NC}"

# 1. Check prerequisites
echo -e "\n${BLUE}[1/5] Checking prerequisites...${NC}"
if ! [ -x "$(command -v docker)" ]; then
    echo -e "${YELLOW}Warning: Docker is not installed.${NC}"
    echo -e "Attempting to install Docker automatically..."
    if [ -x "$(command -v apt-get)" ]; then
        sudo apt-get update
        sudo apt-get install -y docker.io
    elif [ -x "$(command -v yum)" ]; then
        sudo yum install -y docker
    else
        echo -e "${RED}Error: Cannot auto-install Docker. Please install Docker manually first.${NC}"
        exit 1
    fi
fi

# Start Docker if not running
if ! sudo docker info >/dev/null 2>&1; then
    echo -e "Starting Docker service..."
    sudo systemctl start docker || sudo service docker start
fi
echo -e "${GREEN}✓ Docker is installed and running.${NC}"

# 2. Setup Directories
echo -e "\n${BLUE}[2/5] Setting up deployment directories...${NC}"
DEPLOY_DIR="/var/www/pocket"
DATA_DIR="$DEPLOY_DIR/data"

echo -e "Creating directory $DEPLOY_DIR..."
sudo mkdir -p "$DEPLOY_DIR"
sudo mkdir -p "$DATA_DIR"

# Set permissions so Docker can read/write data volume
sudo chmod -R 775 "$DEPLOY_DIR"
sudo chown -R $USER:$USER "$DEPLOY_DIR" || true
echo -e "${GREEN}✓ Directories created successfully.${NC}"

# 3. Build Monolithic Docker Image
echo -e "\n${BLUE}[3/5] Building monolithic Docker image locally...${NC}"
echo -e "This might take a few minutes (compiling frontend Next.js + setting up Python backend)..."
sudo docker build -t pocket-platform:latest .
echo -e "${GREEN}✓ Docker image built successfully.${NC}"

# 4. Stop existing container if running
echo -e "\n${BLUE}[4/5] Preparing container deployment...${NC}"
CONTAINER_NAME="pocket-app"
if [ "$(sudo docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo -e "Stopping and removing old container: $CONTAINER_NAME..."
    sudo docker stop "$CONTAINER_NAME" || true
    sudo docker rm "$CONTAINER_NAME" || true
fi

# 5. Start Container on Port 14080
echo -e "\n${BLUE}[5/5] Launching Pocket container...${NC}"
sudo docker run -d \
  -p 14080:8000 \
  -v "$DATA_DIR:/app/data" \
  --name "$CONTAINER_NAME" \
  --restart always \
  -e ENV_MODE="production" \
  pocket-platform:latest

echo -e "${GREEN}✓ Pocket is running in the background!${NC}"

# Print completion report
IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDR" ]; then
    IP_ADDR="localhost"
fi

echo -e "\n${GREEN}===================================================${NC}"
echo -e "${GREEN}        DEPLOYMENT COMPLETED SUCCESSFULLY!        ${NC}"
echo -e "${GREEN}===================================================${NC}"
echo -e "📍 App URL:      ${YELLOW}http://$IP_ADDR:14080${NC}"
echo -e "📂 Storage Path:  ${YELLOW}$DATA_DIR${NC} (SQLite database location)"
echo -e "🐳 Docker Name:  ${YELLOW}$CONTAINER_NAME${NC}"
echo -e "\nUseful Commands:"
echo -e "  - View Logs:    ${BLUE}sudo docker logs -f $CONTAINER_NAME${NC}"
echo -e "  - Stop App:     ${BLUE}sudo docker stop $CONTAINER_NAME${NC}"
echo -e "  - Start App:    ${BLUE}sudo docker start $CONTAINER_NAME${NC}"
echo -e "==================================================="
