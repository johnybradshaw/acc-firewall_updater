---
title: Merging dependency update PRs one by one makes the rest conflict
author: John
date: 2026-11-09
standing: true
id: l-30de81a5
scope: repo
status: active
src: init-sessions
---

## Watch out
- After the first Dependabot PRs were merged, the others conflicted in the requirements file because their lines sit next to each other. Rebase requests to Dependabot took a while to be picked up.
- In the code: Merge Dependabot PRs sequentially. Comment `@dependabot rebase` on the conflicting ones, wait for CI to pass again, then merge. Do not tag a release until all are in. Re-read the PR after rebase before merging.

_From past Claude sessions here, Oct 22._
