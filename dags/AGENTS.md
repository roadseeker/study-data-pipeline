# AGENTS.md — `dags/`

This file applies to all Airflow DAG files under `dags/`.

## Purpose

DAGs are orchestration deliverables, not toy examples. They should reflect real operational needs for scheduling, dependency control, monitoring, and recovery.

## Scope by Week

- Week 1: environment health-check DAG
- Week 7: migration, ETL, CDC monitoring, backfill, and master orchestration DAGs
- Week 8: acceptance rehearsal DAG

## Rules

- Use business-relevant DAG names and task naming.
- DAGs should reflect operational intent: validation, migration, ETL, monitoring, backfill, recovery, rehearsal.
- Preserve clear dependency structure and readable scheduling logic.
- Prefer practical operators and explicit failure behavior over decorative complexity.
- SLA, retries, alerting hooks, and recovery behavior matter in Week 7 and Week 8 assets.
