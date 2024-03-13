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


_CHECK_INTERVAL = datetime.timedelta(minutes=1)
_BRAVE_SHERRIF = 'Top metrics'

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
  _, _ , count = anomaly.Anomaly.QueryAsync(
      keys_only=True,
      limit=1000,
      recovered=False,
      subscriptions=[_BRAVE_SHERRIF],
      is_improvement=False,
      bug_id='', # untriaged
      min_timestamp=min_timestamp_to_check)
  logging.info('untriaged count %s', count)
  return count

def MaybeSendEmail():
  LAST_CHECK_KEY = 'brave_last_anomaly_check_timestamp'
  BRAVE_EMAILS_TO_NOTIFY_KEY = 'brave_emails_to_notify'
  now = datetime.datetime.now()
  last_checked = stored_object.Get(LAST_CHECK_KEY) or None
  if last_checked is not None:
    delta = now - last_checked
    logging.info('Time delta %s', delta)
    if delta < _CHECK_INTERVAL:
      return
  stored_object.Set(LAST_CHECK_KEY, now)

  count = _GetUntriagedAnomaliesCount(last_checked)
  if count == 0:
    return

  emails = stored_object.Get(BRAVE_EMAILS_TO_NOTIFY_KEY)
  if emails is None:
    logging.error('No emails to notify')
    return

  query = urlencode({'sheriff': _BRAVE_SHERRIF})
  body = f'Visit https://brave-perf-dashboard.appspot.com/alerts?{query} for details'

  mail.send_mail(
      sender='perf-alerts@brave.com',
      to=emails,
      subject=f'New perf {count} alert(s) detected',
      body=body)
  logging.info('Sent a mail to %s', emails)
