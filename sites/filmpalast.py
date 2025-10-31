# -*- coding: utf-8 -*-

#2024-10-10

import json, sys
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting
import xbmcgui
oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'filmpalast'
SITE_NAME = 'FilmPalast'
SITE_ICON = 'filmpalast.png'
DOMAIN = getSetting('provider.'+ SITE_IDENTIFIER +'.domain', 'filmpalast.to')
URL_MAIN = 'https://' + DOMAIN #+ '/'


URL_MOVIES = URL_MAIN + '/movies/%s'
URL_SERIES = URL_MAIN + '/serien/view'
URL_ENGLISH = URL_MAIN + '/search/genre/Englisch'
URL_SEARCH = URL_MAIN + '/search/title/%s'

def load():
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&new=True&&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultAddonsSearch.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showMovieMenu' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showSeriesMenu' % SITE_NAME, SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()

def showMovieMenu():
    addDirectoryItem("Neuesten", 'runPlugin&site=%s&function=showEntries&new=True&sUrl=%s' % (SITE_NAME, URL_MOVIES % 'new'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Hits", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES % 'top'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Votes", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES % 'votes'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("IMDB-Bewertung", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES % 'imdb'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Englisch", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_ENGLISH), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showValue&value=genre&sUrl=%s' % (SITE_NAME, URL_MOVIES % 'new'), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("A-Z", 'runPlugin&site=%s&function=showValue&value=movietitle&sUrl=%s' % (SITE_NAME, URL_MOVIES % 'new'), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()

def showSeriesMenu():
    addDirectoryItem("Neuesten", 'runPlugin&site=%s&function=showEntries&new=True&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("A-Z", 'runPlugin&site=%s&function=showValue&value=movietitle&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    setEndOfDirectory()

def showValue():
    params = ParameterHandler()
    value = params.getValue("value")
    oRequest = cRequestHandler(params.getValue('sUrl'))
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<section[^>]id="%s">(.*?)</section>' % value
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch: return
    isMatch, aResult = cParser.parse(sContainer, 'href="([^"]+)">([^<]+)')
    if not isMatch: return
    for sUrl, sName in aResult:
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultFolder.png')
    setEndOfDirectory()

def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = '<article[^>]*>\s*<a href="([^"]+)" title="([^"]+)">\s*<img src=["\']([^"\']+)["\'][^>]*>(.*?)</article>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        # will match movies from specific pages (filmpalast.to/movies/new)
        # last match is just a dummy!
        pattern = '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*<img[^>]*src=["\']([^"\']*)["\'][^>]*>\s*</a>(\s*)</article>'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        # not needed anymore???
        pattern = '</div><a[^>]href="([^"]+)"[^>]title="([^"]+)">.*?src="([^"]+)(.*?)alt'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    hName = []  # Dubletten ausfiltern
    for sUrl, sName, sThumbnail, sDummy in aResult:
        if sSearchText:
            pattern = '\\b%s\\b' % sSearchText.lower()
            if not cParser().search(pattern , sName.lower()): continue
        item = {}
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        isYear, sYear = cParser.parseSingleResult(sDummy, 'Jahr:[^>]([\d]+)')
        # isDuration, sDuration = cParser.parseSingleResult(sDummy, '[Laufzeit][Spielzeit]:[^>]([\d]+)')
        # isRating, sRating = cParser.parseSingleResult(sDummy, 'Imdb:[^>]([^<]+)')
        if sUrl.startswith('//'): sUrl =  'https:' + sUrl
        isTvshow, aName = cParser.parseSingleResult(sName, '(.*?).(S\d\dE\d\d)')

        if isTvshow:
            sName, sSE = aName
            if sName not in hName: hName.append(sName)  # Dubletten ausfiltern
            else: continue
            infoTitle = sName
            if bGlobal: sName = SITE_NAME + ' - ' + sName + ' (Serie)'
            elif params.exist('new'): sName = sName + ' ' + sSE
        else:
            infoTitle = sName
            if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)  # für "Erweiterte Info"
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        # optional
        item.setdefault('year', sYear)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, infoTitle))
        # item.setdefault('sDuration', sDuration)
        # item.setdefault('sRating', sRating)
        items.append(item)
    xsDirectory(items, SITE_NAME)

    if bGlobal: return

    if sSearchText==None:
        pattern = '<a class="pageing.*?(/page/\d+).*?vor'  # '<a class="pageing[^"]*"\s*href=([^>]+).*?vor'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            sNextUrl = entryUrl.rsplit('/page')[0] + sNextUrl
        else:
            pattern = "active...>\d.*?href='([^']+)"
            isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri(), 'next.png', 'DefaultFolder.png')

    setEndOfDirectory()

