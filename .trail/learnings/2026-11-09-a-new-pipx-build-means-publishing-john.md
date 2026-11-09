---
title: "A new pipx build means publishing a GitHub Release, which pushes to PyPI"
author: John
date: 2026-11-09
standing: true
id: l-4c3d1e08
scope: repo
status: active
src: init-sessions
touches:
  - CLAUDE.md
---

## Decided
- Publishing is triggered by a GitHub Release, with the version taken from the git tag. A PyPI version cannot be re-uploaded, so the release must wait until everything intended is merged.
- In the code: Repo `acc-firewall_updater` (PyPI `acc-fwu`). Version comes from the tag via setuptools_scm. Order per the repo CLAUDE.md: changelog commit, annotated tag `vX.Y.Z`, push tag, then create the GitHub Release. Verify with `pipx upgrade acc-fwu`.

_From past Claude sessions here, Oct 22._
