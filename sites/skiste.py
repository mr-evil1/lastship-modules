# -*- coding: utf-8 -*-
import json, sys, xbmcgui, re
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

SITE_IDENTIFIER = 'skiste'
SITE_NAME = 'SKiste'
SITE_ICON = 'skiste.png'

DOMAIN = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'streamkiste.sx')
URL_MAIN = 'https://' + DOMAIN + '/'
URL_BROWSE = URL_MAIN + 'data/browse/?lang=%s&type=%s&order_by=%s&page=%s'
URL_SEARCH = URL_MAIN + 'data/browse/?lang=%s&order_by=%s&page=%s&limit=0'
URL_GENRE = URL_MAIN + 'data/browse/?lang=%s&type=%s&order_by=%s&genre=%s&page=%s'
URL_CAST = URL_MAIN + 'data/browse/?lang=%s&type=%s&order_by=%s&cast=%s&page=%s'
URL_YEAR = URL_MAIN + 'data/browse/?lang=%s&type=%s&order_by=%s&year=%s&page=%s'
URL_WATCH = URL_MAIN + 'data/watch/?_id=%s'
URL_THUMBNAIL = 'https://image.tmdb.org/t/p/w300%s'
_apiCache = None


def getLanguage():
    """Gibt die aktuelle Spracheinstellung zurück"""
    sLanguage = getSetting('prefLanguage')
    if sLanguage == '0': return 'all'
    if sLanguage == '1': return '2'
    if sLanguage == '2': return '3' 
    return 'all'


def load():
    logger.info('Load %s' % SITE_NAME)
    sLang = getLanguage()
    
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showMovieMenu&sLanguage=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme Genre", 'runPlugin&site=%s&function=showGenreMMenu&sLanguage=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showSeriesMenu&sLanguage=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien Genre", 'runPlugin&site=%s&function=showGenreSMenu&sLanguage=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Jahre", 'runPlugin&site=%s&function=showYearsMenu&sLanguage=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultYear.png')
    addDirectoryItem("Schauspieler Suche", 'runPlugin&site=%s&function=showSearchActor&sLanguage=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultAddonsSearch.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showMovieMenu():
    params = ParameterHandler()
    sLanguage = params.getValue('sLanguage')
    
    addDirectoryItem("Trending", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'Trending', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Neue Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'new', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Views", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'views', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Rating", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'rating', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Votes", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'votes', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Updates", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'updates', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Name", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'name', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Featured", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'featured', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Requested", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'requested', '1'))), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Releases", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'movies', 'releases', '1'))), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showSeriesMenu():
    params = ParameterHandler()
    sLanguage = params.getValue('sLanguage')
    
    addDirectoryItem("Trending", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'Trending', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Neue Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'new', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Views", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'views', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Rating", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'rating', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Votes", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'votes', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Updates", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'updates', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Name", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'name', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Featured", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'featured', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Requested", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'requested', '1'))), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Releases", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_BROWSE % (sLanguage, 'series', 'releases', '1'))), SITE_ICON, 'DefaultTVShows.png')
    setEndOfDirectory()


def showGenreMMenu():
    params = ParameterHandler()
    sLanguage = params.getValue('sLanguage')
    sType = 'movies'
    sOrder = 'new'
    
    genres = getGenres(sLanguage)
    for genre, searchGenre in genres.items():
        addDirectoryItem(genre, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_GENRE % (sLanguage, sType, sOrder, searchGenre, '1'))), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showGenreSMenu():
    params = ParameterHandler()
    sLanguage = params.getValue('sLanguage')
    sType = 'series'
    sOrder = 'new'
    
    genres = getGenres(sLanguage)
    for genre, searchGenre in genres.items():
        addDirectoryItem(genre, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_GENRE % (sLanguage, sType, sOrder, searchGenre, '1'))), SITE_ICON, 'DefaultTVShows.png')
    setEndOfDirectory()


