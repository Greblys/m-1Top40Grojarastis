__author__ = 'lukas'

import urllib2
from bs4 import BeautifulSoup
from createPlaylist import createFullPlaylist

TOP40_URL = "http://www.m-1.fm/top40/?topid=%s"

soup = BeautifulSoup(urllib2.urlopen(TOP40_URL).read(), 'lxml')
for option in reversed(soup.find(attrs={"name": "topid"}).findAll("option")):
  createFullPlaylist(TOP40_URL % option["value"])