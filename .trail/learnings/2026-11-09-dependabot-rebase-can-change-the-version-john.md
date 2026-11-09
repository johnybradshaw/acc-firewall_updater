---
title: Dependabot rebase can change the version floor from what the PR title says
author: John
date: 2026-11-09
standing: true
id: l-a177a758
scope: repo
status: active
src: init-sessions
touches:
  - pyproject.toml
  - requirements.txt
---

## Watch out
- After rebasing, the setuptools-scm PR raised its minimum to a newer version than its title stated. Writing the changelog from the title would have been wrong.
- In the code: Read the actual diff in `pyproject.toml` / `requirements.txt` on main after merging before writing the changelog entry. For v0.5.2 the floor was `setuptools_scm>=10.3.4`, not 10.2.3.

_From past Claude sessions here, Oct 22._
