---
title: Remove the Snyk secret only after the Snyk CI steps are merged away
author: John
date: 2026-11-09
standing: true
id: l-d07c0ca2
scope: repo
status: active
src: init-review
---

## Watch out
- The still-live Snyk steps on main would fail if the token was deleted before the removal PR landed.
- In the code: After PR #85 is on main, delete the SNYK_TOKEN repo secret. Do not delete it earlier. The scan job keeps Bandit with SARIF upload, and CodeQL and dependency review run as separate workflows.

_From PR #85 here, Aug 15._
