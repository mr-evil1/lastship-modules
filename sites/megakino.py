# -*- coding: utf-8 -*-
import json, sys
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting, setSetting
import xbmcgui
oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'megakino'
SITE_NAME = 'Megakino'
SITE_ICON = 'megakino.png'
DOMAIN = getSetting('provider.'+ SITE_IDENTIFIER +'.domain', 'megakino.ist')
URL_MAIN = 'https://' + DOMAIN #+ '/'
URL_KINO = URL_MAIN + '/kinofilme/'
URL_MOVIES = URL_MAIN + '/films/'
URL_SERIES = URL_MAIN + '/serials/'
URL_ANIMATION = URL_MAIN + '/multfilm/'
URL_DOKU = URL_MAIN + '/documentary/'
URL_SEARCH = URL_MAIN + '?do=search&subaction=search&story=%s'

def load():
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&new=True&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Aktuelle Filme im Kino", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Animationsfilme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_ANIMATION), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Dokumentationen", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_DOKU), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showGenre&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()

def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<div\s+class="side-block__title">Genres</div>(.*?)</ul>\s*</div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    aResult = []
    if isMatch:
        pattern = 'href="([^"]+)">([^<]+)</a>'
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch: return
    for sUrl, sName in aResult:
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = '<a[^>]*class="poster grid-item.*?href="([^"]+).*?<img data-src="([^"]+).*?alt="([^"]+)".*?class="poster__label">([^<]+).*?class="poster__text[^"]+">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    for sUrl, sThumbnail, sName, sQuality, sDesc in aResult:
        if sSearchText:
            pattern = '\\b%s\\b' % sSearchText.lower()
            if not cParser().search(pattern , sName.lower()): continue
        item = {}
        if sThumbnail.startswith('/'): sThumbnail = URL_MAIN + sThumbnail
        if sUrl.startswith('//'): sUrl =  'https:' + sUrl
        isTvshow = True if 'Episode' in sQuality or 'Komplett' in sQuality else False
        if isTvshow:
            isMatch, aName = cParser.parseSingleResult(sName, '(.*?)\s+-\s+Staffel\s+(\d+)')
            if isMatch:
                infoTitle, sSE = aName
                item.setdefault('season', sSE)
            else:
                item.setdefault('season', '00')
                infoTitle = sName
            item.setdefault('infoTitle', quote_plus(infoTitle))
            item.setdefault('sFunction', 'showEpisodes')
        else:
            infoTitle = sName
            item.setdefault('infoTitle', infoTitle)
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        try: sDesc = unescape(sDesc)
        except: pass
        sDesc = sDesc.replace("\r", "").replace("\n", "")
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]{2}'.format(SITE_NAME, infoTitle, quote(sDesc)))
        items.append(item)
    xsDirectory(items, SITE_NAME)

    if bGlobal: return

    if sSearchText==None:
        pattern = '">\s*<a\s+href="([^"]+)">\D'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri(), 'next.png', 'DefaultVideo.png')

    setEndOfDirectory(sorted=False)


def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    sSeason = meta["season"]
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    pattern = 'Episode (\d+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    sThumbnail = meta["poster"]
    infoTitle = meta["infoTitle"]
    infoTitle = quote_plus(infoTitle)
    items = []
    for sEpisode in aResult:
        item = {}
        item.setdefault('title', 'Episode ' + sEpisode)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('poster', sThumbnail)
        item.setdefault('season', sSeason)
        item.setdefault('episode', sEpisode)
        item.setdefault('infoTitle', infoTitle)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def getHosters():
    isProgressDialog=True
    isResolve = True
    items = []
    sUrl = params.getValue('entryUrl')
    if sUrl.startswith('//'): sUrl = 'https:' + sUrl
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    meta = json.loads(params.getValue('meta'))
    if meta.get('isTvshow', False):
        episode = meta['episode']
        pattern = r'id="ep%s">.*?(<option.*?)</select' % episode
        isMatch, sHtmlContent = cParser().parseSingleResult(sHtmlContent, pattern)
        pattern = r'value="([^"]+)'
    else:
        pattern = 'tabs-block__content.*?src(?:="|=)(http.*?)(?:"|\s)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        sThumbnail = meta['poster']
        if meta.get('isTvshow', False):
            sTitle = meta['infoTitle'] + ' S%sE%s' % (meta['season'], meta['episode'])
            meta.setdefault('mediatype', 'tvshow')
        else:
            sTitle = meta['infoTitle']
            meta.setdefault('mediatype', 'movie')
        if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
        t = 0
        if isProgressDialog: progressDialog.update(t)

        for sUrl in aResult:
            t += 100 / len(aResult)
            sHoster = cParser.urlparse(sUrl).upper()
            if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
            if isResolve:
                isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                if isBlocked: continue
            elif isBlockedHoster(sUrl)[0]:
                continue
            items.append((sHoster, sTitle, meta, isResolve, sUrl, sThumbnail))
        if isProgressDialog:  progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)

def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search(sSearchText):
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=True)

