# AGENTS.md — `spark-jobs/`

This file applies to all assets under `spark-jobs/`.

## Purpose

This folder covers Week 6 to Week 7 Spark-based migration and orchestration support.

## Scope

- `migration/`: full export, incremental load, CDC reflection, reconciliation
- `orchestration/`: support jobs invoked by Airflow or higher-level workflows

## Rules

- Keep migration strategies clearly separated: full load, incremental load, CDC.
- Reconciliation and source-to-target validation are mandatory concerns.
- Prefer business-safe migration logic over convenience shortcuts.
- Use naming and table semantics consistent with Nexus Pay legacy migration scenarios.
- If a change affects Airflow orchestration, preserve compatibility with DAG-level assumptions.
