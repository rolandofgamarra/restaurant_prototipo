---
description: SDD phase 6 — privacy and defensive security audit of the completed feature
---

Dispatch the `security-auditor` subagent against the validated feature.

Cover, in this order: data inventory and minimisation, least privilege across roles,
audit-log integrity, attack surface, fraud paths specific to a POS, secrets and
configuration, dependency vulnerabilities.

Update `docs/PRIVACY.md` with every sensitive datum this feature introduces — what,
why, where, who reads it, how long it is kept, how it is deleted.

Write `specs/NNN/privacy-audit.md` in Spanish. Order findings by severity, each with the
concrete scenario that exploits it and a specific remediation. Do not inflate severity.

State explicitly in the document that this is an engineering review and not legal advice.

Defensive only: no offensive tooling, no working proof of concept.
