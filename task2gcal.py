from __future__ import print_function
import os
import json
import re

import datetime
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Export pending tasks from taskwarrior
stream = os.popen('task status:pending export')
tasks = stream.read()
tasks = re.match('\[[\s\S]*\]', tasks, re.I | re.M | re.A).group(0)
tasks = json.loads(tasks)

# Set up GCal

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('calendar', 'v3', credentials=creds)


# Look for the latest due date from the pending tasks
now = datetime.datetime.utcnow()
latest = now

for task in tasks:
    due_timestamp = task.get('due')

    if due_timestamp:
        due = datetime.datetime.strptime(due_timestamp, '%Y%m%dT%H%M%SZ')

        if due > latest:
            latest = due

latest_string = latest.isoformat() + 'Z'
now_string = now.isoformat() + 'Z'

events_results = service.events().list(calendarId='primary', timeMin=now_string, timeMax=latest_string).execute()

events = events_results.get('items', [])

# TODO: Add event's id to task to keep track of them. If no id, assume it hasn't been created yet. If there's an id
# TODO: update that one. We shouldnt need to pull them all...


for event in events:
    print(event.get('summary'))


