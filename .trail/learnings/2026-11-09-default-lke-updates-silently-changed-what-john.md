---
title: Default LKE updates silently changed what existing scheduled runs touch
author: John
date: 2026-11-09
standing: true
id: l-23ab69b2
scope: repo
status: active
src: init-review
---

## Watch out
- Firewall runs began syncing IPs into every cluster's control plane access list by default. Anyone with cron on an account with clusters is affected unless they opt out.
- In the code: Use --no-lke (and --no-database) for firewall-only behaviour. --lke means LKE only. Mention opt-out flags in README cron examples when adding new implicit steps.

_From PR #54 here, Apr 20._
