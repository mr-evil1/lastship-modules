import re, sys, json
import xbmc
from datetime import datetime
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.control import getSetting

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'kinokiste'
SITE_NAME       = 'Kinokiste'
SITE_ICON       = 'kinokiste.png'

DOMAIN    = getSetting('provider.' + SITE_IDENTIFIER + '.domain', 'kinokiste.club')
ORIGIN    = 'https://' + DOMAIN + '/'
REFERER   = ORIGIN
UA        = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

URL_API       = 'https://' + DOMAIN
URL_MAIN      = 'https://kinokiste.eu/data/browse/?lang=%s&type=%s&order_by=%s&page=%s'
URL_SEARCH    = 'https://kinokiste.eu/data/browse/?lang=%s&order_by=new&page=1&limit=0'
URL_THUMBNAIL = 'https://image.tmdb.org/t/p/w300%s'
URL_WATCH     = URL_API + '/data/watch/?_id=%s'
URL_GENRE     = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&genre=%s&page=%s'
URL_CAST      = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&cast=%s&page=%s'
URL_YEAR      = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&year=%s&page=%s'

_apiJson = None

def _getLang():
    sLang = getSetting('provider.' + SITE_IDENTIFIER + '.lang', '2')
    return sLang if sLang else '2'

def _getQuality(sQuality):
    isMatch, aResult = cParser.parse(str(sQuality), '(HDCAM|HD|WEB|BLUERAY|BRRIP|DVD|TS|SD|CAM)', 1, True)
    return aResult[0] if isMatch else str(sQuality)

def _getGenres(sLang):
    if sLang in ('2', 'all'):
        return {
            'Action': 'Action', 'Abenteuer': 'Abenteuer', 'Animation': 'Animation',
            'Biographie': 'Biographie', 'Dokumentation': 'Dokumentation', 'Drama': 'Drama',
            'Familie': 'Familie', 'Fantasy': 'Fantasy', 'Geschichte': 'Geschichte',
            'Horror': 'Horror', 'Komoedie': 'Komoedie', 'Krieg': 'Krieg', 'Krimi': 'Krimi',
            'Musik': 'Musik', 'Mystery': 'Mystery', 'Romantik': 'Romantik',
            'Reality-TV': 'Reality-TV', 'Sci-Fi': 'Sci-Fi', 'Sport': 'Sport',
            'Thriller': 'Thriller', 'Western': 'Western',
        }
    return {
        'Action': 'Action', 'Adventure': 'Abenteuer', 'Animation': 'Animation',
        'Biography': 'Biographie', 'Comedy': 'Komoedie', 'Crime': 'Krimi',
        'Documentation': 'Dokumentation', 'Drama': 'Drama', 'Family': 'Familie',
        'Fantasy': 'Fantasy', 'History': 'Geschichte', 'Horror': 'Horror',
        'Music': 'Musik', 'Mystery': 'Mystery', 'Romance': 'Romantik',
        'Reality-TV': 'Reality-TV', 'Sci-Fi': 'Sci-Fi', 'Sports': 'Sport',
        'Thriller': 'Thriller', 'War': 'Krieg', 'Western': 'Western',
    }

def _addEntry(sName, sUrl):
    addDirectoryItem(sName,
        'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sUrl)),
        SITE_ICON, 'DefaultVideo.png')

