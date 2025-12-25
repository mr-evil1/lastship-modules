# -*- coding: utf-8 -*-
import re, json, sys, xbmcgui
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

SITE_IDENTIFIER = 'movie2k'
SITE_NAME = 'Movie2K'
SITE_ICON = 'movie2k.png'

DOMAIN = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'www2.movie2k.ch')
STATUS = getSetting('plugin_' + SITE_IDENTIFIER + '_status')
ACTIVE = getSetting('plugin_' + SITE_IDENTIFIER)

URL_MAIN = 'https://' + DOMAIN + '/'
URL_BROWSE = URL_MAIN + 'data/browse/?lang=%s&type=%s&order_by=%s&page=%s'
URL_SEARCH = URL_MAIN + 'data/browse/?lang=%s&keyword=%s&page=%s&limit=0'
URL_THUMBNAIL = 'https://image.tmdb.org/t/p/w300%s'
URL_WATCH = URL_MAIN + 'data/watch/?_id=%s'

ORIGIN = 'https://' + DOMAIN + '/'
REFERER = ORIGIN


def load():
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showMovieMenu' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showSeriesMenu' % SITE_NAME, SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def _cleanTitle(sTitle):
    sTitle = re.sub("[\xE4]", 'ae', sTitle)
    sTitle = re.sub("[\xFC]", 'ue', sTitle)
    sTitle = re.sub("[\xF6]", 'oe', sTitle)
    sTitle = re.sub("[\xC4]", 'Ae', sTitle)
    sTitle = re.sub("[\xDC]", 'Ue', sTitle)
    sTitle = re.sub("[\xD6]", 'Oe', sTitle)
    sTitle = re.sub("[\x00-\x1F\x80-\xFF]", '', sTitle)
    return sTitle


def _getQuality(sQuality):
    isMatch, aResult = cParser.parse(sQuality, '(HDCAM|HD|WEB|BLUERAY|BRRIP|DVD|TS|SD|CAM)', 1, True)
    if isMatch:
        return aResult[0]
    else:
        return sQuality


def showMovieMenu():
    sLanguage = getSetting('prefLanguage')
    if sLanguage == '0':
        sLang = 'all'
    elif sLanguage == '1':
        sLang = '2'
    elif sLanguage == '2':
        sLang = '3'
    else:
        sLang = 'all'
    
    addDirectoryItem("Filme - Featured", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'featured', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Neuerscheinungen", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'releases', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Trending", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'trending', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Updates", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'updates', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Requested", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'requested', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Top bewertet", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'rating', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Meiste Votes", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'votes', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme - Meiste Views", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'movies', 'views', '1'), safe='')), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showSeriesMenu():
    sLanguage = getSetting('prefLanguage')
    if sLanguage == '0': 
        sLang = 'all'
    elif sLanguage == '1':
        sLang = '2'
    elif sLanguage == '2':
        sLang = '3'
    else:
        sLang = 'all'
    
    addDirectoryItem("Serien - Neuerscheinungen", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'releases', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien - Trending", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'trending', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien - Updates", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'updates', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien - Requested", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'requested', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien - Top bewertet", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'rating', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien - Meiste Votes", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'votes', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien - Meiste Views", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(URL_BROWSE % (sLang, 'tvseries', 'views', '1'), safe='')), SITE_ICON, 'DefaultTVShows.png')
    setEndOfDirectory()


def showEntries(entryUrl=False, bGlobal=False, sSearchText=False):
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    
    try:
        oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', ORIGIN)
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return

    if 'movies' not in aJson or not isinstance(aJson.get('movies'), list) or len(aJson['movies']) == 0:
        return

    items = []
    
    for movie in aJson['movies']:
        if '_id' not in movie:
            continue
        
        item = {}
        sTitle = str(movie['title'])
        
        if sSearchText and not cParser().search(sSearchText, sTitle):
            continue
        
        isTvshow = False
        if 'Staffel' in sTitle or 'Season' in sTitle:
            isTvshow = True
        
        sFunction = 'showEpisodes' if isTvshow else 'getHosters'
        
        sThumbnail = ''
        if 'poster_path_season' in movie and movie['poster_path_season']:
            sThumbnail = URL_THUMBNAIL % str(movie['poster_path_season'])
        elif 'poster_path' in movie and movie['poster_path']:
            sThumbnail = URL_THUMBNAIL % str(movie['poster_path'])
        elif 'backdrop_path' in movie and movie['backdrop_path']:
            sThumbnail = URL_THUMBNAIL % str(movie['backdrop_path'])
        
        if 'storyline' in movie:
            plot = str(movie['storyline'])
        elif 'overview' in movie:
            plot = str(movie['overview'])
        else:
            plot = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sTitle)
        
        mediaType = 'tvshow' if isTvshow else 'movie'
        infoTitle = sTitle
        if bGlobal:
            sTitle = SITE_NAME + ' - ' + sTitle
        
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sTitle)
        item.setdefault('entryUrl', URL_WATCH % str(movie['_id']))
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', plot)
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sName', sTitle)
        item.setdefault('sFunction', sFunction)
        item.setdefault('sMediaType', mediaType)
        
        items.append(item)
    xsDirectory(items, SITE_NAME)

    if not bGlobal and not sSearchText:
        if 'pager' in aJson:
            curPage = aJson['pager']['currentPage']
            if curPage < aJson['pager']['totalPages']:
                nextPage = curPage + 1
                sNextUrl = re.sub(r'page=\d+', 'page=' + str(nextPage), entryUrl)
                addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote(sNextUrl, safe='')), 'next.png', 'next.png')
    
    setEndOfDirectory()


