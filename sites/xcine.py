# -*- coding: utf-8 -*-
import json
import re
import xbmcgui
from datetime import datetime
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import quote_plus, getSetting
from resources.lib.indexers.navigatorXS import navigator

try:
    import resolveurl
except ImportError:
    resolveurl = None

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'xcine'
SITE_NAME = 'xCine'
SITE_ICON = 'xcinetop.png'

DOMAIN      = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'xcine.io')
ORIGIN      = 'https://' + DOMAIN + '/'
REFERER     = ORIGIN + '/'
URL_API     = 'https://' + DOMAIN
URL_MAIN    = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&page=%s'
URL_SEARCH  = URL_API + '/data/browse/?lang=%s&order_by=%s&page=%s&limit=0'
URL_THUMB   = 'https://image.tmdb.org/t/p/w300%s'
URL_WATCH   = URL_API + '/data/watch/?_id=%s'
URL_GENRE   = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&genre=%s&page=%s'
URL_CAST    = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&cast=%s&page=%s'
URL_YEAR    = URL_API + '/data/browse/?lang=%s&type=%s&order_by=%s&year=%s&page=%s'

# Globaler Such-Cache
_apiJson = None


# ── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _getLang():
    sLanguage = getSetting('prefLanguage')
    if sLanguage == '1': return '2'
    if sLanguage == '2': return '3'
    return 'all'

def _getQuality(sQuality):
    isMatch, aResult = cParser.parse(sQuality, '(HDCAM|HD|WEB|BLUERAY|BRRIP|DVD|TS|SD|CAM)', 1, True)
    return aResult[0] if isMatch else sQuality

def _fetchJson(url):
    oRequest = cRequestHandler(url)
    oRequest.addHeaderEntry('Referer', REFERER)
    oRequest.addHeaderEntry('Origin', ORIGIN)
    return json.loads(oRequest.request())

def _thumb(movie):
    for key in ('poster_path_season', 'poster_path', 'backdrop_path'):
        if movie.get(key):
            return URL_THUMB % movie[key]
    return ''

def _isTvshow(title):
    return 'Staffel' in title or 'Season' in title


# ── Hauptmenü ───────────────────────────────────────────────────────────────

