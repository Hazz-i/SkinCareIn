# Docker Compose Setup Design Spec

This document specifies the design for setting up Docker Compose to build and run the backend service, connecting it to an existing external MySQL database running in another container.

## Context and Requirements

- **Backend Service**: Formatted to build from local `dockerfile`. Exposes and listens on port `8888`.
- **Database**: Already running in a container named `mysql_server` inside the `skinsight-net` Docker network.
- **Environment**: DB configuration (user, password, port, etc.) is stored in `.env`.
- **Port Mapping**: The service must map port `8888:8888` on the host, and the database connection should retrieve settings from `.env`.

## Proposed Architecture

A single `docker-compose.yml` file is created at the repository root.

```yaml
services:
  web:
    build:
      context: .
      dockerfile: dockerfile
    ports:
      - "8888:8888"
    networks:
      - skinsight-net
    env_file:
      - .env
    environment:
      - DB_HOST=mysql_server
      - DB_PORT=${DB_PORT}

networks:
  skinsight-net:
    external: true
```

### Key Decisions

1. **External Network Integration**: Instead of running a new database container, the compose file connects the web service directly to the existing external `skinsight-net` network where `mysql_server` resides.
2. **Environment Variable Reading**:
   - `env_file: - .env` loads all environment configurations.
   - `environment: - DB_HOST=mysql_server` overrides the default `localhost` host from `.env` with the container name inside the Docker network.
   - `DB_PORT=${DB_PORT}` passes the port value dynamically from the `.env` file.
3. **No Database Re-definition**: Since the database is already running, there is no `db` service definition, avoiding resource conflicts or duplicates.

## Verification Plan

1. Verify that `docker-compose.yml` syntax is correct.
2. Ensure that the backend service correctly connects to the external network and retrieves environment variables.
