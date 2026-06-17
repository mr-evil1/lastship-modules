import json, sys, re, xbmcgui
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting, setSetting
from resources.lib.indexers.navigatorXS import navigator
import requests

SITE_IDENTIFIER    = 'huhu'
SITE_NAME          = 'HUHU'
SITE_ICON          = 'huhu.png'
SITE_GLOBAL_SEARCH = True

URL_MAIN  = 'https://huhu.to'
URL_WEB   = URL_MAIN + '/web-vod/'
URL_LIST  = URL_WEB + 'api/list'
URL_LINKS = URL_WEB + 'api/links'
URL_GET   = URL_WEB + 'api/get'

API_KEY = 'TC2AJpYciVIFw6POgjNpiJfsnSnw'
UA      = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/30.0 Chrome/143.0.0.0 Mobile Safari/537.36'

LANG_LABELS = {1: ' (DE)', 2: ' (EN)', 3: ' (EN/DE-Sub)', 4: ' (JP)'}

oNavigator        = navigator()
addDirectoryItem  = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory       = oNavigator.xsDirectory
params            = ParameterHandler()


def _get_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': UA,
        'api-key':    API_KEY,
        'Accept':     '*/*',
        'referer':    URL_WEB,
        'origin':     URL_MAIN,
    })
    return s


def _api_get(endpoint, p):
    logger.debug('Huhu _api_get url: %s params: %s' % (endpoint, p))
    try:
        r = _get_session().get(endpoint, params=p, timeout=12)
        logger.debug('Huhu _api_get status: %s' % r.status_code)
        if r.status_code != 200:
            logger.error('Huhu _api_get non-200: %s' % r.status_code)
            return None
        return r.json()
    except Exception as e:
        logger.error('Huhu _api_get error: %s' % e)
        return None


def _get_list(list_id):
    data = _api_get(URL_LIST, {'id': list_id})
    if isinstance(data, dict):
        return data.get('data', [])
    return []


def _get_links(media_id):
    data = _api_get(URL_LINKS, {'id': media_id})
    if isinstance(data, list):
        return data
    return []


def _numeric_id(item_id):
    parts = str(item_id).split('.')
    return parts[-1] if parts else item_id


def _get_lang_code(language):
    lang = (language or '').lower()
    if 'sub' in lang and 'de' in lang and 'en' in lang:
        return 3
    if lang.startswith('de'):
        return 1
    if lang.startswith('en'):
        return 2
    if lang.startswith('ja') or lang.startswith('jp'):
        return 4
    return 0


def _display_list(items, is_movie=False):
    for item in items:
        item_id  = item.get('id', '')
        name     = item.get('name', '')
        poster   = item.get('poster', '')
        backdrop = item.get('backdrop', '')
        plot     = item.get('description', '')
        genres   = ', '.join(item.get('genres', []))
        year     = (item.get('releaseDate') or '')[:4]

        meta = quote_plus(json.dumps({
            'title': name, 'plot': plot, 'genre': genres, 'year': year,
            'poster': poster, 'fanart': backdrop, 'id': item_id,
        }))

        if is_movie:
            addDirectoryItem(
                name,
                'runPlugin&site=%s&function=getHosters&sId=%s&TVShowTitle=%s&sThumbnail=%s&meta=%s'
                % (SITE_NAME, quote_plus(item_id), quote_plus(name), quote_plus(poster), meta),
                poster or SITE_ICON, 'DefaultMovies.png', plot=plot,
            )
        else:
            addDirectoryItem(
                name,
                'runPlugin&site=%s&function=showSeasons&sId=%s&TVShowTitle=%s&sThumbnail=%s&meta=%s'
                % (SITE_NAME, quote_plus(item_id), quote_plus(name), quote_plus(poster), meta),
                poster or SITE_ICON, 'DefaultMovies.png', plot=plot,
            )
    setEndOfDirectory()


