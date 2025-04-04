
<!-- Copyright (c) 2023 The Brave Authors. All rights reserved.
     This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file,
     You can obtain one at https://mozilla.org/MPL/2.0/.
-->

General
========

The brave performance dashboard is forked version of the catapult dashboard deployed to https://brave-perf-dashboard.appspot.com. It's used to track Brave and Chrome performance.

Deploy
========

[Github action to deploy](https://github.com/brave/catapult/actions/workflows/deploy-to-appengine.yml)

What was changed
========

[Diff with upstream](https://github.com/brave/catapult/compare/upstream...brave:catapult:main)


Update
========

1. Update `upstream` branch to the recent catapult commit.
2. Make a new branch `update-something` from `main`, merge `upstream` to it, resolve the conflicts.
3. Deploy and verify your changes.
4. Make a PR from your branch to `main`.
