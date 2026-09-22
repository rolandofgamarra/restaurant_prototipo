---
description: SDD phase 7 — document deployment and archive the validated spec
---

Only run on a spec whose `validation.md` says **cumplida** and whose `privacy-audit.md`
has no unresolved blocking finding.

1. Update `docs/DEPLOYMENT.md`: what this feature adds to the deployment — new
   environment variables, migrations and their application order, scheduled tasks,
   third-party credentials needed, rollback procedure, and what to check after release.
2. Move `specs/NNN-<kebab>/` to `specs/done/NNN-<kebab>/`.
3. Update `docs/STATE.md`: phase closed, feature archived, next spec.
4. Write or refresh `client/NNN-resumen.md` — the business-facing summary in plain
   Spanish: what the client can now do, what changed for each role, what is still
   pending. No RF, no EARS, no stack, no file names, no jargon.
5. Report the closing summary: RF delivered, gate status, open debt.
