# Docker Compose Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `docker-compose.yml` file in the root directory to build the backend service using the existing `dockerfile`, map host port 8888, and retrieve DB configuration from `.env` over the external `skinsight-net` network.

**Architecture:** A single Docker Compose service `web` that builds the local directory, reads the `.env` file, overrides the database host to connect to the external network `skinsight-net` where the database container `mysql_server` is located.

**Tech Stack:** Docker Compose, Docker

## Global Constraints

- Must read database configurations from `.env` dynamically.
- Must run the web service on port 8888.
- Must connect to the existing external Docker network `skinsight-net`.
- Must set DB_HOST to `mysql_server` to connect internally.

---

### Task 1: Create docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

**Interfaces:**
- Consumes: `.env` file for database configuration (DB_PORT, DB_PASSWORD, DB_NAME, DB_USER)
- Produces: `docker-compose.yml`

- [ ] **Step 1: Write the docker-compose.yml file**

Create the file `docker-compose.yml` in the root folder with the following content:
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

- [ ] **Step 2: Run verification**

Run: `docker compose config`
Expected output: Syntax is valid, environment variables are correctly parsed.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml docs/superpowers/specs/2026-07-19-docker-compose-setup-design.md
git commit -m "feat: add docker-compose config for backend service"
```
