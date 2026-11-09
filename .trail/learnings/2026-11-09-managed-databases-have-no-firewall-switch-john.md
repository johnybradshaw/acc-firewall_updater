---
title: Managed databases have no firewall switch; the allow list is the firewall
author: John
date: 2026-11-09
standing: true
id: l-6b27dcc9
scope: repo
status: active
src: init-review
---

## Decided
- The Linode API has no on/off toggle for database firewalls, so enabling means stripping open-to-the-world ranges. An empty list would block everyone.
- In the code: In databases.py, --db-enable-firewall removes 0.0.0.0/0 and ::/0 from allow_list only after appending the user's IP, so the list is never empty. It is ignored in remove mode.

_From PR #79 here, Jul 9._
