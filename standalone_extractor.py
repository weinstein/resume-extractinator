#!/usr/bin/python

import httplib2
import email_util

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from zipfile import ZipFile


# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'auth/client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

credentials = run(flow, STORAGE, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1', http=http)

helper = email_util.ResumeAttachmentHelper(gmail_service)
helper.resumes_to_zip('me', ZipFile('/tmp/resumes.zip', 'w'))
