#!/bin/sh
# This script will backup the data files used by the bot, everyday at 2AM (once a cronjob has been established).
# The cron task should be:
# 0 2 * * * PATH/TO/XmasLootBox/backup.sh >/dev/null 2>&1
# Note: The >/dev/null 2>&1 will prevent it from sending an email everytime it is run
#
# Setup:
# 1. Run: crontab -e
# 2. Add: (crontask above)
set -e

timestamp=`date '+%Y%m%d%H%M'`
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

mkdir -p $SCRIPTPATH/bkups

ACCOUNTS="accounts.json"
TS_ACCOUNTS="$timestamp-$ACCOUNTS"
cp "$SCRIPTPATH/$ACCOUNTS" "$SCRIPTPATH/bkups/$TS_ACCOUNTS"

HISTORY="history.json"
TS_HISTORY="$timestamp-$HISTORY"
cp "$SCRIPTPATH/$HISTORY" "$SCRIPTPATH/bkups/$TS_HISTORY"

OWNERS="owners.json"
TS_OWNERS="$timestamp-$OWNERS"
cp "$SCRIPTPATH/$OWNERS" "$SCRIPTPATH/bkups/$TS_OWNERS"

RARITIES="rarities.json"
TS_RARITIES="$timestamp-$RARITIES"
cp "$SCRIPTPATH/$RARITIES" "$SCRIPTPATH/bkups/$TS_RARITIES"

NEXT_ID="next_id"
TS_NEXT_ID="$timestamp-$NEXT_ID"
cp "$SCRIPTPATH/$NEXT_ID" "$SCRIPTPATH/bkups/$TS_NEXT_ID"
