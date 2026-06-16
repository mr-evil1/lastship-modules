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

SITE_GLOBAL_SEARCH = False

DOMAIN = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'www.oha.to')

URL_MAIN          = 'https://' + DOMAIN + '/web-vod/'
URL_VALUE         = URL_MAIN + 'api/list?id=%s'
URL_ITEM          = URL_MAIN + 'api/links?id=%s'
URL_HOSTER        = URL_MAIN + 'api/get?link='
URL_INFO          = URL_MAIN + 'api/info?id=%s'
URL_SEARCH_MOVIES = URL_MAIN + 'api/list?id=movie.popular.search=%s'
URL_SEARCH_SERIES = URL_MAIN + 'api/list?id=series.popular.search=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    oNavigator.addDirectoryItem('Beliebte Filme',
        'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'movie.popular'),
        SITE_ICON, 'DefaultMovies.png')
    oNavigator.addDirectoryItem('Trending Filme',
        'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'movie.trending'),
        SITE_ICON, 'DefaultMovies.png')
    oNavigator.addDirectoryItem('Filme suchen',
        'runPlugin&site=%s&function=showSearchMovies' % SITE_NAME,
        SITE_ICON, 'DefaultAddonsSearch.png')
    oNavigator.addDirectoryItem('Beliebte Serien',
        'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'series.popular'),
        SITE_ICON, 'DefaultTVShows.png')
    oNavigator.addDirectoryItem('Trending Serien',
        'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'series.trending'),
        SITE_ICON, 'DefaultTVShows.png')
    oNavigator.addDirectoryItem('Serien suchen',
        'runPlugin&site=%s&function=showSearchSeries' % SITE_NAME,
        SITE_ICON, 'DefaultAddonsSearch.png')
    oNavigator._endDirectory()


def showEntries(entryUrl=False, sGui=False):
    if not entryUrl:
        entryUrl = params.getValue('sUrl')

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', 'https://' + DOMAIN)

    try:
        jSearch = json.loads(oRequest.request())
    except Exception:
        oNavigator._endDirectory()
        return

    if not jSearch:
        oNavigator._endDirectory()
        return

    aResults = jSearch.get('data', [])
    sNextUrl = jSearch.get('next', '')

    if not aResults:
        oNavigator._endDirectory()
        return

    items = []
    isTvshow = False
    for i in aResults:
        sId      = i.get('id', '')
        sName    = i.get('name', '')
        isTvshow = 'series' in sId

        sThumbnail = i.get('poster', '')
        sFanart    = i.get('backdrop', '')
        sDesc      = i.get('description', '')
        sYear      = str(i.get('releaseDate', '')).split('-')[0].strip()
        sFunction  = 'showSeasons' if isTvshow else 'getHosters'

        items.append({
            'title':     sName,
            'infoTitle': sName,
            'year':      sYear,
            'plot':      sDesc,
            'entryUrl':  URL_INFO % sId,
            'sUrl':      URL_ITEM % sId,
            'sId':       sId,
            'poster':    sThumbnail,
            'fanart':    sFanart,
            'isTvshow':  True,                                    # immer True → isFolder=True → Klick funktioniert
            'mediatype': 'tvshow' if isTvshow else 'movie',      # echter Kodi-Medientyp
            'sFunction': sFunction,
        })

    oNavigator.xsDirectory(items, SITE_NAME)

    if sNextUrl:
        nextFull = URL_MAIN + 'api/list?id=' + sNextUrl
        oNavigator.addDirectoryItem('>>> Nächste Seite',
            'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, nextFull),
            SITE_ICON, 'DefaultMovies.png')

    oNavigator._endDirectory()


def showSeasons():
    sId   = params.getValue('sId')
    sMeta = params.getValue('meta')

    if not sId and sMeta:
        try:
            sId = json.loads(sMeta).get('sId', '')
        except Exception:
            pass

    entryUrl = URL_INFO % sId

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', 'https://' + DOMAIN)

    try:
        jSearch = json.loads(oRequest.request())
    except Exception:
        oNavigator._endDirectory()
        return

    if not jSearch:
        oNavigator._endDirectory()
        return

    sThumbnail = jSearch.get('poster', '')
    sFanart    = jSearch.get('backdrop', '')
    sDesc      = jSearch.get('description', '')
    aSeasons   = sorted(jSearch.get('seasons', {}).keys())

    if not aSeasons:
        oNavigator._endDirectory()
        return

    for sSeasonNr in aSeasons:
        sLabel = 'Extras' if sSeasonNr == '0' else 'Staffel ' + sSeasonNr
        oNavigator.addDirectoryItem(sLabel,
            'runPlugin&site=%s&function=showEpisodes&sId=%s&sSeasonNr=%s&sThumbnail=%s&sDesc=%s&sFanart=%s' % (
                SITE_NAME, sId, sSeasonNr,
                quote_plus(sThumbnail), quote_plus(sDesc), quote_plus(sFanart)
            ),
            SITE_ICON, 'DefaultTVShows.png')

    oNavigator._endDirectory()


