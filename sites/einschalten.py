# -*- coding: utf-8 -*-

#2024-10-20 - FIXED VERSION V4 - MINIMAL

import json, sys,xbmcgui,re
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()


SITE_IDENTIFIER = 'einschalten'
SITE_NAME = 'Einschalten'
SITE_ICON = 'einschalten.png'
DOMAIN = getSetting('provider.'+ SITE_IDENTIFIER +'.domain', 'einschalten.in')
URL_MAIN = 'https://' + DOMAIN

URL_NEW_MOVIES = URL_MAIN + '/movies'
URL_LAST_MOVIES = URL_MAIN + '/movies?order=added'
URL_COLLECTIONS = URL_MAIN + '/collections'
URL_GENRES = URL_MAIN + '/genres'
URL_SEARCH = URL_MAIN + '/search?query=%s'
URL_THUMBNAIL = URL_MAIN + '/api/image/poster'


def load():
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Neue Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW_MOVIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Neu hinzugefügt", 'runPlugin&site=%s&function=showEntriesLast&sUrl=%s' % (SITE_NAME, URL_LAST_MOVIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Collectionen", 'runPlugin&site=%s&function=showCollections&sUrl=%s' % (SITE_NAME, URL_COLLECTIONS), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showGenre' % SITE_NAME, SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showGenre():
    """Zeigt Genre-Liste"""
    oRequest = cRequestHandler(URL_GENRES)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    
    # Pattern für Genre-Liste (nur id und name)
    pattern = '{"id":([^,"]+).*?name":"([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    
    if not isMatch:
        setEndOfDirectory()
        return
    
    for sUrl, sName in aResult:
        entryUrl = URL_NEW_MOVIES + '?genre=' + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showGenreEntries&sUrl=%s' % (SITE_NAME, entryUrl), SITE_ICON, 'DefaultGenre.png')
    
    setEndOfDirectory()


def showGenreEntries(entryUrl=False, sSearchText=None):
    """Zeigt Filme in einem Genre"""
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + '&page=' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(True))
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    # Pattern für Filme
    pattern = '{"id":([^,"]+).*?title":"([^"]+).*?Date":"([^-]+).*?"posterPath":"([^"]+).*?collectionId":([^}]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    
    if not isMatch:
        setEndOfDirectory()
        return
    
    items = []
    total = len(aResult)
    for sUrl, sName, sYear, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        
        item = {}
        thumbnail = URL_THUMBNAIL + sThumbnail
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('poster', thumbnail)
        item.setdefault('infoTitle', sName)
        item.setdefault('year', sYear)
        item.setdefault('isTvshow', False)
        item.setdefault('thumbnail', thumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    
    if sSearchText == None:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('sUrl', entryUrl)
        params.setParam('page', int(sPageNr))
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri()+'&page='+str(sPageNr), 'next.png', 'DefaultVideo.png')
    
    setEndOfDirectory()


def showEntries(entryUrl=False, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + '?page=' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(True))
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    # JSON Pattern
    pattern = '{"id":([^,"]+).*?title":"([^"]+).*?Date":"([^-]+).*?"posterPath":"([^"]+).*?collectionId":([^}]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        return
    
    items = []
    total = len(aResult)
    for sUrl, sName, sYear, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        if sSearchText:
            pattern = '\\b%s\\b' % sSearchText.lower()
            if not cParser().search(pattern , sName.lower()): continue
      
        isCollections, aResult2 = cParser.parse(sDummy, 'null')
        if isCollections:
            item = {}
            sThumbnail = URL_THUMBNAIL + sThumbnail
            isTvshow=False
            infoTitle = sName
            if bGlobal: sName = SITE_NAME + ' - ' + sName
            item.setdefault('infoTitle', infoTitle)
            item.setdefault('year', sYear)
            item.setdefault('title', sName)
            item.setdefault('entryUrl', sUrl)
            item.setdefault('isTvshow', isTvshow)
            item.setdefault('poster', sThumbnail)
            item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
            items.append(item)
        else:
            # Collection - zeige als Ordner an
            sThumbnail = URL_THUMBNAIL + sThumbnail
            infoTitle = sName
            if bGlobal: sName = SITE_NAME + ' - ' + sName
            plot = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
            # Rufe showCollectionEntries auf (nicht showCollections!)
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showCollectionEntries&sUrl=%s' % (SITE_NAME, sUrl), sThumbnail, 'DefaultFolder.png', plot=plot)

    try:
        xsDirectory(items, SITE_NAME)
    except:pass

    if bGlobal: return
    sPageNr = int(params.getValue('page'))

    if sSearchText == None:
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('sUrl', entryUrl)
        params.setParam('page', int(sPageNr))
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri()+'&page='+str(sPageNr), 'next.png', 'DefaultVideo.png')
    setEndOfDirectory()