def getGenres(sLanguage):
    """Gibt Genre-Dictionary basierend auf Sprache zurück"""
    if sLanguage == '2' or sLanguage == 'all':
        return {
            'Action': 'Action',
            'Abenteuer': 'Abenteuer',
            'Animation': 'Animation',
            'Biographie': 'Biographie',
            'Dokumentation': 'Dokumentation',
            'Drama': 'Drama',
            'Familie': 'Familie',
            'Fantasy': 'Fantasy',
            'Geschichte': 'Geschichte',
            'Horror': 'Horror',
            'Komödie': 'Komödie',
            'Krieg': 'Krieg',
            'Krimi': 'Krimi',
            'Musik': 'Musik',
            'Mystery': 'Mystery',
            'Romantik': 'Romantik',
            'Reality-TV': 'Reality-TV',
            'Sci-Fi': 'Sci-Fi',
            'Sports': 'Sport',
            'Thriller': 'Thriller',
            'Western': 'Western'
        }
    else:
        return {
            'Action': 'Action',
            'Adventure': 'Abenteuer',
            'Animation': 'Animation',
            'Biography': 'Biographie',
            'Comedy': 'Komödie',
            'Crime': 'Krimi',
            'Documentation': 'Dokumentation',
            'Drama': 'Drama',
            'Family': 'Familie',
            'Fantasy': 'Fantasy',
            'History': 'Geschichte',
            'Horror': 'Horror',
            'Music': 'Musik',
            'Mystery': 'Mystery',
            'Romance': 'Romantik',
            'Reality-TV': 'Reality-TV',
            'Sci-Fi': 'Sci-Fi',
            'Sports': 'Sport',
            'Thriller': 'Thriller',
            'War': 'Krieg',
            'Western': 'Western'
        }


def showYearsMenu():
    params = ParameterHandler()
    sLanguage = params.getValue('sLanguage')
    from datetime import datetime
    currentYear = datetime.now().year
    
    for year in range(currentYear, 1949, -1):
        addDirectoryItem(str(year), 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, quote_plus(URL_YEAR % (sLanguage, 'movies', 'new', year, '1'))), SITE_ICON, 'DefaultYear.png')
    setEndOfDirectory()


def showEntries(entryUrl=False, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    iPage = params.getValue('page')
    if iPage and int(iPage) > 1:
        iPage = int(iPage)
        if 'page=' in entryUrl:
            entryUrl = re.sub(r'page=\d+', 'page=' + str(iPage), entryUrl)
    
    logger.info('[%s] Loading URL: %s' % (SITE_IDENTIFIER, entryUrl))
    
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    
    if 'movies' not in jSearch or not jSearch['movies']:
        return
    
    aResults = jSearch['movies']
    total = len(aResults)
    if len(aResults) == 0:
        return
    
    items = []
    for i in aResults:
        if '_id' not in i:
            continue
        
        item = {}
        sId = str(i['_id'])
        sName = i['title']
        
        isTvshow = 'Staffel' in sName or 'Season' in sName
        function = 'showSeasons' if isTvshow else 'getHosters'
        
        if 'storyline' in i and i['storyline']:
            plot = i['storyline']
        elif 'overview' in i and i['overview']:
            plot = i['overview']
        else:
            plot = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
        
        sThumbnail = ''
        if 'poster_path_season' in i and i['poster_path_season']:
            sThumbnail = URL_THUMBNAIL % str(i['poster_path_season'])
        elif 'poster_path' in i and i['poster_path']:
            sThumbnail = URL_THUMBNAIL % str(i['poster_path'])
        elif 'backdrop_path' in i and i['backdrop_path']:
            sThumbnail = URL_THUMBNAIL % str(i['backdrop_path'])
        
        mediaType = 'tvshow' if isTvshow else 'movie'
        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', URL_WATCH % sId)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', plot)
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sName', sName)
        item.setdefault('sFunction', function)
        item.setdefault('sMediaType', mediaType)
        
        if 'year' in i and len(str(i['year'])) == 4:
            item.setdefault('year', i['year'])
        if 'quality' in i:
            item.setdefault('quality', getQuality(i['quality']))
        if 'rating' in i:
            item.setdefault('rating', i['rating'])
        if 'runtime' in i:
            isMatch, sRuntime = cParser.parseSingleResult(i['runtime'], '\d+')
            if isMatch:
                item.setdefault('duration', sRuntime)
        
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    
    if not bGlobal:
        sPageNr = int(params.getValue('page')) if params.getValue('page') else 1
        sPageNr += 1
        
        nextUrl = params.getValue('sUrl')
        if 'page=' in nextUrl:
            nextUrl = re.sub(r'page=\d+', 'page=' + str(sPageNr), nextUrl)
        
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries&page=%s&sUrl=%s' % (SITE_NAME, int(sPageNr), quote_plus(nextUrl)), 'next.png', 'next.png')
    
    setEndOfDirectory()


