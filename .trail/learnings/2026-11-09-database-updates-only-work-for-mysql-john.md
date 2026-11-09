---
title: Database updates only work for MySQL and PostgreSQL; other engines are skipped
author: John
date: 2026-11-09
standing: true
id: l-e631b196
scope: repo
status: active
src: init-review
---

## Decided
- The update endpoint is rooted by engine, so other engines listed by the instances endpoint cannot be committed. Failing the whole batch for them was rejected.
- In the code: In databases.py, only mysql and postgresql are updated via /databases/{engine}/instances/{id}. Report other engines as a per-database skip.

_From PR #60 here, May 8._
