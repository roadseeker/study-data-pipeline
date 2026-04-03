# AGENTS.md — `scripts/`

This file applies to all scripts under `scripts/`.

## Purpose

Scripts in this folder are hands-on lab utilities for setup, simulation, validation, and rehearsal. They should feel operational and demo-ready.

## Scope by Week

- Week 1: initialization and full-stack health checks
- Week 2: Kafka producer, consumer, and partition validation
- Week 3: API, CSV, and NiFi verification scripts
- Week 4: Flink event generation, checkpoint monitoring, and verification
- Week 8: integrated rehearsal and failure-drill automation in `e2e/`

## Rules

- Prefer task-oriented scripts with clear names and predictable outputs.
- Verification scripts should make pass/fail expectations obvious.
- Use realistic sample data and Nexus Pay business terms.
- Use `nexuspay` / `NexusPay` machine-readable identifiers consistently in script names, sample payloads, CLI examples, and emitted metadata.
- Keep scripts easy to run locally in the lab environment.
- Avoid mixing unrelated weekly concerns in one script unless it is intentionally an integration or rehearsal script.
- When adding a verification script, favor names like `verify_*.sh` or `verify_*.py`.