def load():
    sLang = _getLang()
    addDirectoryItem('Filme',         'runPlugin&site=%s&function=showMovieMenu&sLang=%s'  % (SITE_NAME, sLang), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Filme / Genre', 'runPlugin&site=%s&function=showGenreMMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Serien',        'runPlugin&site=%s&function=showSeriesMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Serien / Genre','runPlugin&site=%s&function=showGenreSMenu&sLang=%s' % (SITE_NAME, sLang), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Jahre',         'runPlugin&site=%s&function=showYearsMenu&sLang=%s'  % (SITE_NAME, sLang), SITE_ICON, 'DefaultYear.png')
    addDirectoryItem('Schauspieler',  'runPlugin&site=%s&function=showSearchActor&sLang=%s'% (SITE_NAME, sLang), SITE_ICON, 'DefaultActor.png')
    addDirectoryItem('Suche',         'runPlugin&site=%s&function=showSearch&sLang=%s'     % (SITE_NAME, sLang), SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


# ── Film-Menü ────────────────────────────────────────────────────────────────

def showMovieMenu():
    sLang = params.getValue('sLang')
    orders = [
        ('Trending',   'Trending'),
        ('Neu',        'new'),
        ('Meist gesehen', 'views'),
        ('Bewertung',  'rating'),
        ('Votes',      'votes'),
        ('Updates',    'updates'),
        ('A-Z',        'name'),
        ('Featured',   'featured'),
        ('Requested',  'requested'),
        ('Releases',   'releases'),
    ]
    for label, order in orders:
        url = URL_MAIN % (sLang, 'movies', order, '1')
        addDirectoryItem(label, 'runPlugin&site=%s&function=showEntries&sLang=%s&sUrl=%s' % (
            SITE_NAME, sLang, quote_plus(url)), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showGenreMMenu():
    sLang = params.getValue('sLang')
    orders = [('Trending','Trending'),('Neu','new'),('Views','views'),('Votes','votes'),
              ('Updates','updates'),('Rating','rating'),('A-Z','name'),
              ('Requested','requested'),('Featured','featured'),('Releases','releases')]
    for label, order in orders:
        addDirectoryItem('Genre ' + label,
            'runPlugin&site=%s&function=showGenreMenu&sLang=%s&sType=movies&sMenu=%s' % (
                SITE_NAME, sLang, order), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


# ── Serien-Menü ──────────────────────────────────────────────────────────────

def showSeriesMenu():
    sLang = params.getValue('sLang')
    orders = [
        ('Neu',        'neu'),
        ('Meist gesehen', 'views'),
        ('Votes',      'votes'),
        ('Updates',    'updates'),
        ('A-Z',        'name'),
        ('Featured',   'featured'),
        ('Requested',  'requested'),
        ('Releases',   'releases'),
        ('Bewertung',  'rating'),
    ]
    for label, order in orders:
        url = URL_MAIN % (sLang, 'tvseries', order, '1')
        addDirectoryItem(label, 'runPlugin&site=%s&function=showEntries&sLang=%s&sUrl=%s' % (
            SITE_NAME, sLang, quote_plus(url)), SITE_ICON, 'DefaultTVShows.png')
    setEndOfDirectory()


def showGenreSMenu():
    sLang = params.getValue('sLang')
    orders = [('Trending','Trending'),('Neu','new'),('Views','views'),('Votes','votes'),
              ('Updates','updates'),('Rating','rating'),('A-Z','name'),
              ('Requested','requested'),('Featured','featured'),('Releases','releases')]
    for label, order in orders:
        addDirectoryItem('Serien Genre ' + label,
            'runPlugin&site=%s&function=showGenreMenu&sLang=%s&sType=tvseries&sMenu=%s' % (
                SITE_NAME, sLang, order), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showGenreMenu():
    sLang  = params.getValue('sLang')
    sType  = params.getValue('sType')
    sMenu  = params.getValue('sMenu')

    if sLang in ('2', 'all'):
        genres = {
            'Action':'Action','Abenteuer':'Abenteuer','Animation':'Animation',
            'Biographie':'Biographie','Dokumentation':'Dokumentation','Drama':'Drama',
            'Familie':'Familie','Fantasy':'Fantasy','Geschichte':'Geschichte',
            'Horror':'Horror','Komödie':'Komödie','Krieg':'Krieg','Krimi':'Krimi',
            'Musik':'Musik','Mystery':'Mystery','Romantik':'Romantik',
            'Reality-TV':'Reality-TV','Sci-Fi':'Sci-Fi','Sport':'Sport',
            'Thriller':'Thriller','Western':'Western'
        }
    else:
        genres = {
            'Action':'Action','Adventure':'Abenteuer','Animation':'Animation',
            'Biography':'Biographie','Comedy':'Komödie','Crime':'Krimi',
            'Documentation':'Dokumentation','Drama':'Drama','Family':'Familie',
            'Fantasy':'Fantasy','History':'Geschichte','Horror':'Horror',
            'Music':'Musik','Mystery':'Mystery','Romance':'Romantik',
            'Reality-TV':'Reality-TV','Sci-Fi':'Sci-Fi','Sport':'Sport',
            'Thriller':'Thriller','War':'Krieg','Western':'Western'
        }
    for label, searchGenre in sorted(genres.items()):
        url = URL_GENRE % (sLang, sType, sMenu, searchGenre, '1')
        addDirectoryItem(label, 'runPlugin&site=%s&function=showEntries&sLang=%s&sUrl=%s' % (
            SITE_NAME, sLang, quote_plus(url)), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showYearsMenu():
    sLang = params.getValue('sLang')
    for jahr in range(datetime.now().year, 1930, -1):
        url = URL_YEAR % (sLang, 'movies', 'new', str(jahr), '1')
        addDirectoryItem(str(jahr), 'runPlugin&site=%s&function=showEntries&sLang=%s&sUrl=%s' % (
            SITE_NAME, sLang, quote_plus(url)), SITE_ICON, 'DefaultYear.png')
    setEndOfDirectory()


# ── Inhalte ──────────────────────────────────────────────────────────────────

def showEntries(entryUrl=False, sSearchText=False):
    sLang = params.getValue('sLang') or _getLang()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    try:
        aJson = _fetchJson(entryUrl)
    except Exception as e:
        logger.info('xCine showEntries error: %s' % str(e))
        setEndOfDirectory()
        return

    movies = aJson.get('movies', [])
    if not isinstance(movies, list) or not movies:
        setEndOfDirectory()
        return

    items = []
    for movie in movies:
        if '_id' not in movie:
            continue
        sTitle = str(movie.get('title', ''))
        if sSearchText and not cParser.search(sSearchText, sTitle):
            continue

        isTv = _isTvshow(sTitle)
        sThumbnail = _thumb(movie)
        sPlot = str(movie.get('storyline') or movie.get('overview') or '')
        sYear = str(movie.get('year', ''))
        watchUrl = URL_WATCH % str(movie['_id'])

        item = {
            'title':     sTitle,
            'infoTitle': sTitle,
            'entryUrl':  watchUrl,
            'sUrl':      watchUrl,
            'poster':    sThumbnail,
            'plot':      sPlot,
            'year':      sYear if len(sYear) == 4 else '',
            'sThumbnail': sThumbnail,
            # isTvshow=True immer → isFolder=True → echter Handle für getHosters
            'isTvshow':  True,
            'sFunction': 'showEpisodes' if isTv else 'getHosters',
        }
        if movie.get('quality'):
            item['quality'] = _getQuality(movie['quality'])
        if movie.get('rating'):
            item['rating'] = movie['rating']
        items.append(item)

    xsDirectory(items, SITE_NAME)

    # Nächste Seite
    pager = aJson.get('pager', {})
    curPage = pager.get('currentPage', 1)
    if curPage < pager.get('totalPages', 1):
        sNextUrl = entryUrl.replace('page=' + str(curPage), 'page=' + str(curPage + 1))
        addDirectoryItem('>>> Nächste Seite',
            'runPlugin&site=%s&function=showEntries&sLang=%s&sUrl=%s' % (
                SITE_NAME, sLang, quote_plus(sNextUrl)), SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()


def showEpisodes():
    meta_str = params.getValue('meta')
    try:
        meta = json.loads(meta_str)
    except Exception:
        meta = {}
    sUrl       = meta.get('entryUrl') or meta.get('sUrl') or params.getValue('entryUrl') or ''
    sThumbnail = meta.get('sThumbnail') or meta.get('poster') or ''
    sTitle     = meta.get('infoTitle') or meta.get('title') or ''

    try:
        aJson = _fetchJson(sUrl)
    except Exception as e:
        logger.info('xCine showEpisodes error: %s' % str(e))
        setEndOfDirectory()
        return

    streams = aJson.get('streams', [])
    if not streams:
        setEndOfDirectory()
        return

    episodes = sorted(set(int(s['e']) for s in streams if 'e' in s))
    items = []
    for ep in episodes:
        epTitle = 'Episode %d' % ep
        items.append({
            'title':     epTitle,
            'infoTitle': epTitle,
            'entryUrl':  sUrl,
            'sUrl':      sUrl,
            'poster':    sThumbnail,
            'plot':      epTitle,
            'isTvshow':  True,       # → isFolder=True → echter Handle
            'sFunction': 'getHosters',
            'sEpisode':  str(ep),
        })
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters():
    meta_str = params.getValue('meta') or ''
    try:
        meta = json.loads(meta_str)
    except Exception:
        meta = {}
    sUrl       = meta.get('entryUrl') or meta.get('sUrl') or params.getValue('entryUrl') or ''
    sThumbnail = meta.get('sThumbnail') or meta.get('poster') or ''
    sTitle     = meta.get('infoTitle') or meta.get('title') or ''
    sEpisode   = meta.get('sEpisode') or params.getValue('sEpisode') or ''

    try:
        aJson = _fetchJson(sUrl)
    except Exception as e:
        logger.info('xCine getHosters error: %s' % str(e))
        oNavigator.showHosters(json.dumps([]))
        return

    streams = aJson.get('streams', [])
    hosters = []
    i = 0
    for stream in streams:
        # Episode-Filter
        if sEpisode and 'e' in stream and str(sEpisode) != str(stream['e']):
            continue

        streamUrl = stream.get('stream', '')
        if not streamUrl:
            continue

        # Hostname extrahieren
        isMatch, aName = cParser.parse(streamUrl, '//([^/]+)/')
        if isMatch:
            sName = aName[0][:aName[0].rindex('.')]
        else:
            sName = str(i)

        # Qualitäts-Label
        label = '%d: %s' % (i, sName)
        if stream.get('release'):
            label += ' [I][%s][/I]' % _getQuality(str(stream['release']))

        # showHosters-Format: [label, title, meta, isResolve, url, thumbnail]
        # isResolve=False → Framework ruft resolveurl auf
        hosters.append([label, sTitle, meta_str, False, streamUrl, sThumbnail])
        i += 1

    oNavigator.showHosters(json.dumps(hosters))


# ── Suche ────────────────────────────────────────────────────────────────────

def showSearchActor():
    sName = oNavigator.showKeyBoard()
    if not sName:
        return
    sLang = params.getValue('sLang') or _getLang()
    showEntries(URL_CAST % (sLang, 'movies', 'new', quote_plus(sName), '1'))


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        return
    _search(sSearchText)


def _search(sSearchText):
    SSsearch(sSearchText)


def SSsearch(sSearchText=False):
    global _apiJson
    sLang = params.getValue('sLang') or _getLang()

    if _apiJson is None or 'movies' not in _apiJson:
        _loadMoviesData(sLang)

    movies = _apiJson.get('movies', []) if _apiJson else []
    if not movies:
        setEndOfDirectory()
        return

    sst = sSearchText.lower()

    dialog = xbmcgui.DialogProgress()
    dialog.create(SITE_NAME, 'Suche läuft...')

    total  = len(movies)
    items  = []
    for idx, movie in enumerate(movies):
        if idx % 128 == 0:
            if dialog.iscanceled(): break
            dialog.update(int(idx / total * 100), '%d / %d' % (idx, total))

        if '_id' not in movie:
            continue

        sTitle  = str(movie.get('title', ''))
        isTv    = _isTvshow(sTitle)
        sSearch = sTitle.rsplit('-', 1)[0].replace(' ', '').lower() if isTv else sTitle.lower()

        if sst not in sSearch:
            continue

        sThumbnail = _thumb(movie)
        sPlot      = str(movie.get('storyline') or movie.get('overview') or '')
        sYear      = str(movie.get('year', ''))
        watchUrl   = URL_WATCH % str(movie['_id'])

        item = {
            'title':     sTitle,
            'infoTitle': sTitle,
            'entryUrl':  watchUrl,
            'sUrl':      watchUrl,
            'poster':    sThumbnail,
            'plot':      sPlot,
            'year':      sYear if len(sYear) == 4 else '',
            'sThumbnail': sThumbnail,
            'isTvshow':  True,
            'sFunction': 'showEpisodes' if isTv else 'getHosters',
        }
        if movie.get('quality'):
            item['quality'] = _getQuality(movie['quality'])
        if movie.get('rating'):
            item['rating'] = movie['rating']
        items.append(item)

    dialog.close()
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def _loadMoviesData(sLang=None):
    global _apiJson
    if sLang is None:
        sLang = _getLang()
    try:
        oRequest = cRequestHandler(URL_SEARCH % (sLang, 'new', '1'), caching=True)
        oRequest.addHeaderEntry('Referer', REFERER)
        oRequest.addHeaderEntry('Origin', ORIGIN)
        oRequest.cacheTime = 60 * 60 * 48  # 2 Tage
        _apiJson = json.loads(oRequest.request())
        logger.info('xCine: API-Daten geladen')
    except Exception as e:
        logger.info('xCine: API-Fehler: %s' % str(e))
        _apiJson = {'movies': []}
