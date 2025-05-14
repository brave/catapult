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

_METRICS_PATTERN_HALF_PERCENT = re.compile('|'.join([
  # apk total size:
  'apk_size/(TransferSize|InstallSize)',

  # Process number
  'ChildProcess.Launched.UtilityProcessHash#count',
  'all_processes:process_count',
]))

# Metrics that are stable and tolerate to small min_relative_change.
_METRICS_PATTERN_3_PERCENT = re.compile('|'.join([
    # Memory:
    'reported_by_chrome:allocated_objects_size/',
]))

_METRICS_PATTERN_5_PERCENT = re.compile('|'.join([
    # Memory:
    'reported_by_os:private_footprint_size/',

    # CPU:
    'cpuTime:',

    # speedometer3:
    'speedometer3/Score',

    # jetstream2:
    'jetstream2/Score',

    # Motionmark:
    'rendering.(desktop|mobile)/motionmark/',

    'rectsBasedSpeedIndex',

    # Startup
    'Startup.FirstWebContents.MainNavigationStart',
    'startup/navigationStart',
    'system_health.common_(desktop|mobile)/navigationStart',

    # Page loading:
    'timeToOnload/',
    'timeToInteractive/',
    'timeToFirstMeaningfulPaint/',
    'cpuTimeToFirstMeaningfulPaint/',

    # apk install breakdown:
    'apk_size/InstallBreakdown',
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

_ONLINE_METRICS_PATTERN = re.compile('|'.join([
  '^BravePerf/mac-mini-x64-online/',
]))

def _GetAnomalyConfigs(min_relative_change: float):
  config = subscription.AnomalyConfig()
  config.min_segment_size = 2
  config.min_relative_change = min_relative_change
  return [config]

def _GetSubscription(name: str, min_relative_change: float):
  return subscription.Subscription(name=name,
                                   monorail_project_id='brave-browser',
                                   anomaly_configs = _GetAnomalyConfigs(min_relative_change),
                                   visibility = subscription.VISIBILITY.PUBLIC,
                                   auto_triage_enable=True,
                                   auto_bisect_enable=False)

def _GetTopMetricsSubscription(min_relative_change: float = 0.05):
  return _GetSubscription(BRAVE_TOP_METRICS_SHERRIF, min_relative_change)

def _GetOtherMetricsSubscription():
  return _GetSubscription('Brave Sheriff', 0.05)


class InternalServerError(Exception):
  """An error indicating that something unexpected happens."""

class BraveSheriffConfigClient(object):
  def Match(self, path, check=False):
    if _IGNORE_PATTERN.search(path) is not None:
      return [], None

    if _ONLINE_METRICS_PATTERN.search(path) is None:  # online use < 5% accuracy
      if _METRICS_PATTERN_HALF_PERCENT.search(path) is not None:
        return [_GetTopMetricsSubscription(0.005)], None
      if _METRICS_PATTERN_3_PERCENT.search(path) is not None:
        return [_GetTopMetricsSubscription(0.03)], None

    if _METRICS_PATTERN_5_PERCENT.search(path) is not None:
      return [_GetTopMetricsSubscription(0.05)], None
    return [_GetOtherMetricsSubscription()], None

  def List(self, check=False):
    return [_GetTopMetricsSubscription(), _GetOtherMetricsSubscription()], None

  def Update(self, check=False):
    return True, None
