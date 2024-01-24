# Copyright (c) 2024 The Brave Authors. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.

"""Brave sheriff_config service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dashboard.models import subscription

def _GetTopMetricsSubscription():
  return subscription.Subscription(name='Top Metrics',
                                    monorail_project_id='brave-browser',
                                    auto_triage_enable=True,
                                    auto_bisect_enable=False)
def _GetOtherMetricsSubscription():
  return [subscription.Subscription(name='Brave Sheriff',
                                    monorail_project_id='brave-browser',
                                    auto_triage_enable=True,
                                    auto_bisect_enable=False)]

def _IsTopMetrics(path: str) -> bool:
  TOP_METRICS_PATTERNS = [
    # Memory:
    'reported_by_os:private_footprint_size/',
    'reported_by_chrome:allocated_objects_size/',

    # CPU:
    'cpuTime:',

    # JS performance:
    'speedometer2/RunsPerMinute/',
    'rectsBasedSpeedIndex',

    # apk
    'apk_size/InstallSize',

    # Page loading:
    'timeToOnload/'
    'timeToFirstMeaningfulPaint/'
    'cpuTimeToFirstMeaningfulPaint/'

    # Process number
    'ChildProcess.Launched.UtilityProcessHash#count',
    'all_processes:process_count',
  ]
  for pattern in TOP_METRICS_PATTERNS:
    if path in pattern:
      return True

  return False

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

    if _IsTopMetrics(path):
      return [_GetTopMetricsSubscription()], None
    else:
      return [_GetOtherMetricsSubscription()], None

  def List(self, check=False):
    return [_GetTopMetricsSubscription(), _GetOtherMetricsSubscription()], None

  def Update(self, check=False):
    return True, None
