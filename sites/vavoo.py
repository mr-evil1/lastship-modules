import json, sys,xbmcgui,re
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
SITE_IDENTIFIER = 'vavoo'
SITE_NAME = 'Vavoo'
SITE_ICON = 'vavoo.png'
import xbmcgui
def load():
    xbmcgui.Dialog().notification('xStreamV2','Noch nicht im xStream V2 verfügbar')
