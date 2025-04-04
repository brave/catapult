# Copyright (c) 2024 The Brave Authors. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.

"""Brave sheriff_config service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re

BRAVE_TOP_METRICS_SHERRIF = 'Top Metrics'

from dashboard.models import subscription

_TOP_METRICS_PATTERN = re.compile('|'.join([
    # Memory:
    'reported_by_os:private_footprint_size/',
    'reported_by_chrome:allocated_objects_size/',

    # CPU:
    'cpuTime:',

    # speedometer3:
    'speedometer3/Score',

    # jetstream2:
    'jetstream2/Score',

    # Motionmark:
    'rendering.(desktop|mobile)/motionmark/',

    'rectsBasedSpeedIndex',

    # apk_size:
    'apk_size/(TransferSize|InstallSize|InstallBreakdown)',

    # Startup
    'Startup.FirstWebContents.MainNavigationStart',
    'startup/navigationStart',
    'system_health.common_(desktop|mobile)/navigationStart',

    # Page loading:
    'timeToOnload/',
    'timeToInteractive/',
    'timeToFirstMeaningfulPaint/',
    'cpuTimeToFirstMeaningfulPaint/',

    # Process number
    'ChildProcess.Launched.UtilityProcessHash#count',
    'all_processes:process_count',
]))

_IGNORE_PATTERN = re.compile('|'.join([
  # '^BravePerf/test-agent',
  '/Metric_duration',
  '_avg',
  '_sum',
  '_min',
  '_max',
  '_std',

  # skip aggregate metrics:
  r'^([^/]+/){2}system_health.\w+(/[^/]+){1,2}$',
  r'^([^/]+/){2}loading.[^/]+(/[^/]+){1,2}$',
]))

def _GetAnomalyConfigs():
  config = subscription.AnomalyConfig()
  config.min_segment_size = 2
  return [config]

def _GetTopMetricsSubscription():
  return subscription.Subscription(name=BRAVE_TOP_METRICS_SHERRIF,
                                   monorail_project_id='brave-browser',
                                   anomaly_configs = _GetAnomalyConfigs(),
                                   visibility = subscription.VISIBILITY.PUBLIC,
                                   auto_triage_enable=True,
                                   auto_bisect_enable=False)

def _GetOtherMetricsSubscription():
  return subscription.Subscription(name='Brave Sheriff',
                                   monorail_project_id='brave-browser',
                                   anomaly_configs = _GetAnomalyConfigs(),
                                   visibility = subscription.VISIBILITY.PUBLIC,
                                   auto_triage_enable=True,
                                   auto_bisect_enable=False)


class InternalServerError(Exception):
  """An error indicating that something unexpected happens."""

class BraveSheriffConfigClient(object):
  def Match(self, path, check=False):
    if _IGNORE_PATTERN.search(path) is not None:
      return [], None

    if _TOP_METRICS_PATTERN.search(path) is not None:
      return [_GetTopMetricsSubscription()], None
    else:
      return [_GetOtherMetricsSubscription()], None

  def List(self, check=False):
    return [_GetTopMetricsSubscription(), _GetOtherMetricsSubscription()], None

  def Update(self, check=False):
    return True, None
