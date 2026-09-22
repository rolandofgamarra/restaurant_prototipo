---
description: SDD phase 0 — interview and write a new spec in EARS notation
argument-hint: "<short description of the feature>"
---

Feature: $ARGUMENTS

Dispatch the `sdd-spec-writer` subagent.

Do NOT write code at any point in this command.

1. Read `docs/constitution.md` and every existing `specs/*/spec.md` first, so the new
   spec cannot contradict what was already agreed.
2. Interview me **one question at a time**, maximum 6, waiting for each answer. Focus on
   edge cases, error behaviour and what stays out of scope. If I drift into HOW, bring me
   back to WHAT.
3. Write `specs/NNN-<kebab-case>/spec.md` using `specs/TEMPLATE-spec.md`, no section
   skipped, requirements numbered RF-n in EARS, in Spanish.
4. Mark every unknown as `[NECESITA ACLARACIÓN: <pregunta concreta>]`. Do not guess.
5. Update `docs/STATE.md` and stop for my explicit approval.