def showSeasons(bGlobal=False):
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    entryUrl = meta.get('entryUrl')
    sThumbnail = meta.get('sThumbnail')
    sName = meta.get('sName')
    
    oRequest = cRequestHandler(entryUrl)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    
    if 'streams' not in jSearch or not jSearch['streams']:
        return
    
    seasons = set()
    for stream in jSearch['streams']:
        if 's' in stream:
            seasons.add(int(stream['s']))
    
    if not seasons:
        return
    
    aResults = sorted(list(seasons))
    total = len(aResults)
    items = []
    
    for sSeasonNr in aResults:
        item = {}
        item.setdefault('sMediaType', 'season')
        item.setdefault('TVShowTitle', sName)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', 'Staffel ' + str(sSeasonNr))
        item.setdefault('entryUrl', entryUrl)
        item.setdefault('isTvshow', True)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', meta.get('plot', ''))
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sUrl', entryUrl)
        item.setdefault('sSeasonNr', str(sSeasonNr))
        item.setdefault('sFunction', 'showEpisodes')
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def showEpisodes(bGlobal=False):
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    sSeasonNr = meta.get('sSeasonNr')
    kName = meta.get('infoTitle')
    sThumbnail = meta.get('sThumbnail')
    
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 4  # 4 Stunden
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    
    if 'streams' not in jSearch or not jSearch['streams']:
        return
    
    episodes = set()
    for stream in jSearch['streams']:
        if 's' in stream and str(stream['s']) == sSeasonNr:
            if 'e' in stream:
                episodes.add(int(stream['e']))
    
    if not episodes:
        return
    
    aResults = sorted(list(episodes))
    total = len(aResults)
    items = []
    
    for sEpisodeNr in aResults:
        item = {}
        name = 'Episode ' + str(sEpisodeNr)
        
        item.setdefault('from', 'showEpisodes')
        item.setdefault('sMediaType', 'episode')
        item.setdefault('TVShowTitle', kName)
        item.setdefault('infoTitle', kName)
        item.setdefault('title', name)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', meta.get('plot', ''))
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sSeasonNr', sSeasonNr)
        item.setdefault('sEpisodeNr', str(sEpisodeNr))
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters(bGlobal=False):
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    sThumbnail = meta.get('poster')
    isProgressDialog = True
    
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', URL_MAIN)
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    
    if 'streams' not in jSearch or not jSearch['streams']:
        return
    
    aResults = jSearch['streams']
    sEpisode = meta.get('sEpisodeNr', None)
    
    if len(aResults) == 0:
        return
    
    items = []
    if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
    t = 0
    
    for stream in aResults:
        if sEpisode:
            if 'e' not in stream or str(stream['e']) != str(sEpisode):
                continue
        else:
            if 'e' in stream:
                continue
        
        if 'stream' not in stream:
            continue
        
        streamUrl = stream['stream']
        isMatch, aName = cParser.parse(streamUrl, '//([^/]+)/')
        if isMatch:
            sName = aName[0][:aName[0].rindex('.')]
        else:
            sName = cParser.urlparse(streamUrl)
        
        #if isBlockedHoster(sName)[0]: continue
        

        sQuality = ''
        if 'release' in stream and str(stream['release']) != '':
            sQuality = getQuality(stream['release'])
        
        infoTitle = sName
        if sQuality:
            infoTitle = sName + ' - ' + sQuality
        
        t += 100 / len(aResults)
        if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sName)
        
        Request = cRequestHandler(streamUrl, caching=False)
        Request.request()
        sUrl = Request.getRealUrl()
        
        items.append((infoTitle, infoTitle, meta, False, sUrl, sThumbnail))
    
    if isProgressDialog: progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def getQuality(sQuality):
    """Extrahiert Quality aus String"""
    isMatch, aResult = cParser.parse(sQuality, '(HDCAM|HD|WEB|BLUERAY|BRRIP|DVD|TS|SD|CAM)', 1, True)
    if isMatch:
        return aResult[0]
    else:
        return sQuality


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)


