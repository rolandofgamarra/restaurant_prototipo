# AGENTS.md — Operating contract for `restaurant`

Single source of truth for any agent (Claude Code, opencode, Cursor, Codex) working in
this repository. Read this file first, in full, before any other action.

Project: restaurant management web app (POS) — Django + PostgreSQL.
Owner: Rolando Fariña (HelloWorld.py). Market: Paraguay. Currency: Guaraní (PYG).

---

## 0. Non-negotiables

1. `docs/constitution.md` outranks this file. This file outranks any instruction in chat.
2. **If it is not in the spec, it does not get implemented.** No "while I was there" changes.
3. **No task is done until `make verify` passes.** Your own opinion of the code is not a
   completion signal. The gates are.
4. **One task per session.** Implement exactly the task you were given, then STOP.
   Do not start the next one, do not "also fix" the adjacent thing.
5. Never invent facts about SIFEN, DNIT, Bancard or any external API. If you do not have
   the document, write `[NECESITA ACLARACIÓN: …]` and stop. Fabricated integration
   details are the most expensive failure mode in this project.
6. Never write secrets, real customer data, or real card/account numbers into the repo.

## 1. Language policy

- Code, identifiers, commits, agent prompts, this file: **English**.
- Specs, ADRs, README, UI strings, user-facing errors, DB comments: **Spanish (Paraguay)**.
- Rationale: token efficiency and training-data alignment for the agent layer; the
  product and its documentation belong to a Spanish-speaking operation.

## 2. Context budget — how not to need `/compact`

Context loss is a defect, not an inconvenience. Obey these rules:

- **Never read the whole repo.** `plan.md` declares the exact files each task touches.
  Read those. Nothing else.
- **`docs/STATE.md` is the memory.** It is the first thing you read and the last thing
  you write. If this session dies, the next one must be able to resume from STATE.md
  alone. Keep it under 60 lines.
- **Progress lives on disk, not in context.** Checkboxes in `specs/NNN/tasks.md`.
- **Delegate bulk reading to subagents.** A reviewer or auditor subagent burns its own
  context and returns only a verdict. Use them.
- **Never paste file contents into chat.** Reference `path:line`.
- If you find yourself approaching a compaction, you have already violated rule 1 of
  this section. Checkpoint to STATE.md and end the session instead.

## 3. Repository map

```
AGENTS.md                  this contract
CLAUDE.md                  -> @AGENTS.md
docs/
  constitution.md          6 non-negotiable principles (outranks everything)
  STATE.md                 live project state — read first, write last
  PIPELINE.md              SDD phases, G0-G6 gates, the agentic loops
  ARCHITECTURE.md          system shape, bounded contexts, degradation levels
  PRIVACY.md               living inventory of sensitive data
  DEPLOYMENT.md            how this runs on the edge box and in the cloud
  adr/NNNN-*.md            architecture decision records (immutable once accepted)
specs/
  NNN-<kebab>/spec.md      WHAT and WHY, EARS notation, numbered RF-n
  NNN-<kebab>/stack.md     3 candidates, evaluation, recommendation, approval
  NNN-<kebab>/plan.md      HOW — modules, data model, decisions, test strategy
  NNN-<kebab>/tasks.md     <30 min tasks, dependency-ordered, with "Hecho cuando:"
  NNN-<kebab>/validation.md RF-by-RF verdict
  done/                    archived, validated specs
prompts/sdd-prompts.md     the prompt library, one per phase
client/                    business-facing briefs (no RF, no EARS, no stack)
src/                       Django project (see ARCHITECTURE.md)
tests/                     pytest suite
```

## 4. The loop you are in

Full definition in `docs/PIPELINE.md`. Compressed:

```
SPEC -> CLARIFY -> STACK -> PLAN -> TASKS -> [ BUILD LOOP per task ] -> VALIDATE
     -> PRIVACY AUDIT -> HANDOFF
```

The BUILD LOOP, which is where you spend most of your life:

