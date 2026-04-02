# AGENTS.md — `flink-jobs/`

This file applies to all Flink code under `flink-jobs/`.

## Purpose

This folder contains Week 4 real-time stream-processing deliverables built with Java and Flink.

## Rules

- Keep the code focused on event-time processing, windows, fraud detection, and exactly-once delivery concerns.
- Prefer clear separation between jobs, functions, models, and utilities.
- Use PayNex event semantics consistently.
- Preserve readable Java structure suitable for portfolio review.
- Stream-processing correctness is more important than premature abstraction.
- If changing schemas or event models, ensure consistency with Kafka, NiFi, and documentation assumptions.