def _search(bGlobal, sSearchText):
    showSearchEntries(False, bGlobal, sSearchText)


def showSearchEntries(entryUrl=False, bGlobal=False, sSearchText=''):
    global _apiCache
    
    params = ParameterHandler()
    sLanguage = getLanguage()
    if _apiCache is None or 'movies' not in _apiCache:
        loadMoviesData()
    
    if 'movies' not in _apiCache or not _apiCache['movies']:
        return
    
    aResults = _apiCache['movies']
    sst = sSearchText.lower()
    
    dialog = xbmcgui.DialogProgress()
    dialog.create('xStream V2', 'Suche läuft ...')
    
    total = len(aResults)
    position = 0
    items = []
    
    for movie in aResults:
        position += 1
        
        if '_id' not in movie:
            continue
        
        if position % 128 == 0:
            if dialog.iscanceled(): break
            dialog.update(position, str(position) + ' von ' + str(total))
        
        sTitle = movie['title']
        isTvshow = 'Staffel' in sTitle or 'Season' in sTitle
        if isTvshow:
            sSearch = sTitle.rsplit('-', 1)[0].replace(' ', '').lower()
        else:
            sSearch = sTitle.lower()
        if sst not in sSearch:
            continue
        
        item = {}
        sId = str(movie['_id'])
        function = 'showSeasons' if isTvshow else 'getHosters'
        if 'storyline' in movie and movie['storyline']:
            plot = movie['storyline']
        elif 'overview' in movie and movie['overview']:
            plot = movie['overview']
        else:
            plot = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sTitle)
        sThumbnail = ''
        if 'poster_path_season' in movie and movie['poster_path_season']:
            sThumbnail = URL_THUMBNAIL % str(movie['poster_path_season'])
        elif 'poster_path' in movie and movie['poster_path']:
            sThumbnail = URL_THUMBNAIL % str(movie['poster_path'])
        elif 'backdrop_path' in movie and movie['backdrop_path']:
            sThumbnail = URL_THUMBNAIL % str(movie['backdrop_path'])
        
        mediaType = 'tvshow' if isTvshow else 'movie'
        infoTitle = sTitle
        if bGlobal: sTitle = SITE_NAME + ' - ' + sTitle
        
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sTitle)
        item.setdefault('entryUrl', URL_WATCH % sId)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', plot)
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sName', sTitle)
        item.setdefault('sFunction', function)
        item.setdefault('sMediaType', mediaType)
        if 'year' in movie and len(str(movie['year'])) == 4:
            item.setdefault('year', movie['year'])
        if 'quality' in movie:
            item.setdefault('quality', getQuality(movie['quality']))
        if 'rating' in movie:
            item.setdefault('rating', movie['rating'])
        
        items.append(item)
    
    dialog.close()
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def showSearchActor():
    params = ParameterHandler()
    sLanguage = params.getValue('sLanguage')
    sName = oNavigator.showKeyBoard()
    if not sName: return
    _searchActor(False, sName, sLanguage)


def _searchActor(bGlobal, sName, sLanguage):
    sUrl = URL_CAST % (sLanguage, 'movies', 'new', quote_plus(sName), '1')
    showEntries(sUrl, bGlobal)
    setEndOfDirectory()


def loadMoviesData():
    """Lädt alle Movies-Daten für die Suche"""
    global _apiCache
    sLang = getLanguage()
    
    try:
        oRequest = cRequestHandler(URL_SEARCH % (sLang, 'new', '1'), caching=True)
        oRequest.addHeaderEntry('Referer', URL_MAIN)
        oRequest.addHeaderEntry('Origin', URL_MAIN)
        oRequest.cacheTime = 60 * 60 * 48  # 2 Tage Cache
        sJson = oRequest.request()
        _apiCache = json.loads(sJson)
        logger.info('[%s] API-Daten erfolgreich geladen' % SITE_IDENTIFIER)
    except:
        logger.error('[%s] Fehler beim Laden der API-Daten' % SITE_IDENTIFIER)
        _apiCache = {'movies': []}

