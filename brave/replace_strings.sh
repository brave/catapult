#!/bin/bash
export LC_CTYPE=C
export LANG=C
files=$(find ./dashboard | egrep  "\.py|\.htm(l)?|\.js|\.css|\.yaml|\.yml|Dockerfile")
files=$(echo "$files" | egrep -v '(_|-|/)test(s)?\.py$|(_|-|/)test(s)?\.html$|/test(s)?(data)?/')

REPLACES=(
# Core changes
  "s/chromeperf/brave-perf-dashboard/g"
  "s/add-histograms-cache/brave-perf-add-histograms-cache/g"
  "s/histograms-queue/histogram-queue/g"

# UI changes
  "s/Chrome Performance/Brave Performance/g"
  "s/signed-in google.com accounts/signed-in brave.com accounts/g"

# Replace emails just in case
  "s/@google.com/@brave.com/g"
  "s/@chromium.com/@brave.com/g"
  "s/corp.google.com/invalid-domain/g"
  "s/engprod@google.com/disabled@invaliddomain/g"
  "s/alerts@google.com/disabled@invaliddomain/g"
  "s/mail.send_mail/raise NotImplementedError(\'calling send_mail\'); mail.send_mail_to_admins/g"

# Disable other .appspot.com domains
  "s/[-,a-z,A-Z,0-9,_]*.appspot.com/brave-perf-dashboard.appspot.com/g"
)
for ((i = 0; i < ${#REPLACES[@]}; i++)); do
  replace=${REPLACES[$i]}
  echo $replace
  echo -n "$files" | xargs -I{} sed -i.back "$replace" {}
done
find . -iname "*.back" | xargs rm