def load():
    logger.info('Load %s' % SITE_NAME)
    sLang = _getLang()
    addDirectoryItem('Filme',
        'runPlugin&site=%s&function=showMovieMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Genre (Filme)',
        'runPlugin&site=%s&function=showGenreMMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Serien',
        'runPlugin&site=%s&function=showSeriesMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Genre (Serien)',
        'runPlugin&site=%s&function=showGenreSMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Jahre',
        'runPlugin&site=%s&function=showYearsMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultYear.png')
    addDirectoryItem('Schauspieler',
        'runPlugin&site=%s&function=showSearchActor&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultActor.png')
    addDirectoryItem('Suche',
        'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()

def showMovieMenu():
    params = ParameterHandler()
    sLang  = params.getValue('sLang') or _getLang()
    _addEntry('Trending',  URL_MAIN % (sLang, 'movies', 'Trending',  '1'))
    _addEntry('Neu',       URL_MAIN % (sLang, 'movies', 'new',       '1'))
    _addEntry('Aufrufe',   URL_MAIN % (sLang, 'movies', 'views',     '1'))
    _addEntry('Bewertung', URL_MAIN % (sLang, 'movies', 'rating',    '1'))
    _addEntry('Votes',     URL_MAIN % (sLang, 'movies', 'votes',     '1'))
    _addEntry('Updates',   URL_MAIN % (sLang, 'movies', 'updates',   '1'))
    _addEntry('Name',      URL_MAIN % (sLang, 'movies', 'name',      '1'))
    _addEntry('Featured',  URL_MAIN % (sLang, 'movies', 'featured',  '1'))
    _addEntry('Angefragt', URL_MAIN % (sLang, 'movies', 'requested', '1'))
    _addEntry('Releases',  URL_MAIN % (sLang, 'movies', 'releases',  '1'))
    setEndOfDirectory()

def showSeriesMenu():
    params = ParameterHandler()
    sLang  = params.getValue('sLang') or _getLang()
    _addEntry('Neu',       URL_MAIN % (sLang, 'tvseries', 'new',       '1'))
    _addEntry('Aufrufe',   URL_MAIN % (sLang, 'tvseries', 'views',     '1'))
    _addEntry('Votes',     URL_MAIN % (sLang, 'tvseries', 'votes',     '1'))
    _addEntry('Updates',   URL_MAIN % (sLang, 'tvseries', 'updates',   '1'))
    _addEntry('Name',      URL_MAIN % (sLang, 'tvseries', 'name',      '1'))
    _addEntry('Featured',  URL_MAIN % (sLang, 'tvseries', 'featured',  '1'))
    _addEntry('Angefragt', URL_MAIN % (sLang, 'tvseries', 'requested', '1'))
    _addEntry('Releases',  URL_MAIN % (sLang, 'tvseries', 'releases',  '1'))
    _addEntry('Bewertung', URL_MAIN % (sLang, 'tvseries', 'rating',    '1'))
    setEndOfDirectory()

def showGenreMMenu():
    params = ParameterHandler()
    sLang  = params.getValue('sLang') or _getLang()
    for label, order in [('Trending','Trending'), ('Neu','new'), ('Aufrufe','views'),
                         ('Votes','votes'), ('Updates','updates'), ('Bewertung','rating'),
                         ('Name','name'), ('Angefragt','requested'), ('Featured','featured'),
                         ('Releases','releases')]:
        addDirectoryItem('Genre %s' % label,
            'runPlugin&site=%s&function=showGenreList&sLang=%s&sType=movies&sMenu=%s' % (SITE_NAME, sLang, order),
            SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showGenreSMenu():
    params = ParameterHandler()
    sLang  = params.getValue('sLang') or _getLang()
    for label, order in [('Trending','Trending'), ('Neu','new'), ('Aufrufe','views'),
                         ('Votes','votes'), ('Updates','updates'), ('Bewertung','rating'),
                         ('Name','name'), ('Angefragt','requested'), ('Featured','featured'),
                         ('Releases','releases')]:
        addDirectoryItem('Genre %s' % label,
            'runPlugin&site=%s&function=showGenreList&sLang=%s&sType=tvseries&sMenu=%s' % (SITE_NAME, sLang, order),
            SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showGenreList():
    params = ParameterHandler()
    sLang  = params.getValue('sLang') or _getLang()
    sType  = params.getValue('sType') or 'movies'
    sMenu  = params.getValue('sMenu') or 'new'
    for genre, searchGenre in sorted(_getGenres(sLang).items()):
        sUrl = URL_GENRE % (sLang, sType, sMenu, searchGenre, '1')
        addDirectoryItem(genre,
            'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sUrl)),
            SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showYearsMenu():
    params = ParameterHandler()
    sLang  = params.getValue('sLang') or _getLang()
    for year in range(datetime.now().year, 1930, -1):
        sUrl = URL_YEAR % (sLang, 'movies', 'new', str(year), '1')
        addDirectoryItem(str(year),
            'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sUrl)),
            SITE_ICON, 'DefaultYear.png')
    setEndOfDirectory()

def showEntriesFromUrl():
    params = ParameterHandler()
    showEntries(entryUrl=params.getValue('sUrl'))

def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    sUrl   = entryUrl if entryUrl else params.getValue('sUrl')

    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('User-Agent', UA)
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', 'https://' + DOMAIN)
        oRequest.cacheTime = 60 * 60 * 6
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return

    if 'movies' not in aJson or not isinstance(aJson.get('movies'), list) or not aJson['movies']:
        return

    isTvshow = False
    items    = []

    for movie in aJson['movies']:
        if '_id' not in movie:
            continue
        sTitle   = str(movie['title'])
        isTvshow = 'Staffel' in sTitle or 'Season' in sTitle
        if sSearchText and sSearchText.lower() not in sTitle.lower():
            continue

        sThumbnail = ''
        for key in ('poster_path_season', 'poster_path', 'backdrop_path'):
            if movie.get(key):
                sThumbnail = URL_THUMBNAIL % str(movie[key])
                break

        sDesc    = str(movie.get('storyline', movie.get('overview', '')))
        sQuality = _getQuality(str(movie['quality'])) if movie.get('quality') else ''
        sYear    = str(movie['year']) if movie.get('year') and len(str(movie['year'])) == 4 else ''
        sRating  = str(movie['rating']) if movie.get('rating') else ''

        plot = '[B][COLOR blue]{0}[/COLOR][/B]'.format(SITE_NAME)
        if sYear:   plot += ' [COLOR yellow]({0})[/COLOR]'.format(sYear)
        if sRating: plot += ' [COLOR orange]* {0}[/COLOR]'.format(sRating)
        if sDesc:   plot += '[CR]{0}'.format(sDesc[:250])

        item = {
            'title':     (SITE_NAME + ' - ' + sTitle) if bGlobal else sTitle,
            'infoTitle': sTitle,
            'entryUrl':  URL_WATCH % str(movie['_id']),
            'poster':    sThumbnail,
            'isTvshow':  True,
            'quality':   sQuality,
            'year':      sYear,
            'rating':    sRating,
            'plot':      plot,
        }

        if movie.get('runtime'):
            isMatch, sRuntime = cParser.parseSingleResult(str(movie['runtime']), r'\d+')
            if isMatch:
                item['duration'] = sRuntime

        if movie.get('lang') == 2:
            item['language'] = 'DE'
        elif movie.get('lang') == 3:
            item['language'] = 'EN'

        if isTvshow:
            item['sFunction'] = 'showEpisodes'
            mSeason = re.search(r'Staffel\s+(\d+)|Season\s+(\d+)', sTitle, re.IGNORECASE)
            item['season'] = (mSeason.group(1) or mSeason.group(2)) if mSeason else '1'
            if ' - ' in sTitle:
                item['infoTitle'] = sTitle.split(' - ')[0].strip()
        else:
            item["sFunction"] = "getHosters"
            item["isTvshow"]  = True  # isFolder=True -> gueltiger Handle fuer getHosters

        items.append(item)

    if not items:
        return

    xsDirectory(items, SITE_NAME)

    if bGlobal:
        return

    try:
        curPage    = int(aJson['pager']['currentPage'])
        totalPages = int(aJson['pager']['totalPages'])
        if curPage < totalPages:
            sNextUrl = re.sub(r'page=\d+', 'page=' + str(curPage + 1), sUrl)
            addDirectoryItem('[B]>>> Naechste Seite[/B]',
                'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sNextUrl)),
                'next.png', 'DefaultVideo.png')
    except:
        pass

    setEndOfDirectory(sorted=False)

def showEpisodes():
    params     = ParameterHandler()
    sUrl       = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail') or ''
    meta       = {}
    try:
        meta = json.loads(params.getValue('meta'))
        if not sUrl:
            sUrl = meta.get('entryUrl', '')
        if not sThumbnail:
            sThumbnail = meta.get('poster', '')
    except:
        pass

    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('User-Agent', UA)
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', 'https://' + DOMAIN)
        oRequest.cacheTime = 60 * 60 * 4
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return

    if 'streams' not in aJson or not aJson['streams']:
        return

    aEpisodes = sorted(set(int(s['e']) for s in aJson['streams'] if 'e' in s))
    if not aEpisodes:
        return

    sInfTitle = meta.get('infoTitle', '')
    sSeason   = str(aJson['s']) if 's' in aJson else meta.get('season', '1')

    items = []
    for ep in aEpisodes:
        items.append({
            'title':     'Episode %d' % ep,
            'infoTitle': sInfTitle,
            'entryUrl':  sUrl,
            'poster':    sThumbnail,
            'isTvshow':  True,
            'season':    sSeason,
            'episode':   str(ep),
            'sFunction': 'getHosters',
        })

    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def getHosters():
    params   = ParameterHandler()
    sUrl     = params.getValue('entryUrl')
    sEpisode = params.getValue('episode')
    sRawMeta = params.getValue('meta')
    meta     = {}
    sThumbnail = ''
    sTitle     = ''

    if sRawMeta:
        try:
            meta       = json.loads(sRawMeta)
            sThumbnail = meta.get('poster', '')
            sTitle     = meta.get('infoTitle', '')
            if not sUrl:
                sUrl   = meta.get('entryUrl', '')
            if not sEpisode and meta.get('isTvshow'):
                sEpisode = str(meta.get('episode', ''))
        except:
            pass

    if not sUrl:
        logger.error('[%s] getHosters: keine URL' % SITE_NAME)
        oNavigator.showHosters(json.dumps([]))
        return

    sJson = None
    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('User-Agent', UA)
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', 'https://' + DOMAIN)
        oRequest.addHeaderEntry('Accept', 'application/json, text/plain, */*')
        oRequest.cacheTime = 0
        sJson = oRequest.request()
        logger.info('[%s] Watch-API Antwort: %d Bytes fuer %s' % (SITE_NAME, len(sJson) if sJson else 0, sUrl))
        logger.info('[%s] Watch-API raw: %s' % (SITE_NAME, sJson[:300] if sJson else ''))
    except Exception as e:
        logger.error('[%s] Watch-API Fehler: %s' % (SITE_NAME, str(e)))
        oNavigator.showHosters(json.dumps([]))
        return

    if not sJson:
        logger.error('[%s] Watch-API leere Antwort fuer %s' % (SITE_NAME, sUrl))
        oNavigator.showHosters(json.dumps([]))
        return

    try:
        aJson = json.loads(sJson)
    except Exception as e:
        logger.error('[%s] Watch-API JSON-Fehler: %s' % (SITE_NAME, str(e)))
        oNavigator.showHosters(json.dumps([]))
        return

    if 'streams' not in aJson or not aJson['streams']:
        logger.info('[%s] Keine Streams - aJson keys: %s' % (SITE_NAME, str(list(aJson.keys()))))
        logger.info('[%s] aJson streams wert: %s' % (SITE_NAME, str(aJson.get('streams', 'KEY_FEHLT'))))
        oNavigator.showHosters(json.dumps([]))
        return

    logger.info('[%s] %d Streams gefunden' % (SITE_NAME, len(aJson['streams'])))

    items = []
    for stream in aJson['streams']:
        if 'e' in stream and sEpisode and str(stream['e']) != str(sEpisode):
            continue
        if 'stream' not in stream:
            continue

        sStreamUrl = stream['stream']
        if sStreamUrl.startswith('//'):
            sStreamUrl = 'https:' + sStreamUrl

        isMatch, aName = cParser.parse(sStreamUrl, '//([^/]+)/')
        if isMatch:
            sName = aName[0]
            if '.' in sName:
                sName = sName[:sName.rindex('.')]
            sHoster = sName.upper()
        else:
            sHoster = 'STREAM'

        if stream.get('release') and str(stream['release']) != '':
            sHoster += ' [I][%s][/I]' % _getQuality(str(stream['release']))

        items.append((sHoster, sTitle, meta, False, sStreamUrl, sThumbnail))

    logger.info('[%s] %d Hoster-Items gebaut' % (SITE_NAME, len(items)))
    oNavigator.showHosters(json.dumps(items))

def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]

def showSearchActor():
    sName = oNavigator.showKeyBoard()
    if not sName:
        return
    sLang = _getLang()
    showEntries(URL_CAST % (sLang, 'movies', 'new', quote_plus(sName), '1'), bGlobal=False)




def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        setEndOfDirectory()
        return
    _search(sSearchText)

def _search(sSearchText):
    global _apiJson
    sLang = _getLang()

    if _apiJson is None or 'movies' not in _apiJson:
        _loadSearchData(sLang)

    if not _apiJson or not _apiJson.get('movies'):
        setEndOfDirectory()
        return

    sst   = sSearchText.lower()
    items = []

    for movie in _apiJson['movies']:
        if '_id' not in movie:
            continue
        sTitle   = str(movie.get('title', ''))
        isTvshow = 'Staffel' in sTitle or 'Season' in sTitle
        sSearch  = (sTitle.rsplit('-', 1)[0] if isTvshow else sTitle).replace(' ', '').lower()
        if sst not in sSearch and sst not in sTitle.lower():
            continue

        sThumbnail = ''
        for key in ('poster_path_season', 'poster_path', 'backdrop_path'):
            if movie.get(key):
                sThumbnail = URL_THUMBNAIL % str(movie[key])
                break

        sDesc    = str(movie.get('storyline', movie.get('overview', '')))
        sQuality = _getQuality(str(movie['quality'])) if movie.get('quality') else ''
        sYear    = str(movie['year']) if movie.get('year') and len(str(movie['year'])) == 4 else ''
        sRating  = str(movie['rating']) if movie.get('rating') else ''

        plot = '[B][COLOR blue]{0}[/COLOR][/B]'.format(SITE_NAME)
        if sYear:   plot += ' [COLOR yellow]({0})[/COLOR]'.format(sYear)
        if sRating: plot += ' [COLOR orange]* {0}[/COLOR]'.format(sRating)
        if sDesc:   plot += '[CR]{0}'.format(sDesc[:250])

        item = {
            'title':     SITE_NAME + ' - ' + sTitle,
            'infoTitle': sTitle,
            'entryUrl':  URL_WATCH % str(movie['_id']),
            'poster':    sThumbnail,
            'isTvshow':  True,
            'quality':   sQuality,
            'year':      sYear,
            'rating':    sRating,
            'plot':      plot,
        }
        if isTvshow:
            item['sFunction'] = 'showEpisodes'
            mSeason = re.search(r'Staffel\s+(\d+)|Season\s+(\d+)', sTitle, re.IGNORECASE)
            item['season'] = (mSeason.group(1) or mSeason.group(2)) if mSeason else '1'
            if ' - ' in sTitle:
                item['infoTitle'] = sTitle.split(' - ')[0].strip()
        else:
            item["sFunction"] = "getHosters"
            item["isTvshow"]  = True
        items.append(item)

    if items:
        xsDirectory(items, SITE_NAME)
    setEndOfDirectory(sorted=False)

def _loadSearchData(sLang):
    global _apiJson
    try:
        oRequest = cRequestHandler(URL_SEARCH % sLang)
        oRequest.addHeaderEntry('User-Agent', UA)
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', 'https://kinokiste.eu')
        oRequest.cacheTime = 60 * 60 * 48
        sJson    = oRequest.request()
        _apiJson = json.loads(sJson)
        logger.info('[%s] Suchdaten geladen' % SITE_NAME)
    except:
        logger.error('[%s] Fehler beim Laden der Suchdaten' % SITE_NAME)
        _apiJson = {'movies': []}