def load():
    addDirectoryItem('Serien – Trending', 'runPlugin&site=%s&function=showTrending&sType=series' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Serien – Beliebt',  'runPlugin&site=%s&function=showPopular&sType=series'  % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Filme – Trending',  'runPlugin&site=%s&function=showTrending&sType=movie'  % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Filme – Beliebt',   'runPlugin&site=%s&function=showPopular&sType=movie'   % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Suche',             'runPlugin&site=%s&function=showSearch'                % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showTrending():
    sType = params.getValue('sType') or 'series'
    _display_list(_get_list('%s.trending' % sType), is_movie=(sType == 'movie'))


def showPopular():
    sType = params.getValue('sType') or 'series'
    _display_list(_get_list('%s.popular' % sType), is_movie=(sType == 'movie'))


def showSeasons():
    sId          = params.getValue('sId')
    sTVShowTitle = params.getValue('TVShowTitle') or ''
    sThumbnail   = params.getValue('sThumbnail') or ''
    metaStr      = params.getValue('meta') or '{}'

    try:
        meta = json.loads(metaStr)
    except Exception:
        meta = {}

    items   = _get_list('series.%s' % _numeric_id(sId))
    plot    = meta.get('plot', '')
    poster  = meta.get('poster', sThumbnail)
    seasons = items[0].get('seasons') or {} if items else {}

    if seasons:
        for season_key in sorted(seasons.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
            sLabel = 'Specials' if str(season_key) == '0' else 'Staffel %s' % season_key
            addDirectoryItem(
                sLabel,
                'runPlugin&site=%s&function=showEpisodes&sId=%s&sSeason=%s&TVShowTitle=%s&sThumbnail=%s&meta=%s'
                % (SITE_NAME, quote_plus(sId), season_key, quote_plus(sTVShowTitle), quote_plus(poster), quote_plus(metaStr)),
                poster or SITE_ICON, 'DefaultMovies.png', plot=plot,
            )
    else:
        addDirectoryItem(
            'Staffel 1',
            'runPlugin&site=%s&function=showEpisodes&sId=%s&sSeason=1&TVShowTitle=%s&sThumbnail=%s&meta=%s'
            % (SITE_NAME, quote_plus(sId), quote_plus(sTVShowTitle), quote_plus(poster), quote_plus(metaStr)),
            poster or SITE_ICON, 'DefaultMovies.png', plot=plot,
        )
    setEndOfDirectory()


def showEpisodes():
    sId          = params.getValue('sId')
    sSeason      = params.getValue('sSeason') or '1'
    sTVShowTitle = params.getValue('TVShowTitle') or ''
    sThumbnail   = params.getValue('sThumbnail') or ''
    metaStr      = params.getValue('meta') or '{}'

    try:
        meta = json.loads(metaStr)
    except Exception:
        meta = {}

    items = _get_list('series.%s.%s' % (_numeric_id(sId), sSeason))

    if not items:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Episoden gefunden')
        setEndOfDirectory()
        return

    plot   = meta.get('plot', '')
    poster = meta.get('poster', sThumbnail)

    ep_items = []
    for item in items:
        ep_id     = item.get('id', '')
        ep_name   = item.get('name', '')
        ep_plot   = item.get('description', plot)
        ep_poster = item.get('poster', poster)

        ep_meta = quote_plus(json.dumps({
            'title':       ep_name,
            'TVShowTitle': sTVShowTitle,
            'plot':        ep_plot,
            'poster':      ep_poster,
            'fanart':      item.get('backdrop', meta.get('fanart', '')),
            'season':      int(sSeason) if sSeason.isdigit() else 1,
            'id':          ep_id,
        }))

        ep_items.append({
            'TVShowTitle': sTVShowTitle,
            'title':       ep_name,
            'infoTitle':   ep_name,
            'entryUrl':    '',
            'sUrl':        'runPlugin&site=%s&function=getHosters&sId=%s&TVShowTitle=%s&sThumbnail=%s&meta=%s'
                           % (SITE_NAME, quote_plus(ep_id), quote_plus(sTVShowTitle), quote_plus(ep_poster), ep_meta),
            'isTvshow':    True,
            'poster':      ep_poster or SITE_ICON,
            'sThumbnail':  ep_poster or SITE_ICON,
            'fanart':      item.get('backdrop', meta.get('fanart', '')),
            'plot':        ep_plot,
            'mediatype':   'episode',
            'season':      int(sSeason) if sSeason.isdigit() else 1,
            'sFunction':   'getHosters',
        })

    xsDirectory(ep_items, SITE_NAME)
    setEndOfDirectory()


def getHosters():
    sId        = params.getValue('sId') or ''
    sThumbnail = params.getValue('sThumbnail') or ''
    sTitle     = params.getValue('TVShowTitle') or ''
    metaStr    = params.getValue('meta') or '{}'

    try:
        meta = json.loads(metaStr)
    except Exception:
        meta = {}

    sThumbnail = sThumbnail or meta.get('poster', '')
    sTitle     = sTitle or meta.get('title', '')

    if not sId:
        logger.error('Huhu getHosters: sId leer')
        setEndOfDirectory()
        return

    links = _get_links(sId)
    logger.debug('Huhu getHosters links count: %s' % len(links))

    if not links:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Streams gefunden')
        setEndOfDirectory()
        return

    hosters = []
    for link in links:
        if not isinstance(link, dict):
            continue
        token    = link.get('url', '').strip()
        if not token:
            continue
        name     = link.get('name', 'Stream')
        language = link.get('language', '').split('(')[0].strip()
        sLang    = language.lower()

        sLangPref = getSetting('prefLanguage') or '0'
        if sLangPref == '1' and 'en' in sLang: continue
        if sLangPref == '2' and 'de' in sLang: continue
        if sLangPref == '3':                    continue

        lang_code  = _get_lang_code(language)
        lang_label = LANG_LABELS.get(lang_code, '')

        if 1==1:
            s = requests.Session()
            s.headers.update({
                'sec-ch-ua':                 '"Samsung Internet";v="30.0", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-mobile':          '?1',
                'sec-ch-ua-platform':        '"Android"',
                'upgrade-insecure-requests': '1',
                'User-Agent':                UA,
                'Accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'sec-fetch-site':            'same-origin',
                'sec-fetch-mode':            'navigate',
                'sec-fetch-user':            '?1',
                'sec-fetch-dest':            'document',
                'Referer':                   URL_MAIN + '/web-vod/item',
                'Accept-Encoding':           'gzip, deflate, br',
                'Accept-Language':           'de-AT,de-DE;q=0.9,de;q=0.8,en-US;q=0.7,en;q=0.6',
            })
            resp = s.get(URL_GET + '?link=' + token, allow_redirects=False, timeout=10)
            hoster_url = resp.headers.get('location', '')
            
            logger.debug('Huhu redirect status=%s url=%s' % (resp.status_code, hoster_url))
        #except Exception as e:
            #logger.error('Huhu getHosters redirect error: %s' % e)
            #hoster_url = ''

        if not hoster_url:
            continue

        logger.debug('Huhu getHosters adding: %s %s -> %s' % (name, lang_label, hoster_url))

        hosters.append([
            '%s%s' % (name, lang_label),
            sTitle,
            metaStr,
            False,
            hoster_url,
            sThumbnail,
        ])

    if not hosters:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Streams gefunden')
        setEndOfDirectory()
        return

    oNavigator.showHosters(json.dumps(hosters))


def getHosterUrl(sUrl=False):
    if not sUrl:
        sUrl = params.getValue('sUrl')
    logger.debug('Huhu getHosterUrl sUrl: %s' % sUrl)

    try:
        s = requests.Session()
        s.headers.update({'User-Agent': UA, 'Referer': URL_WEB, 'Origin': URL_MAIN})
        resp = s.get(sUrl, allow_redirects=False, timeout=10)
        real_url = resp.headers.get('location', sUrl)
        logger.debug('Huhu getHosterUrl real_url: %s' % real_url)
        return [{'streamUrl': real_url, 'resolved': False}]
    except Exception as e:
        logger.error('Huhu getHosterUrl error: %s' % e)
        return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if sSearchText:
        _search(sSearchText)
    setEndOfDirectory()


def _search(sSearchText, bGlobal=False):
    if not sSearchText:
        return

    query   = sSearchText.lower()
    results = []
    seen    = set()

    for list_id in ('series.trending', 'series.popular', 'movie.trending', 'movie.popular'):
        is_movie = list_id.startswith('movie')
        for item in _get_list(list_id):
            item_id = item.get('id', '')
            name    = item.get('name', '')
            orig    = item.get('originalName', '')
            if query in name.lower() or query in orig.lower():
                if item_id not in seen:
                    seen.add(item_id)
                    results.append((item, is_movie))

    if not results:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Treffer für: ' + sSearchText)
        setEndOfDirectory()
        return

    for item, is_movie in results:
        name     = item.get('name', '')
        poster   = item.get('poster', '')
        backdrop = item.get('backdrop', '')
        plot     = item.get('description', '')
        genres   = ', '.join(item.get('genres', []))
        year     = (item.get('releaseDate') or '')[:4]
        sId      = item.get('id', '')

        meta = quote_plus(json.dumps({
            'title': name, 'plot': plot, 'genre': genres, 'year': year,
            'poster': poster, 'fanart': backdrop, 'id': sId,
        }))

        if is_movie:
            addDirectoryItem(
                name,
                'runPlugin&site=%s&function=getHosters&sId=%s&TVShowTitle=%s&sThumbnail=%s&meta=%s'
                % (SITE_NAME, quote_plus(sId), quote_plus(name), quote_plus(poster), meta),
                poster or SITE_ICON, 'DefaultMovies.png', plot=plot,
            )
        else:
            addDirectoryItem(
                name,
                'runPlugin&site=%s&function=showSeasons&sId=%s&TVShowTitle=%s&sThumbnail=%s&meta=%s'
                % (SITE_NAME, quote_plus(sId), quote_plus(name), quote_plus(poster), meta),
                poster or SITE_ICON, 'DefaultMovies.png', plot=plot,
            )
    setEndOfDirectory()