def showEntriesLast(entryUrl=False, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    entryUrl=entryUrl + '&page=' + str(iPage) if iPage > 0 else entryUrl
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(True))
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    # JSON Pattern
    pattern = '{"id":([^,"]+).*?title":"([^"]+).*?Date":"([^-]+).*?"posterPath":"([^"]+).*?collectionId":([^}]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        return
    
    items = []
    total = len(aResult)
   
    for sUrl, sName, sYear, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        if sSearchText:
            pattern = '\\b%s\\b' % sSearchText.lower()
            if not cParser().search(pattern , sName.lower()): continue
        
        item = {}
        sThumbnail = URL_THUMBNAIL + sThumbnail
        isTvshow=False
        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('year', sYear)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
        items.append(item)

    xsDirectory(items, SITE_NAME)

    if bGlobal: return
    sPageNr = int(params.getValue('page'))

    if sSearchText == None:
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('sUrl', entryUrl)
        params.setParam('page', int(sPageNr))
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri()+'&page='+str(sPageNr), 'next.png', 'DefaultVideo.png')
    setEndOfDirectory()


def showCollections(entryUrl=False, sSearchText=None):
    """Zeigt LISTE von Collections an"""
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + '?page=' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(True))
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    # Pattern für Collections-Liste (verwendet "name" statt "title")
    pattern = '{"id":([^,"]+).*?name":"([^"]+).*?"posterPath":"([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        setEndOfDirectory()  # WICHTIG!
        return
    
    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        
        thumbnail = URL_THUMBNAIL + sThumbnail
        plot = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
        
        # Rufe showCollectionEntries auf um Filme in der Collection anzuzeigen
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showCollectionEntries&sUrl=%s' % (SITE_NAME, sUrl), thumbnail, 'DefaultFolder.png', plot=plot)
    
    if sSearchText == None:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('sUrl', entryUrl)
        params.setParam('page', int(sPageNr))
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri()+'&page='+str(sPageNr), 'next.png', 'DefaultVideo.png')
    
    setEndOfDirectory()


def showCollectionEntries(entryUrl=False, sSearchText=None):
    """Zeigt FILME in einer Collection an"""
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    
    # URL für Collection-Einträge
    sUrl = URL_COLLECTIONS + '/' + entryUrl
    oRequest = cRequestHandler(sUrl, ignoreErrors=(True))
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    # Pattern für Filme (verwendet "title")
    pattern = '{"id":([^,"]+).*?title":"([^"]+).*?Date":"([^-]+).*?"posterPath":"([^"]+).*?collectionId":([^}]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        setEndOfDirectory()  # WICHTIG!
        return
    
    total = len(aResult)
    items = []
    for sUrl, sName, sYear, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        
        item = {}
        thumbnail = URL_THUMBNAIL + sThumbnail
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('poster', thumbnail)
        item.setdefault('infoTitle', sName)
        item.setdefault('year', sYear)
        item.setdefault('isTvshow', False)
        item.setdefault('thumbnail', thumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters():
    logger.info('[EINSCHALTEN] === getHosters START ===')
    params = ParameterHandler()
    items = []
    
    try:
        meta = json.loads(params.getValue('meta'))
        entryUrl = params.getValue('entryUrl')
        
        # URL konstruieren
        sUrl = URL_MAIN + '/api/movies/' + entryUrl + '/watch'
        logger.info('[EINSCHALTEN] API URL: %s' % sUrl)
        
        # API Request
        sHtmlContent = cRequestHandler(sUrl, caching=False).request()
        logger.info('[EINSCHALTEN] Response Length: %d' % len(sHtmlContent))
        logger.info('[EINSCHALTEN] Response Preview: %s' % sHtmlContent[:200])
        
        # Pattern matchen
        pattern = r'streamUrl":"([^"]+)'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
        
        logger.info('[EINSCHALTEN] Pattern Match: %s' % str(isMatch))
        logger.info('[EINSCHALTEN] Results Count: %d' % (len(aResult) if aResult else 0))
        
        if not isMatch or not aResult:
            logger.info('[EINSCHALTEN] No streams found!')
            url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
            execute('Container.Update(%s)' % url)
            return
        
        # Log erste URL
        logger.info('[EINSCHALTEN] First Stream URL: %s' % aResult[0])
        
        # Meta-Daten
        sThumbnail = meta.get('poster', '')
        infoTitle = meta.get('infoTitle', meta.get('title', ''))
        meta.setdefault('mediatype', 'movie')
        
        # MINIMAL: Füge JEDEN Stream hinzu ohne Filterung
        for sUrl in aResult:
            try:
                sHoster = cParser.urlparse(sUrl)
                logger.info('[EINSCHALTEN] Adding Stream: %s -> %s' % (sHoster, sUrl))
                
                # WICHTIG: isResolve = False damit ResolveURL später auflöst
                isResolve = False
                items.append((sHoster, infoTitle, meta, isResolve, sUrl, sThumbnail))
            except Exception as e:
                logger.info('[EINSCHALTEN] Error adding stream: %s' % str(e))
                pass
        
        logger.info('[EINSCHALTEN] Total items added: %d' % len(items))
        
    except Exception as e:
        logger.info('[EINSCHALTEN] ERROR in getHosters: %s' % str(e))
        import traceback
        logger.info('[EINSCHALTEN] Traceback: %s' % traceback.format_exc())
    
    # Gib Items zurück
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    logger.info('[EINSCHALTEN] Final URL: %s' % url[:200])
    logger.info('[EINSCHALTEN] === getHosters END ===')
    execute('Container.Update(%s)' % url)


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText, sSearchText, bGlobal=False)

def _search(sSearchText):
    showEntries(URL_SEARCH % sSearchText, sSearchText, bGlobal=True)
