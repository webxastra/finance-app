#!/bin/bash

# Finance App Docker Management Script
# Simplifies common Docker operations for the Finance App

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project name for docker-compose
PROJECT_NAME="finance-app"

# Display header
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  Finance App Docker Manager v1.0.0  ${NC}"
echo -e "${BLUE}=====================================${NC}\n"

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running or you don't have permission.${NC}"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo -e "Usage: $0 [command]\n"
    echo "Commands:"
    echo "  start        - Start all services"
    echo "  stop         - Stop all services"
    echo "  restart      - Restart all services"
    echo "  status       - Show status of all services"
    echo "  logs         - View logs from all services"
    echo "  logs app     - View logs from the web application"
    echo "  logs db      - View logs from the database"
    echo "  shell        - Open a shell in the web container"
    echo "  db-shell     - Open a PostgreSQL shell"
    echo "  build        - Rebuild the containers"
    echo "  clean        - Remove all containers and volumes"
    echo "  backup       - Backup the database"
    echo "  restore      - Restore database from backup"
    echo ""
}

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Check if Docker is running
check_docker

# Process commands
case "$1" in
    start)
        echo -e "${GREEN}Starting Finance App services...${NC}"
        docker-compose up -d
        echo -e "${GREEN}Services started. Access the application at http://localhost:8000${NC}"
        ;;
    
    stop)
        echo -e "${YELLOW}Stopping Finance App services...${NC}"
        docker-compose down
        echo -e "${GREEN}Services stopped.${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting Finance App services...${NC}"
        docker-compose down
        docker-compose up -d
        echo -e "${GREEN}Services restarted. Access the application at http://localhost:8000${NC}"
        ;;
        
    status)
        echo -e "${BLUE}Current status of Finance App services:${NC}"
        docker-compose ps
        ;;
        
    logs)
        if [ "$2" = "app" ]; then
            echo -e "${BLUE}Showing logs for the web application:${NC}"
            docker-compose logs -f finance-app
        elif [ "$2" = "db" ]; then
            echo -e "${BLUE}Showing logs for the database:${NC}"
            docker-compose logs -f finance-app-db
        else
            echo -e "${BLUE}Showing logs for all services:${NC}"
            docker-compose logs -f
        fi
        ;;
        
    shell)
        echo -e "${BLUE}Opening a shell in the web container...${NC}"
        docker-compose exec finance-app /bin/bash || docker-compose exec finance-app /bin/sh
        ;;
        
    db-shell)
        echo -e "${BLUE}Opening a PostgreSQL shell...${NC}"
        docker-compose exec finance-app-db psql -U ${DB_USER:-postgres} -d ${DB_NAME:-financeapp}
        ;;
        
    build)
        echo -e "${GREEN}Rebuilding Finance App containers...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}Build complete. Use './docker-manage.sh start' to start the services.${NC}"
        ;;
        
    clean)
        echo -e "${RED}WARNING: This will remove all containers and volumes for this project.${NC}"
        read -p "Are you sure you want to continue? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Removing all containers and volumes...${NC}"
            docker-compose down -v --remove-orphans
            echo -e "${GREEN}Cleanup complete.${NC}"
        else
            echo -e "${BLUE}Operation cancelled.${NC}"
        fi
        ;;
        
    backup)
        BACKUP_FILE="financeapp_backup_$(date +%Y%m%d_%H%M%S).sql"
        echo -e "${BLUE}Backing up database to ${BACKUP_FILE}...${NC}"
        
        # Make sure backups directory exists
        mkdir -p backups
        
        docker-compose exec -T finance-app-db pg_dump -U ${DB_USER:-postgres} -d ${DB_NAME:-financeapp} > "backups/${BACKUP_FILE}"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Backup completed successfully to backups/${BACKUP_FILE}${NC}"
        else
            echo -e "${RED}Backup failed.${NC}"
            exit 1
        fi
        ;;
        
    restore)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: No backup file specified.${NC}"
            echo -e "Usage: $0 restore <backup_file>"
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            echo -e "${RED}Error: Backup file $2 not found.${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}WARNING: This will overwrite the current database.${NC}"
        read -p "Are you sure you want to continue? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Restoring database from $2...${NC}"
            cat "$2" | docker-compose exec -T finance-app-db psql -U ${DB_USER:-postgres} -d ${DB_NAME:-financeapp}
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Database restored successfully.${NC}"
            else
                echo -e "${RED}Database restoration failed.${NC}"
                exit 1
            fi
        else
            echo -e "${BLUE}Operation cancelled.${NC}"
        fi
        ;;
        
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac

exit 0 