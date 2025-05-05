#!/bin/bash

# Finance App Docker Test Script
# Tests the Docker setup and verifies app is running correctly

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  Finance App Docker Test Script     ${NC}"
echo -e "${BLUE}=====================================${NC}\n"

# Clean up function
cleanup() {
  echo -e "\n${YELLOW}Cleaning up containers and volumes...${NC}"
  docker-compose down
  echo -e "${GREEN}Cleanup complete.${NC}"
}

# Trap Ctrl+C
trap cleanup INT

echo -e "${YELLOW}Step 1: Building and starting containers...${NC}"
docker-compose down -v
docker-compose build --no-cache
if [ $? -ne 0 ]; then
  echo -e "${RED}Build failed. Exiting.${NC}"
  exit 1
fi

echo -e "\n${YELLOW}Step 2: Starting services...${NC}"
docker-compose up -d
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to start services. Exiting.${NC}"
  exit 1
fi

echo -e "\n${YELLOW}Step 3: Waiting for services to initialize (30 seconds)...${NC}"
sleep 30

echo -e "\n${YELLOW}Step 4: Checking app health...${NC}"
HEALTH_CHECK=$(curl -s http://localhost:8000/health)
if [[ $HEALTH_CHECK == *"healthy"* ]]; then
  echo -e "${GREEN}Health check passed: $HEALTH_CHECK${NC}"
else
  echo -e "${RED}Health check failed: $HEALTH_CHECK${NC}"
  echo -e "${YELLOW}Checking logs for errors...${NC}"
  docker-compose logs finance-app | grep -i "error"
  echo -e "${RED}Test failed. Cleaning up...${NC}"
  cleanup
  exit 1
fi

echo -e "\n${YELLOW}Step 5: Checking for NLTK errors in logs...${NC}"
NLTK_ERRORS=$(docker-compose logs finance-app | grep -i "nltk" | grep -i "error" | wc -l)
if [ $NLTK_ERRORS -gt 0 ]; then
  echo -e "${RED}Found $NLTK_ERRORS NLTK errors in logs:${NC}"
  docker-compose logs finance-app | grep -i "nltk" | grep -i "error"
  echo -e "${RED}Test failed. Cleaning up...${NC}"
  cleanup
  exit 1
else
  echo -e "${GREEN}No NLTK errors found in logs.${NC}"
fi

echo -e "\n${GREEN}All tests passed successfully!${NC}"
echo -e "${BLUE}The application is running at: http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop and clean up containers${NC}"

# Keep script running until user presses Ctrl+C
read -r -d '' _ </dev/tty

# Clean up
cleanup
exit 0 