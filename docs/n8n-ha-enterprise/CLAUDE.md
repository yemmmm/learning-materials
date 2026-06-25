# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a documentation and reference-configuration repo for an n8n Enterprise HA cluster deployed via Docker Compose (Queue Mode). It lives inside `~/learning-materials/` and tracks the configuration, architecture docs, and deployment guides.

This is NOT an application — there is no build, test, or lint step. It's documentation, shell scripts, and Docker/infra configuration.

## Key Files

- `docker-compose.yml` — Main server (11vm): Traefik, n8n main, n8n worker, Redis, task runners
- `docker-compose.worker.yml` — Worker server (10vm): n8n worker + runner only (connects to shared Redis + external PG)
- `.env.example` — Template for required environment variables
- `config/` — Per-service config files: Traefik (static + dynamic), Redis
- `scripts/` — init.sh, start.sh, stop.sh, status.sh, healthcheck.sh, scale-workers.sh

## Architecture Quick Reference

- **Traefik** (80/443) — LB with sticky cookie `n8n_sid`, TLS termination, auto HTTP→HTTPS redirect
- **n8n main** — API/UI/Webhook, queue mode
- **n8n worker** — Stateless executors, pull jobs from BullMQ in Redis
- **Redis 7** — BullMQ queue + leader election. Accessible from worker server via host network
- **Task Runners** — Sidecar containers (`n8nio/runners`) for Code node execution (n8n 2.0+ requirement)
- **PostgreSQL** — External, not managed by these compose files

## Multi-Server Deployment

| Server | Hostname | Compose File | Services |
|--------|----------|-------------|----------|
| Main (11vm) | li19dksfai11vm.bmwgroup.net | docker-compose.yml | Traefik, Redis, n8n, n8n-worker, runners |
| Worker (10vm) | li19dksfai10vm.bmwgroup.net | docker-compose.worker.yml | n8n-worker, runner (connects to 11vm Redis) |

## Critical Configuration Rules

1. `N8N_ENCRYPTION_KEY` MUST be identical across ALL instances (main + workers, both servers)
2. `RUNNERS_AUTH_TOKEN` MUST be identical across ALL instances
3. `WEBHOOK_URL` MUST point to the Traefik LB
4. Worker server (10vm) MUST set `QUEUE_BULL_REDIS_HOST=li19dksfai11vm.bmwgroup.net`
5. Redis `maxmemory-policy=noeviction` — queue jobs must never be evicted
6. Each n8n instance MUST have a paired task runner sidecar for Code node execution

## Enterprise License Dependency

- Queue mode (multi-main) works only with an active Enterprise license
- Without license: cluster starts and runs community features; architecture is "license-ready"

## Reference

Based on official n8n-hosting: https://github.com/n8n-io/n8n-hosting/tree/main/docker-compose/withPostgresAndWorker
