#!/usr/bin/python
# -*- coding: utf-8 -*-

import httplib2
import os
import sys
import urllib2
import re

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from bs4 import BeautifulSoup

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

TOP40_URL = "http://www.m-1.fm/top40/"

def searchSong(api, title):
  """Searches for song video.

  Args:
    title: Author and song title
  Returns
    ResourceId object returned by Youtube
  """
  try:
    search_response = api.search().list(
      q=title,
      part="id",
      maxResults=1,
      type="video",
    ).execute()

    return search_response.get("items", [])[0]["id"]
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

def retrieveM1Songs(url):
  """Parses URL and returns titles of TOP40 songs

  Args:
    url: address where TOP40 lies
  Returns:
    TOP40 date
    Array with all 40 songs
  """
  songs = []
  soup = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')
  for song in soup.find(id="topvote").find_all(id=re.compile("^title_*")):
    songs += [song.text]
  return soup.find(attrs={"name": "topid"}).find(selected=True).text, songs[:40] #Remove song candidates

def authorise():
  """Authorises credentials

  Returns:
    Youtube data API object
  """
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
  message=MISSING_CLIENT_SECRETS_MESSAGE,
  scope=YOUTUBE_READ_WRITE_SCOPE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    flags = argparser.parse_args()
    credentials = run_flow(flow, storage, flags)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))

def createPlaylist(api, date, description):
  """Creates empty playlist

  Args:
    api: Youtube API object
    date: Date when TOP40 happened
    description: Playlist description
  """
  playlists_insert_response = api.playlists().insert(
    part="snippet,status",
    body=dict(
      snippet=dict(
        title=u"M-1 TOP 40 Grojaraštis " + date,
        description=description
      ),
      status=dict(
        privacyStatus="private"
      )
    )
  ).execute()
  return playlists_insert_response["id"]

def addSongToPlaylist(api, playlist, song, rank):
  """Append song to the playlist

  Args:
    api: Youtube API object
    playlist: Youtube playlist id object
    song: Youtube video id object
    rank: Song's rank in TOP40
  """
  try:
    api.playlistItems().insert(
      part="snippet,contentDetails",
      body=dict(
        snippet=dict(
          playlistId=playlist,
          resourceId=song
        ),
        contentDetails=dict(
          note="%d-a vieta" % rank,
        )
      )
    ).execute()
  except HttpError, e:
    print "Failed to add video %s to playlist %s\n Error %d occured: %s" \
          % (song, playlist, e.resp.status, e.content)


def createFullPlaylist(url):
  """Creates playlist and fills it with TOP40 songs

  Args:
    url: TOP40 source
  """
  youtube = authorise()

  #Retrieve songs from M-1
  date, songs = retrieveM1Songs(url)
  print "Retrieved songs from radio website."

  newPlaylist = createPlaylist(youtube, date, url)
  print "Created empty playlist %s." % newPlaylist

  #Search songs on Youtube
  videos = [searchSong(youtube, song) for song in songs]
  print "Finished songs search."

  #Add songs to the playlist
  for i, video in enumerate(videos):
    addSongToPlaylist(youtube, newPlaylist, video, i+1)
  print "Finished adding songs to a playlist."

if __name__ == "__main__":
  createFullPlaylist(TOP40_URL)
