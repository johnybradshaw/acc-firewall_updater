---
title: Scheduled runs must exit non-zero and write to stderr when any target fails
author: John
date: 2026-11-09
standing: true
id: l-9bb368ff
scope: repo
status: active
src: init-review
---

## Decided
- Cron runs with quiet mode exited 0 and printed nothing even when every update failed, so failures were invisible. Expected skips were also counted as failures.
- In the code: In cli.py, main() exits 2 for partial failures, 1 for fatal errors, 0 for success, no-ops and skips. Failure diagnostics go to stderr even with --quiet. Count unsupported-engine and VPC-attached databases as skipped, not failed.

_From PR #76 here, Jul 2._