def showSeasons():
    # import pydevd
    # pydevd.settrace('localhost', port=12345, stdoutToServer=True, stderrToServer=True)
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    pattern = '<a[^>]*class="staffTab"[^>]*data-sid="(\d+)"[^>]*>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    sThumbnail = meta["poster"]
    infoTitle = meta["infoTitle"]
    infoTitle = quote_plus(infoTitle) # notwendig ??
    # optional
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '"description">([^<]+)')
    items = []
    for sSeason in aResult:
        item = {}
        item.setdefault('title', 'Staffel ' + sSeason)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('poster', sThumbnail)
        item.setdefault('season', sSeason)
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('sFunction', 'showEpisodes')
        item.setdefault('isTvshow', True)
        if isDesc: # optional
            try: sDesc = unescape(sDesc)
            except: pass
            sDesc = sDesc.replace("\r", "").replace("\n", "").replace("„", "").replace("“", "")
            item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[CR]Staffel {2}[/COLOR][CR]{3}'.format(SITE_NAME, infoTitle, sSeason, quote(sDesc)))
        else:
            item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[CR]Staffel {2}[/COLOR][CR]'.format(SITE_NAME, infoTitle, sSeason))
        items.append(item)
    xsDirectory(items, SITE_NAME)
#     cGui().setView('seasons')
    setEndOfDirectory(sorted=True)

def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    sSeason = meta["season"]
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="staffelWrapperLoop[^"]*"[^>]*data-sid="%s">(.*?)</ul></div>' % sSeason
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch: return
    pattern = 'href="([^"]+)'
    isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch: return
    sThumbnail = meta["poster"]
    infoTitle = meta["infoTitle"]
    items = []
    for sUrl in aResult:
        item = {}
        if sUrl.startswith('//'): sUrl = 'https:' + sUrl
        isMatch, sEpisode = cParser.parseSingleResult(sUrl, 'e(\d+)')
        item.setdefault('title', 'Folge ' + sEpisode)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('poster', sThumbnail)
        item.setdefault('season', int(sSeason))
        item.setdefault('episode', int(sEpisode))
        item.setdefault('infoTitle', infoTitle)
        #item.setdefault('sFunction', 'getHosters')
        item.setdefault('plot',  meta["plot"])   # optional
        items.append(item)
    xsDirectory(items, SITE_NAME)
    # cGui().setView('episodes')
    setEndOfDirectory()

def getHosters():
    isProgressDialog=True  # TODO - Wert aus settings - bei globaler Suche keinen ProgressDialog beim Plugin!
    isResolve = True  # TODO - Wert aus settings
    items = []
    # progressDialog = control.progressDialog if control.getSetting('progress.dialog') == '0' else control.progressDialogBG
    sUrl = params.getValue('entryUrl')
    if sUrl.startswith('//'): sUrl = 'https:' + sUrl
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 2
    sHtmlContent = oRequest.request()
    pattern = 'hostName">([^<]+).*?(http[^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        meta = json.loads(params.getValue('meta'))    # God's Country
        sThumbnail = meta['poster']
        if meta.get('isTvshow', False):
            sTitle = meta['infoTitle'] + ' S%sE%s' % (str(meta['season']), str(meta['episode']))
            meta.setdefault('mediatype', 'tvshow')
        else:
            sTitle = meta['infoTitle']
            meta.setdefault('mediatype', 'movie')
        if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
        t = 0
        if isProgressDialog: progressDialog.update(t)
        for sHoster, sUrl in aResult:
            t += 100 / len(aResult)
            hoster = sHoster.rstrip(' HD')
            if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + hoster.upper())
            if isResolve:
                isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                if isBlocked: continue
            elif isBlockedHoster(hoster)[0]: continue
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

