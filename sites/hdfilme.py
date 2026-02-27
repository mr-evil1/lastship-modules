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


def load():
    oNavigator.addDirectoryItem("Neu",    'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW),    SITE_ICON, 'DefaultMovies.png')
    oNavigator.addDirectoryItem("Kino",   'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO),   SITE_ICON, 'DefaultMovies.png')
    oNavigator.addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&isTvshow=True&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    oNavigator.addDirectoryItem("Suche",  'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    oNavigator._endDirectory()


def showEntries(entryUrl=False, sSearchText=False):
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    isTvshow = params.getValue('isTvshow')

    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=True).request()
    pattern = '<div class="box-product(.*?)<h3.*?href="([^"]+).*?">([^<]+).*?(.*?)</li>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        oNavigator._endDirectory()
        return

    # xsDirectory statt addDirectoryItem → vollständiges Kontextmenü
    # navigatorXS.py muss isFolder=True für getHosters-Items setzen (siehe Fix)
    items = []
    for sInfo, sUrl, sName, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isThumbnail, sThumbnail = cParser().parseSingleResult(sInfo, 'data-src="([^"]+)')
        if isThumbnail and sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        full_url = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl.lstrip('/')
        items.append({
            'title':     sName,
            'infoTitle': sName,
            'entryUrl':  full_url,
            'sUrl':      full_url,
            'poster':    sThumbnail,
            # isTvshow=True erzwingt isFolder=True in xsDirectory →
            # getHosters bekommt echten Handle statt -1
            'isTvshow':  True,
            'sFunction': 'getHosters',
        })

    oNavigator.xsDirectory(items, SITE_NAME)

    isMatchNext, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'href="([^"]+)">›</a>')
    if isMatchNext:
        oNavigator.addDirectoryItem('>>> Nächste Seite',
            'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl),
            SITE_ICON, 'DefaultMovies.png')
    oNavigator._endDirectory()


def getHosters():
    # Läuft jetzt mit echtem Handle (isTvshow=True → isFolder=True in xsDirectory)
    sUrl = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTitle = params.getValue('sTitle')
    sMeta = params.getValue('meta') or ''

    # meta-Fallback: xsDirectory übergibt Parameter als JSON in 'meta'
    if not sUrl:
        if sMeta:
            try:
                meta = json.loads(sMeta)
            except Exception:
                meta = {}
            sUrl       = meta.get('entryUrl') or meta.get('sUrl') or ''
            sThumbnail = sThumbnail or meta.get('poster') or ''
            sTitle     = sTitle or meta.get('infoTitle') or meta.get('title') or ''

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
        oNavigator._endDirectory()
        return

    progressDialog.create(SITE_NAME, 'Prüfe Hoster...')
    processed_links = list(set(found_links))
    total = len(processed_links)
    exclude = ['youtube', 'youtu.be', 'trailer', 'facebook', 'gstatic', '.ttf', '.woff', '.svg', '.css', '.js']

    # showHosters-Format: [sHosterName, sTitle, meta, isResolve, sUrl, sThumbnail]
    hosters = []
    for i, hUrl in enumerate(processed_links):
        if progressDialog.iscanceled(): break
        if hUrl.startswith('//'): hUrl = 'https:' + hUrl
        if not hUrl.startswith('http'): continue
        if any(x in hUrl.lower() for x in exclude): continue
        if 'embed-.html' in hUrl.lower(): continue
        if resolveurl and resolveurl.HostedMediaFile(hUrl).valid_url():
            hName = hUrl.split('/')[2].replace('www.', '').split('.')[0].capitalize()
            hosters.append([hName, sTitle, sMeta, False, hUrl, sThumbnail])
        progressDialog.update(int((i / total) * 100))

    progressDialog.close()
    oNavigator.showHosters(json.dumps(hosters))


def showSearch():
    text = oNavigator.showKeyBoard()
    if text:
        showEntries(URL_SEARCH % quote_plus(text), text)
