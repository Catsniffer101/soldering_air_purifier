# Project Steering (Overview)

## Purpose
This repository manages a mixed HW/FW/SW project using spec-driven development (Kiro structure).
Specifications, design decisions, and verification plans are treated as version-controlled sources of truth.

## Structure
- `.kiro/steering/`: project-wide rules ("constitution")
- `.kiro/specs/`: specs per subsystem, each containing requirements/design/tasks (and verification when needed)
- `scripts/`: automation for requirements/traceability checks and report generation
- `.github/workflows/`: CI checks (ID uniqueness, traceability, report generation)

## Domains
- HW: electronics / PCB / BOM / assembly / bench tests
- FW: device firmware (embedded)
- SW: host tools / scripts / desktop/web utilities
- SYS: system-level requirements and interfaces
- OPS: build, release, manufacturing/bring-up procedures
