---
title: Python version pin in the dev container must be kept in sync with CI by hand
author: John
date: 2026-11-09
standing: true
id: l-497468ca
scope: repo
status: active
src: init-review
touches:
  - setup.py
---

## Watch out
- Dev container images are not reused in CI, so the two pins can drift apart without any check.
- In the code: When changing the Python version in CI workflows or setup.py python_requires, also update the devcontainer config. It sets PYTHONPATH to src to mirror CI.

_From PR #86 here, Aug 15._
