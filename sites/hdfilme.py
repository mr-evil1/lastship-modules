# -*- coding: utf-8 -*-
import json
import sys
import xbmc
import xbmcgui
import xbmcplugin
import re
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting
from resources.lib.indexers.navigatorXS import navigator

try:
    import resolveurl
except ImportError:
    resolveurl = None

oNavigator = navigator()
params = ParameterHandler()

SITE_IDENTIFIER = 'hdfilme'
SITE_NAME = 'HD Filme'
SITE_ICON = 'hdfilme.png'

DOMAIN = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'www.hdfilme.garden')
URL_MAIN = 'https://' + DOMAIN + '/'
URL_NEW = URL_MAIN + 'kinofilme-online/'
URL_KINO = URL_MAIN + 'aktuelle-kinofilme-im-kino/'
URL_SERIES = URL_MAIN + 'serienstream-deutsch/'
URL_SEARCH = URL_MAIN + 'index.php?do=search&subaction=search&story=%s'

def load1():
    oNavigator.addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW), SITE_ICON, 'DefaultMovies.png')
    oNavigator.addDirectoryItem("Kino", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO), SITE_ICON, 'DefaultMovies.png')
    oNavigator.addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&isTvshow=True&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    oNavigator.addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    oNavigator._endDirectory()




def showEntries(entryUrl=False, sSearchText=False):
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=True).request()
    pattern = '<div class="box-product(.*?)<h3.*?href="([^"]+).*?">([^<]+).*?(.*?)</li>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch: return
    for sInfo, sUrl, sName, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName): continue
        isThumbnail, sThumbnail = cParser().parseSingleResult(sInfo, 'data-src="([^"]+)')
        if isThumbnail and sThumbnail.startswith('/'): sThumbnail = URL_MAIN + sThumbnail
        u = 'runPlugin&site=%s&function=getHosters&sUrl=%s&sThumbnail=%s&sTitle=%s' % (
            SITE_NAME, quote_plus(sUrl if sUrl.startswith('http') else URL_MAIN + sUrl.lstrip('/')),
            quote_plus(sThumbnail), quote_plus(sName)
        )
        oNavigator.addDirectoryItem(sName, u, sThumbnail, 'DefaultVideo.png')
    isMatchNext, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'href="([^"]+)">›</a>')
    if isMatchNext:
        oNavigator.addDirectoryItem('>>> Nächste Seite', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), SITE_ICON, 'DefaultMovies.png')
    oNavigator._endDirectory()

def getHosters():
    sUrl = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTitle = params.getValue('sTitle')
    sHtmlContent = cRequestHandler(sUrl).request()
    patterns = [
        'link="([^"]+)',
        'data-link="([^"]+)',
        'data-video="([^"]+)',
        'src="([^"]+)'
    ]
    found_links = []
    for p in patterns:
        isMatch, results = cParser().parse(sHtmlContent, p)
        if isMatch:
            found_links.extend(results)
    if not found_links:
        xbmcgui.Dialog().notification(SITE_NAME, "Keine Links gefunden", SITE_ICON, 3000)
        return
    progressDialog.create(SITE_NAME, 'Prüfe Hoster...')
    processed_links = list(set(found_links))
    total = len(processed_links)
    valid_found = False
    exclude = ['youtube', 'youtu.be', 'trailer', 'facebook', 'gstatic', '.ttf', '.woff', '.svg', '.css', '.js']

    for i, hUrl in enumerate(processed_links):
        if progressDialog.iscanceled(): break
        if hUrl.startswith('//'): hUrl = 'https:' + hUrl
        hUrl_lower = hUrl.lower()
        if any(x in hUrl_lower for x in exclude): continue
        if 'embed-.html' in hUrl_lower: continue
        if resolveurl and resolveurl.HostedMediaFile(hUrl).valid_url():
            valid_found = True
            hName = hUrl.split('/')[2].replace('www.', '').split('.')[0].capitalize()
            u = 'runPlugin&site=%s&function=play&sUrl=%s&sTitle=%s' % (SITE_NAME, quote_plus(hUrl), quote_plus(sTitle))
            oNavigator.addDirectoryItem(hName, u, sThumbnail, 'DefaultVideo.png', isFolder=False)
        progressDialog.update(int((i / total) * 100))
    progressDialog.close()
    if not valid_found:
        xbmcgui.Dialog().notification(SITE_NAME, "Keine validen Streams", SITE_ICON, 3000)
    oNavigator._endDirectory()

def play():
    sUrl = params.getValue('sUrl')
    sTitle = params.getValue('sTitle')
    if not resolveurl:
        xbmcgui.Dialog().notification(SITE_NAME, "ResolveURL fehlt!", SITE_ICON, 5000)
        return
    progressDialog.create(SITE_NAME, 'Löse Stream auf...')
    stream_url = None
    try:
        stream_url = resolveurl.resolve(sUrl)
    except Exception as e:
        logger.info("ResolveURL Error: %s" % str(e))
        progressDialog.close()
        xbmcgui.Dialog().notification(SITE_NAME, "Hoster-Fehler (404/Timeout)", SITE_ICON, 5000)
        return
    progressDialog.close()
    if stream_url:
        listItem = xbmcgui.ListItem(sTitle)
        listItem.setPath(stream_url)
        # Wiedergabe für Kodi 21
        xbmc.Player().play(stream_url, listItem)
    else:
        xbmcgui.Dialog().notification(SITE_NAME, "Stream nicht gefunden", SITE_ICON, 5000)

def showSearch():
    text = oNavigator.showKeyBoard()
    if text:
        showEntries(URL_SEARCH % quote_plus(text), text)
