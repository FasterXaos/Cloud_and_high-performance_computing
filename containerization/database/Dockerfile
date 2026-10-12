FROM postgres:16-alpine

# Runs only when the data volume is empty. Later restarts keep the volume as-is.
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
