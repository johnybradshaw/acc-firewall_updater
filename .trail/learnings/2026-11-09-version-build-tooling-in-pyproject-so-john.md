---
title: Version build tooling in pyproject so Python 3.14 builds do not break
author: John
date: 2026-11-09
standing: true
id: l-0c5163cf
scope: repo
status: active
src: init-review
touches:
  - pyproject.toml
  - setup.py
---

## Decided
- The old setup_requires path for the version plugin broke the CI build on Python 3.14 with newer setuptools, which no longer ships pkg_resources.
- In the code: Keep setuptools_scm in pyproject.toml build-system.requires (setuptools>=82.0.1). Do not reintroduce setup_requires in setup.py.

_From PR #53 here, Apr 18._
