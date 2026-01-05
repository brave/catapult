# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from telemetry.core import exceptions
from telemetry.testing import browser_test_case


UNCLOSEABLE_URLS = ['chrome://reload-button']


class TabTestCase(browser_test_case.BrowserTestCase):
  def __init__(self, *args):
    super().__init__(*args)
    self._tab = None

  def setUp(self):
    super().setUp()

    if self._browser.supports_tab_control:
      try:
        # Identify a valid test tab and close any extra tabs,
        # while explicitly ignoring the WaaP Reload Button WebUI.
        test_tab = None
        tabs_to_close = []
        for tab in self._browser.tabs:
          # Skip the uncloseable links.
          if any(url in tab.url for url in UNCLOSEABLE_URLS):
            continue
          if test_tab is None:
            test_tab = tab
          else:
            tabs_to_close.append(tab)

        # Close all extra testable tabs
        for tab in tabs_to_close:
          tab.Close()

        # If no usable tab was found (e.g. only WebUI existed), create one
        if test_tab is None:
          self._browser.tabs.New()
          # The new tab is essentially the last one, search in reverse.
          for tab in reversed(self._browser.tabs):
            if not any(url in tab.url for url in UNCLOSEABLE_URLS):
              test_tab = tab
              break
        self._tab = test_tab
      except exceptions.TimeoutException:
        self._RestartBrowser()
    else:
      self._RestartBrowser()
    self._tab.WaitForDocumentReadyStateToBeInteractiveOrBetter()
    self._tab.Navigate('about:blank')

  def Navigate(self,
               filename,
               script_to_evaluate_on_commit=None,
               handler_class=None):
    """Navigates |tab| to |filename| in the unittest data directory.

    Also sets up http server to point to the unittest data directory.
    """
    url = self.UrlOfUnittestFile(filename, handler_class)
    self._tab.Navigate(url, script_to_evaluate_on_commit)
    self._tab.WaitForDocumentReadyStateToBeComplete()
    self._tab.WaitForFrameToBeDisplayed()

  def _RestartBrowser(self):
    if not self._browser.tabs:
      self.tearDownClass()
      self.setUpClass()
    self._tab = self._browser.tabs[0]

  @property
  def tabs(self):
    return self._browser.tabs
