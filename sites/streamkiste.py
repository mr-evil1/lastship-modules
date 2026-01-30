# -*- coding: utf-8 -*-
import json, sys
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting, setSetting
oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()
import base64
import binascii
import hashlib
import re,xbmcgui
import json
from resources.lib import pyaes
from itertools import zip_longest as ziplist

SITE_IDENTIFIER = 'streamkiste'
SITE_NAME = 'Streamkiste'
SITE_ICON = 'streamkiste.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'streamkiste.taxi')
import xbmcgui
def load():
    xbmcgui.Dialog().notification('xStreamV2','Noch nicht im xStream V2 verfügbar')
