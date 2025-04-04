# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Processes tests and creates new Anomaly entities.

This module contains the ProcessTest function, which searches the recent
points in a test for potential regressions or improvements, and creates
new Anomaly entities.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging
import datetime

from google.appengine.ext import ndb
from google.appengine.api import mail

from six.moves.urllib.parse import urlencode

from dashboard.models import anomaly
from dashboard.common import stored_object
import dashboard.brave_sheriff_config_client as brave_sheriff


_NEW_CHECK_INTERVAL = datetime.timedelta(days=1)
_TOTAL_CHECK_INTERVAL = datetime.timedelta(days=3)

_LAST_TOTAL_CHECK_KEY = 'brave_anomaly_new_check_timestamp'
_BRAVE_EMAILS_TO_NOTIFY_KEY = 'brave_emails_to_notify'

def GetBraveCoreRevision(row_tuples, revision_number):
  for _, row, _ in row_tuples:
    if row.revision == revision_number:
      if hasattr(row, 'a_brave_tag') and row.a_brave_tag:
        return row.a_brave_tag
  return None

def _GetUntriagedAnomaliesCount(min_timestamp_to_check):
  """Fetches recent untriaged anomalies asynchronously from all sheriffs."""
  # Previous code process anomalies by sheriff with LIMIT. It prevents some
  # extreme cases that anomalies produced by a single sheriff prevent other
  # sheriff's anomalies being processed. But it introduced some unnecessary
  # complex to system and considered almost impossible happened.
  logging.info('Fetching untriaged anomalies fired after %s',
               min_timestamp_to_check)
  keys, _ , _ = anomaly.Anomaly.QueryAsync(
      keys_only=True,
      limit=1000,
      recovered=False,
      subscriptions=[brave_sheriff.BRAVE_TOP_METRICS_SHERRIF],
      is_improvement=False,
      bug_id='', # untriaged
      min_timestamp=min_timestamp_to_check).get_result()
  logging.info('Got keys %s', keys)
  return len(keys)

def _SendEmail(subject):
  emails = stored_object.Get(_BRAVE_EMAILS_TO_NOTIFY_KEY)
  if emails is None:
    logging.error('No emails to notify')
    return

  query = urlencode({'sheriff': brave_sheriff.BRAVE_TOP_METRICS_SHERRIF})
  body = f'Visit https://brave-perf-dashboard.appspot.com/alerts?{query} for details'

  mail.send_mail(
      sender='alerts@brave-perf-dashboard.appspotmail.com',
      to=emails,
      subject=subject,
      body=body)
  logging.info('Sent a mail to %s', emails)

def MaybeSendEmail():
  now = datetime.datetime.now()

  new_count = _GetUntriagedAnomaliesCount(now - _NEW_CHECK_INTERVAL)
  if new_count > 0:
    _SendEmail(f'New {new_count} perf alert(s) detected')
    stored_object.Set(_LAST_TOTAL_CHECK_KEY, now)
    return

  last_total_checked = stored_object.Get(_LAST_TOTAL_CHECK_KEY)
  if last_total_checked is not None:
    delta = now - last_total_checked
  else:
    delta = _TOTAL_CHECK_INTERVAL
  logging.info('Total check delta %s', delta)
  if delta >= _TOTAL_CHECK_INTERVAL:
    stored_object.Set(_LAST_TOTAL_CHECK_KEY, now)
    total = _GetUntriagedAnomaliesCount(None)
    if total > 0:
      _SendEmail(f'Perf {total} alert(s) need to be processed')
