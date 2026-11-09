---
title: "Snyk PR check fails on quota, not on findings"
author: John
date: 2026-11-09
branch: 100-trail-setup
cost: { minutes: 1, tokens: 1640 }
id: l-8f4452b5
scope: repo
status: active
src: agent
touches:
  - ".github/workflows/python-app.yml"
---

## Watch out
- The Snyk check on pull requests can go red because the account ran out of its private-test quota, not because of a finding. Snyk's own PR comment still reports 0 issues. Snyk was removed from this repo's CI workflows, so this check comes from the Snyk GitHub app, not from a workflow here.
- In the code: The check is `security/snyk (johnybradshaw)`, with the failure text "You have used your limit of private tests". `main` has no required status checks, so it does not block a merge. Before merging past it, confirm that every GitHub Actions check passed (Test, Build release distributions, CodeQL, Bandit, dependency-review, claude-review) and that the Snyk comment shows 0 issues. To stop the noise, uninstall the Snyk app from the repo or raise the quota; changing the workflows will not help.
