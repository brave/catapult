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

from flask import request

from google.appengine.ext import ndb
from google.appengine.api import mail

from six.moves.urllib.parse import urlencode

from dashboard.models import anomaly, graph_data
from dashboard.common import stored_object, datastore_hooks, utils
import dashboard.brave_sheriff_config_client as brave_sheriff


_LAST_TOTAL_CHECK_KEY = 'brave_anomaly_new_check_timestamp'
_BRAVE_EMAILS_TO_NOTIFY_KEY = 'brave_emails_to_notify'

def GetBraveCoreRevision(test_key, revision_number):
  try:
    row_parent_key = utils.GetTestContainerKey(test_key)
    direct_row = graph_data.Row.get_by_id(revision_number, parent=row_parent_key)
    if direct_row and hasattr(direct_row, 'a_brave_tag'):
      return direct_row.a_brave_tag
    else:
      logging.warning('Empty brave tag for %s, %s, %s, %s', test_key, row_parent_key, revision_number, direct_row)
  except Exception as e:
    logging.warning('Error querying row %s, %s: %s', test_key, revision_number, e)
  return None

def FindBraveCoreRevision(row_tuples, revision_number):
  for revision, row, _ in row_tuples:
    if revision == revision_number:
      return GetBraveCoreRevision(row.key, revision_number)
  return None

def _GetUntriagedAnomaliesCount(min_timestamp, max_timestamp):
  """Fetches recent untriaged anomalies asynchronously from all sheriffs."""
  # Previous code process anomalies by sheriff with LIMIT. It prevents some
  # extreme cases that anomalies produced by a single sheriff prevent other
  # sheriff's anomalies being processed. But it introduced some unnecessary
  # complex to system and considered almost impossible happened.
  logging.info('Fetching untriaged anomalies fired %s - %s',
               min_timestamp, max_timestamp)
  keys, _ , _ = anomaly.Anomaly.QueryAsync(
      keys_only=True,
      limit=1000,
      recovered=False,
      subscriptions=[brave_sheriff.BRAVE_TOP_METRICS_SHERRIF],
      is_improvement=False,
      bug_id='', # untriaged
      max_timestamp=max_timestamp,
      min_timestamp=min_timestamp).get_result()
  logging.info('Got keys %s', keys)
  return len(keys)

def _SendEmail(subject):
  emails = stored_object.Get(_BRAVE_EMAILS_TO_NOTIFY_KEY)
  if emails is None:
    logging.error('No emails to notify')
    return

  query = urlencode({'sheriff': brave_sheriff.BRAVE_TOP_METRICS_SHERRIF})
  body = f'Visit <a href="https://brave-perf-dashboard.appspot.com/alerts?{query}">the Brave Performance Dashboard</a> for details'

  mail.send_mail(
      sender='alerts@brave-perf-dashboard.appspotmail.com',
      to=emails,
      subject=subject,
      body=body,
      html=body)
  logging.info('Sent a mail to %s', emails)

def MaybeSendEmail():
  datastore_hooks.SetPrivilegedRequest()
  force = request.values.get('force') == 'true'
  now = datetime.datetime.now()

  total = _GetUntriagedAnomaliesCount(None, None)
  if total > 0:
    _SendEmail(f'{total} perf alert(s) need to be processed')
    stored_object.Set(_LAST_TOTAL_CHECK_KEY, now)