def showEpisodes():
    sId        = params.getValue('sId')
    sSeasonNr  = params.getValue('sSeasonNr')
    sThumbnail = params.getValue('sThumbnail')
    sDesc      = params.getValue('sDesc')
    sFanart    = params.getValue('sFanart')
    sMeta      = params.getValue('meta')

    if not sId and sMeta:
        try:
            _m    = json.loads(sMeta)
            sId   = _m.get('sId', '')
            sSeasonNr = sSeasonNr or str(_m.get('season', ''))
        except Exception:
            pass

    entryUrl = URL_INFO % sId

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Origin', 'https://' + DOMAIN)

    try:
        jSearch = json.loads(oRequest.request())
    except Exception:
        oNavigator._endDirectory()
        return

    if not jSearch:
        oNavigator._endDirectory()
        return

    aEpisodes = jSearch.get('seasons', {}).get(sSeasonNr, [])

    if not aEpisodes:
        oNavigator._endDirectory()
        return

    items = []
    for i in aEpisodes:
        sEpisodeNr = str(i.get('episode', ''))
        sEpId      = i.get('id', '')
        sEpName    = i.get('name', '')

        items.append({
            'title':     'Episode %s - %s' % (sEpisodeNr, sEpName),
            'infoTitle': sEpName,
            'season':    sSeasonNr,
            'episode':   sEpisodeNr,
            'plot':      sDesc or '',
            'entryUrl':  URL_ITEM % sEpId,
            'sUrl':      URL_ITEM % sEpId,
            'poster':    sThumbnail or '',
            'fanart':    sFanart or '',
            'isTvshow':  True,           # True → isFolder=True → getHosters bekommt Handle
            'mediatype': 'episode',
            'sFunction': 'getHosters',
        })

    oNavigator.xsDirectory(items, SITE_NAME)
    oNavigator._endDirectory()


def getHosters():
    sThumbnail = params.getValue('sThumbnail') or params.getValue('poster') or ''
    sTitle     = params.getValue('sTitle') or params.getValue('infoTitle') or ''
    sMeta      = params.getValue('meta') or ''
    sId        = params.getValue('sId') or ''

    meta = {}
    if sMeta:
        try:
            meta = json.loads(sMeta)
        except Exception:
            pass
        sThumbnail = sThumbnail or meta.get('poster') or ''
        sTitle     = sTitle or meta.get('infoTitle') or meta.get('title') or ''
        sId        = sId or meta.get('sId') or ''

    tmdb_id   = ''
    item_type = 'movie'
    if sId:
        parts = sId.split('.')
        if len(parts) >= 2:
            item_type = parts[0]
            tmdb_id   = parts[1]

    if not tmdb_id:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine ID gefunden', SITE_ICON, 3000)
        oNavigator._endDirectory()
        return

    import time as _time, gzip as _gzip
    from urllib.request import urlopen, Request as _Req

    def _huhu_post(endpoint, payload):
        ts   = str(int(_time.time() * 1000))
        url  = 'http://huhu.to/' + endpoint + '?_t=' + ts
        data = json.dumps(payload).encode('utf-8')
        req  = _Req(url, data=data)
        req.add_header('User-Agent', 'MediaUrl/2')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('mediaurl-signature', '')
        req.add_header('Accept-Encoding', 'gzip')
        try:
            resp = urlopen(req, timeout=15)
            raw  = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                raw = _gzip.decompress(raw)
            return json.loads(raw.decode('utf-8'))
        except Exception:
            return None

    item_payload = {
        'language': 'de', 'region': 'AT', 'clientVersion': '3.1.0',
        'type': item_type,
        'ids':  {'tmdb_id': tmdb_id},
        'name': sTitle,
        'episode': {},
    }
    item_data = _huhu_post('mediaurl-item.json', item_payload)

    if item_data and isinstance(item_data, dict):
        source_payload = dict(item_data)
        source_payload['language']      = 'de'
        source_payload['region']        = 'AT'
        source_payload['clientVersion'] = '3.1.0'
    else:
        source_payload = item_payload

    aResults = _huhu_post('mediaurl-source.json', source_payload)

    if not aResults or not isinstance(aResults, list):
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Links gefunden', SITE_ICON, 3000)
        oNavigator._endDirectory()
        return

    sLangPref = getSetting('prefLanguage') or '0'

    hosters = []
    for i in aResults:
        if not isinstance(i, dict):
            continue
        hUrl     = i.get('url', '')
        sName    = i.get('name', '')
        langs    = i.get('languages', [])
        sLang    = langs[0] if langs else ''
        sQuality = i.get('tag', '720').replace('p', '')

        if sLangPref == '1' and 'en' in sLang: continue
        if sLangPref == '2' and 'de' in sLang: continue
        if sLangPref == '3':                    continue

        sLangLabel = {'de': '(DE)', 'en': '(EN)'}.get(sLang, '')

        hosters.append([
            '%s [I]%s [%sp][/I]' % (sName, sLangLabel, sQuality),
            sTitle,
            sMeta,
            False,
            hUrl,
            sThumbnail,
        ])

    if hosters:
        oNavigator.showHosters(json.dumps(hosters))
    else:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine passenden Streams', SITE_ICON, 3000)
        oNavigator._endDirectory()


