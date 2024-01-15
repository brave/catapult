# Copyright (c) 2024 The Brave Authors. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.

"""Brave sheriff_config service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dashboard.models import subscription

def _GetBraveSubscriptions():
  return [subscription.Subscription(name='Brave Sheriff',
                                    monorail_project_id='brave-browser',
                                    auto_triage_enable=True,
                                    auto_bisect_enable=False)]


class InternalServerError(Exception):
  """An error indicating that something unexpected happens."""

class BraveSheriffConfigClient(object):
  def Match(self, path, check=False):
    if path.find('test-agent') != -1:
      return [], None

    if path.find('metrics_duration') != -1:
      return [], None

    if (path.find('_avg') != -1 or
        path.find('_sum') != -1 or
        path.find('_min') != -1 or
        path.find('_max') != -1):
      return [], None

    # TODO: fix backend errors

    return _GetBraveSubscriptions(), None

  def List(self, check=False):
    return _GetBraveSubscriptions(), None

  def Update(self, check=False):
    return True, None
