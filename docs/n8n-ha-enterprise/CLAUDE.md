# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a documentation and reference-configuration repo for an n8n Enterprise HA cluster deployed via Docker Compose (Multi-Main Queue Mode). It lives inside `~/learning-materials/` and tracks the configuration, architecture docs, and deployment guides for a real deployment at `/home/yangxiang/deployed-services/n8n-ha-enterprise/`.

This is NOT an application — there is no build, test, or lint step. It's documentation, shell scripts, and Docker/infra configuration.

## Key Files

- `docker-compose.yml` — Full 11-container topology (Traefik, 2× n8n-main, 3× n8n-worker, PostgreSQL, Redis, MinIO, Prometheus, Grafana)
- `docs/architecture.md` — C4 architecture, data flows, leader election, storage model, ADRs
- `docs/deployment-guide.md` — Deployment steps, tuning, backup, security hardening, troubleshooting
- `.env.example` — Template for required environment variables (encryption keys, DB/Redis/MinIO passwords)
- `config/` — Per-service config files: PostgreSQL conf, Redis conf, Traefik dynamic/file config, Prometheus scrape targets, Grafana provisioning
- `scripts/` — init.sh, start.sh, stop.sh, status.sh, healthcheck.sh, scale-workers.sh

## Architecture Quick Reference

- **Traefik** (5680) is the LB — uses file provider (not docker labels) to define the `n8n_cluster` service with sticky cookie `n8n_sid`
- **2× n8n-main** (leader/follower) — elected via Redis SET NX lock with 5s TTL. Leader handles at-most-once tasks (cron, polling). Both handle API/UI/webhook
- **3× n8n-worker** (`--concurrency=10`) — stateless; pull jobs from BullMQ in Redis; horizontal scale-out is the primary scaling lever
- **PostgreSQL 15** — single instance (user-accepted SPOF). Stores workflows, credentials, executions, users
- **Redis 7** — BullMQ queue + leader election lock. AOF+RDB persistence enabled; `maxmemory-policy=noeviction`
- **MinIO** — S3-compatible binary data storage (requires Enterprise license to activate; defaults to filesystem mode otherwise)
- **Prometheus + Grafana** — auto-provisioned dashboards for n8n metrics

## Critical Configuration Rules

1. `N8N_ENCRYPTION_KEY` MUST be identical across all main and worker instances
2. `WEBHOOK_URL` MUST point to the Traefik LB (not individual main instances)
3. Traefik's `n8n_cluster` service uses the file provider (`config/traefik/dynamic/dynamic.yml`), not docker labels — adding a main requires updating both docker-compose.yml AND dynamic.yml
4. Redis `maxmemory-policy=noeviction` — queue jobs must never be evicted
5. Worker `--concurrency` should scale with allocated CPU (~10 per 1.5 CPU cores)

## Enterprise License Dependency

- Multi-main mode works only with an active Enterprise license
- S3 binary data mode (N8N_DEFAULT_BINARY_DATA_MODE=s3) requires Enterprise license
- Without license: cluster still starts and runs community features; architecture is "license-ready"