def getHosterUrl(sUrl=False):
    if not sUrl:
        sUrl = params.getValue('sUrl')

    import time, json as _json
    from urllib.request import urlopen, Request as _Req
    import gzip as _gzip

    def _post_resolve(payload_dict):
        ts  = str(int(time.time() * 1000))
        url = 'http://huhu.to/mediaurl-resolve.json?_t=' + ts
        data = _json.dumps(payload_dict).encode('utf-8')
        req  = _Req(url, data=data)
        req.add_header('User-Agent', 'MediaUrl/2')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('mediaurl-signature', '')
        req.add_header('Accept-Encoding', 'gzip')
        try:
            resp = urlopen(req, timeout=15)
            raw  = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                raw = _gzip.decompress(raw)
            return _json.loads(raw.decode('utf-8'))
        except Exception:
            return None

    step1 = _post_resolve({'language': 'de', 'region': 'AT', 'clientVersion': '3.1.0', 'url': sUrl})

    if not step1:
        return [{'streamUrl': sUrl, 'resolved': False}]

    if isinstance(step1, list) and step1:
        return [{'streamUrl': step1[0].get('url', sUrl), 'resolved': True}]

    if isinstance(step1, dict) and step1.get('kind') == 'taskRequest':
        task_id   = step1.get('id', '')
        task_data = step1.get('data', {})
        fetch_url = task_data.get('url', '')
        fetch_params = task_data.get('params', {})
        fetch_method  = fetch_params.get('method', 'GET')
        fetch_headers = fetch_params.get('headers', {})

        try:
            freq = _Req(fetch_url)
            for k, v in fetch_headers.items():
                freq.add_header(k, v)
            freq.add_header('Accept-Encoding', 'gzip')
            fresp     = urlopen(freq, timeout=15)
            fraw      = fresp.read()
            if fresp.info().get('Content-Encoding') == 'gzip':
                fraw = _gzip.decompress(fraw)
            fbody    = fraw.decode('utf-8', 'replace')
            fstatus  = fresp.getcode()
            fheaders = dict(fresp.info())
        except Exception as ex:
            step2 = _post_resolve({
                'kind': 'taskResponse',
                'id':   task_id,
                'data': {'error': str(ex)},
            })
            return [{'streamUrl': sUrl, 'resolved': False}]

        step2 = _post_resolve({
            'kind': 'taskResponse',
            'id':   task_id,
            'data': {
                'status':  fstatus,
                'headers': fheaders,
                'body':    fbody,
            },
        })

        if isinstance(step2, list) and step2:
            return [{'streamUrl': step2[0].get('url', sUrl), 'resolved': True}]
        if isinstance(step2, dict) and step2.get('url'):
            return [{'streamUrl': step2.get('url'), 'resolved': True}]

    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearchMovies():
    text = oNavigator.showKeyBoard()
    if text:
        showEntries(URL_SEARCH_MOVIES % quote_plus(text))
    oNavigator._endDirectory()


def showSearchSeries():
    text = oNavigator.showKeyBoard()
    if text:
        showEntries(URL_SEARCH_SERIES % quote_plus(text))
    oNavigator._endDirectory()


def _search(sSearchText):
    """Globale Suche – Filme und Serien."""
    showEntries(URL_SEARCH_MOVIES % quote_plus(sSearchText))
    showEntries(URL_SEARCH_SERIES % quote_plus(sSearchText))
