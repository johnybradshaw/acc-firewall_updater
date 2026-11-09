---
title: Each release needs a README changelog entry committed before tagging
author: John
date: 2026-11-09
standing: true
id: l-c9397457
scope: repo
status: active
src: init-sessions
---

## Decided
- Releases are squash-merged and each gets a changelog commit in the README before the tag. The previous entry is the template: a Summary of Changes section plus matching release notes.
- In the code: In `acc-firewall_updater` add the entry to the README "Summary of Changes" section, using the previous release as the format. Commit `docs: update changelog for vX.Y.Z release`, wait for main CI green, then tag.

_From past Claude sessions here, Oct 22._