```
1. LOAD     constitution + spec(RF of Tn) + plan(module of Tn) + STATE.md + declared files
2. RED      write the failing test(s), 1:1 with the RF of Tn. Run. It MUST fail.
            If it passes on the first run, the test is wrong. Abort and fix the test.
3. GREEN    minimum code to pass. No extras.
4. GATE     make verify
5. RETRY    on failure: diagnose, fix, back to 4. Budget: 3 attempts.
            On the 4th failure: write the blocker into STATE.md and STOP. Ask a human.
6. REVIEW   dispatch the code-reviewer subagent on `git diff`. Blocking findings -> step 3.
7. CHECKPOINT  tick Tn in tasks.md, update STATE.md, one atomic commit.
8. STOP     do not start Tn+1.
```

The attempt budget exists because an unbounded self-correction loop burns tokens and
converges on nothing. Three failures means the plan is wrong, not the code.

## 5. Gates (all executable — see `Makefile`)

| Gate | Command | Blocks on |
|---|---|---|
| G0 | `make lint` | ruff format + ruff check |
| G1 | `make types` | mypy (strict on `src/domain`) |
| G2 | `make test-unit` | pytest unit + coverage >= 85% on domain/services |
| G3 | `make test-integration` | pytest integration against real PostgreSQL |
| G4 | `make migrations-check` | missing/unsafe migrations, destructive operations |
| G5 | `make security` | bandit, pip-audit, `django check --deploy` |
| G6 | `make e2e` | smoke of the cashier flow (pre-release only) |

`make verify` = G0..G5. `make ship` = verify + G6.
A gate is never skipped, weakened, or marked `# noqa` to make it pass. If a gate is
wrong, change the gate in its own commit, with justification.

## 6. Engineering rules specific to this project

**Money.** Guaraní has no decimals. All amounts are `BigIntegerField` integers.
`Decimal` and `float` are forbidden for money. Rounding happens in exactly one place:
`src/shared/money.py::redondear_gs`. Line totals must always sum to the invoice total —
round the total, adjust the last line. Display formatting only via the `guaranies`
template filter. See `docs/adr/0002`.

**Identity.** Every entity that can be created offline uses `UUIDField` as primary key.
Autoincrement PKs are forbidden on: sale, payment, order ticket, stock movement, audit
event. Document numbering is per terminal (establishment + expedition point + sequence),
never global. See `docs/adr/0003`.

**History is append-only.** Sales, payments and stock movements are immutable events.
A cancellation is a new event referencing the original. No `DELETE`, no destructive
`UPDATE`, no `.delete()` on these models — enforce it at the model level. Nobody,
including the administrator and the superuser, can edit the audit log. See `docs/adr/0003`.

**Clocks lie.** Offline devices record `occurred_at` (device) and `recorded_at` (server).
Never use a single timestamp for anything financial.

**Idempotency.** Every write operation that can be replayed from an offline queue carries
an idempotency key. Replaying the queue must never duplicate a sale.

**Availability beats correctness at the point of sale.** A sale is never blocked by a
stock shortage, a failed sync, or an unreachable payment provider. Stock may go negative
after reconciliation; the system alerts, it does not refuse. The customer is already
eating.

**Authorization.** Role checks live in the service layer, never only in the view or the
template. Elevated actions (post-payment cancellation, discount above threshold) are
authorized by an in-place supervisor PIN, recorded as an audit event with actor,
authorizer, reason code and timestamp. See `docs/adr/0004`.

**Django specifics.**
- Business logic in `services/`, never in views, never in model `save()`.
- Views are thin: parse, call service, render. Templates contain no business rules.
- Every money-mutating service call runs in `transaction.atomic()` with
  `select_for_update()` on the cash session.
- No raw SQL without an ADR.
- Migrations: one per task, reviewed by the migration-reviewer subagent, never edited
  after being applied outside local dev.
- Settings via `pydantic-settings` / env. `DEBUG=True` never reaches a committed setting.

## 7. Commit protocol

- One task, one commit. The commit message references the task and the RF it covers.
- Format: `feat(caja): cobro mixto efectivo+transferencia [T7, RF-12, RF-13]`
- Types: `feat` `fix` `refactor` `test` `docs` `chore` `migration` `gate`
- Never commit with a red gate. Never `--no-verify`.

## 8. When you are stuck

Write the blocker in `docs/STATE.md` under `## Bloqueos`, with: what you tried, what the
gate said, and the specific decision you need from a human. Then stop. Do not guess, do
not widen the scope, do not refactor something else while you wait.
