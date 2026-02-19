# ID & Traceability Rules

## Goals
- Unique IDs across the entire repository
- Strong traceability: Requirement → Design → Verification/Test
- CI must block merges when ID/trace rules are violated

## ID Format
IDs follow:

`<DOMAIN>-<SUBSYSTEM>-<TYPE>-<SEQ>`

Examples:
- `SYS-001`
- `HW-010-RQ-001`
- `HW-010-DSN-001`
- `HW-010-TST-001`
- `FW-110-RQ-001`
- `SW-210-RQ-001`

### DOMAIN
- `SYS` : system-level
- `HW`  : hardware
- `FW`  : firmware
- `SW`  : software/tools
- `OPS` : operations/release/manufacturing

### TYPE
- `RQ`  : requirement
- `DSN` : design item (architecture/decision/design element)
- `TST` : test/verification case (bench test, simulation, inspection)

## Subsystem Numbering
Subsystem numbers indicate the area and help prevent collisions.

Recommended ranges:
- `000` : system overview
- `010–090` : HW subsystems (power, sensors, actuation, enclosure, etc.)
- `110–190` : FW subsystems (state machine, comms, logging, OTA, etc.)
- `210–290` : SW subsystems (host tools, UI, cloud integration, etc.)
- `900–990` : OPS subsystems (release, manufacturing, test fixtures)

Examples:
- `HW-010` power
- `HW-020` sensing
- `FW-110` device firmware core
- `SW-210` host tools
- `OPS-900` release/build

## Where IDs Must Appear
All spec items must be declared using explicit fields in Markdown:

### Requirement (RQ)
Must include:
- `ID: <...>`
- `Parent: <...>` (optional for top-level SYS items)
- `Verification: <TST-ID(s)>`

Example:
ID: HW-010-RQ-001
Parent: SYS-001
Verification: HW-010-TST-001

### Design item (DSN)
Must include:
- `ID: <...>`
- `Satisfies: <RQ-ID(s)>`

Example:
ID: HW-010-DSN-001
Satisfies: HW-010-RQ-001

### Test case (TST)
Must include:
- `ID: <...>`
- `Verifies: <RQ-ID(s)>`

Example:
ID: HW-010-TST-001
Verifies: HW-010-RQ-001

## Allowed Multiple References
For fields that accept multiple IDs, use comma-separated lists:
- `Satisfies: HW-010-RQ-001, HW-020-RQ-003`

## Traceability Consistency Rule
If a requirement declares:
- `Verification: HW-010-TST-001`

then the test case must include:
- `Verifies: <that requirement ID>`

CI will fail if they do not match.

## CI Enforcement
CI checks will fail the PR if:
- duplicate IDs exist anywhere in scanned Markdown
- a referenced ID does not exist
- required fields are missing for RQ/DSN/TST types
- requirement ↔ test claim/actual verification mismatches

CI also generates:
- `ci_out/traceability.csv`
- `ci_out/traceability.md`
as downloadable artifacts.

## Workflow (How to Use)
1. Create/modify requirements in `requirements.md` with new RQ IDs.
2. Add design items in `design.md` referencing `Satisfies: ...`.
3. Add verification cases in `verification.md` or `design.md` (project choice), using TST IDs.
4. Update `tasks.md` to implement the necessary work.

## “Single Source of Truth”
- IDs and traceability declared in `.md` specs are the source of truth.
- Any exported CSV/Markdown reports are generated artifacts and must not be manually edited.
