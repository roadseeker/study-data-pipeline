# AGENTS.md — `scripts/`

This file applies to all scripts under `scripts/`.

## Purpose

Scripts in this folder are hands-on lab utilities for setup, simulation, validation, and rehearsal. They should feel operational and demo-ready.

## Folder Mapping

- `foundation/`: initialization and full-stack health checks
- `kafka/`: producer, consumer, partition, and replication verification
- `nifi/`: API, CSV, DB, and NiFi ingestion support scripts
- `e2e/`: integrated rehearsal and failure-drill automation

## Rules

- Prefer task-oriented scripts with clear names and predictable outputs.
- Verification scripts should make pass/fail expectations obvious.
- Use realistic sample data and Nexus Pay business terms.
- Use `nexuspay` / `NexusPay` machine-readable identifiers consistently in script names, sample payloads, CLI examples, and emitted metadata.
- Keep scripts easy to run locally in the lab environment.
- Avoid mixing unrelated weekly concerns in one script unless it is intentionally an integration or rehearsal script.
- When adding a verification script, favor names like `verify_*.sh` or `verify_*.py`.
- Place new scripts by domain responsibility rather than by week number.
