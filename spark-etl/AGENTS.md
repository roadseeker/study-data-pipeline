# AGENTS.md — `spark-etl/`

This file applies to all assets under `spark-etl/`.

## Purpose

This folder contains Week 5 batch ETL deliverables centered on Spark and Delta Lake using Medallion architecture.

## Rules

- Preserve the Bronze, Silver, Gold layer distinction.
- Treat data quality validation as a first-class requirement, not an afterthought.
- Favor deterministic, batch-friendly transformations.
- Delta Lake operations such as `MERGE`, maintenance, and time travel should be reflected accurately.
- Code, config, and verification scripts should stay synchronized.
- Business outputs should remain meaningful for Nexus Pay reporting use cases such as daily summaries, customer statistics, and fee settlement.