def showEpisodes(bGlobal=False):
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    sThumbnail = meta.get('sThumbnail')
    sName = meta.get('sName')
    
    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', ORIGIN)
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return

    if 'streams' not in aJson or len(aJson['streams']) == 0:
        return

    aEpisodes = []
    for stream in aJson['streams']:
        if 'e' in stream:
            aEpisodes.append(int(stream['e']))
    
    if not aEpisodes:
        return
    
    aEpisodesSorted = sorted(set(aEpisodes))
    items = []
    sSeason = aJson.get('s', '1')
    
    for sEpisode in aEpisodesSorted:
        item = {}
        item.setdefault('sMediaType', 'episode')
        item.setdefault('TVShowTitle', sName)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', 'Episode ' + str(sEpisode))
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', meta.get('plot', ''))
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sSeasonNr', sSeason)
        item.setdefault('sEpisodeNr', str(sEpisode))
        item.setdefault('sFunction', 'getHosters')
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters(bGlobal=False):
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    sEpisode = meta.get('sEpisodeNr', '')
    sThumbnail = meta.get('poster', '')
    isProgressDialog = True
    
    try:
        oRequest = cRequestHandler(sUrl, caching=False)
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', ORIGIN)
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return
    
    if 'streams' not in aJson:
        return
    
    items = []
    seen_hosters = set()
    if isProgressDialog:
        progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
    t = 0
    yes=xbmcgui.Dialog().yesno('Blocked Hoster','Sollen Streams überprüft werden?\n Längere Suchzeiten')
    for stream in aJson['streams']:
        if sEpisode and ('e' not in stream or str(sEpisode) != str(stream['e'])):
            continue
        if not sEpisode and 'e' in stream:
            continue
        
        sStreamUrl = stream['stream']
        sUrl = stream['stream']
        isMatch, aName = cParser.parse(sStreamUrl, '//([^/]+)/')
        if isMatch:
            sName = aName[0][:aName[0].rindex('.')] if '.' in aName[0] else aName[0]
            if yes:
                isBlocked, sUrl = isBlockedHoster(sUrl, resolve=False)
                if isBlocked: 
                    continue
        else:
            sName = 'Unknown'
            
        
        
        sQuality = ''
        if 'release' in stream and str(stream['release']) != '':
            sQuality = _getQuality(stream['release'])
            if len(sQuality) > 10:
                sQuality = 'unbekannt'
        hoster_quality_key = (sName.lower(), sQuality.lower())
        if hoster_quality_key in seen_hosters:
            continue
        seen_hosters.add(hoster_quality_key)
        
        sHosterName = sName
        if sQuality:
            sHosterName += ' [I][' + sQuality + '][/I]'
        
        try:
            infoTitle = cParser.urlparse(sStreamUrl)
        except:
            infoTitle = sName
        
        t += 100 / len(aJson['streams'])
        if isProgressDialog:
            progressDialog.update(int(t), '[CR]Verarbeite Hoster: ' + sName)
        
        items.append((sHosterName, infoTitle, meta, False, sStreamUrl, sThumbnail))
    
    if isProgressDialog:
        progressDialog.close()
    
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        return
    _search(False, sSearchText)


def _search(bGlobal, sSearchText):
    sLanguage = getSetting('prefLanguage')
    if sLanguage == '0':
        sLang = 'all'
    elif sLanguage == '1':
        sLang = '2'
    elif sLanguage == '2':
        sLang = '3'
    else:
        sLang = 'all'
    
    sID = quote_plus(sSearchText)
    showEntries(URL_SEARCH % (sLang, sID, '1'), bGlobal, sSearchText)
