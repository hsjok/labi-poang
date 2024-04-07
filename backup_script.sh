#!/bin/bash

# Set the date format for the backup file
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Backup file name
BACKUP_FILENAME="backup_${BACKUP_DATE}.sql"

# PostgreSQL details
PG_HOST="app_db_1"
PG_PORT="5432"
PG_USER="henriksjokvist"
PG_DB="labi_points_db"

# Run pg_dump
docker exec app_db_1 pg_dump -h $PG_HOST -p $PG_PORT -U $PG_USER $PG_DB > ~/backup/$BACKUP_FILENAME
