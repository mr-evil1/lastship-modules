# -*- coding: utf-8 -*-
import re, sys, json
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger
from resources.lib.control import progressDialog, quote_plus, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting, setSetting

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'kkiste-movie'
SITE_NAME       = 'KKiste-movie'
SITE_ICON       = 'kkiste-movie.png'

DOMAIN   = getSetting('provider.' + SITE_IDENTIFIER + '.domain', 'kkiste-io.skin')
URL_MAIN = 'https://' + DOMAIN
UA       = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

URL_NEUE_FILME = URL_MAIN + '/kinofilme-online/'
URL_KINO       = URL_MAIN + '/aktuelle-kinofilme-im-kino/'
URL_DEMNACHST  = URL_MAIN + '/demnachst/'
URL_SEARCH     = URL_MAIN + '/index.php?do=search'

GENRES = {
    'Action':        '/action/',
    'Abenteuer':     '/abenteuer/',
    'Animation':     '/animation/',
    'Biographie':    '/biographie/',
    'Dokumentation': '/dokumentation/',
    'Drama':         '/drama/',
    'Familie':       '/familie/',
    'Fantasy':       '/fantasy/',
    'Geschichte':    '/historien/',
    'Horror':        '/horror/',
    'Komödie':       '/komodie/',
    'Krieg':         '/krieg/',
    'Krimi':         '/krimi/',
    'Musik':         '/musikfilme/',
    'Mystery':       '/mystery/',
    'Romantik':      '/romantik/',
    'Sci-Fi':        '/sci-fi/',
    'Sport':         '/sport/',
    'Thriller':      '/thriller/',
    'Western':       '/western/',
    'Erotik':        '/erotikfilme/',
}

HOSTER_PRIORITY = {
    'voe': 10,
    'streamruby': 10,
    'mixdrop': 9,
    'streamwish': 8,
    'vidoza': 7,
    'vidguard': 6,
    'doodstream': 5,
    'streamtape': 5,
    'filemoon': 5,
    'upstream': 5,
}
MIN_PRIORITY   = 6
MAX_PER_HOSTER = 5


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _request(sUrl, postData=None):
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('User-Agent', UA)
    oRequest.addHeaderEntry('Referer', URL_MAIN + '/')
    oRequest.addHeaderEntry('Origin', URL_MAIN)
    if postData:
        for k, v in postData.items():
            oRequest.addParameters(k, v)
        oRequest.setRequestType(1)  # POST
    return oRequest.request()


def _parseArticles(sHtml):
    """
    Parst alle <article class="short"> aus einer Listenseite.
    Serien werden übersprungen — nur Filme.
    """
    items = []
    for art in re.findall(r'<article[^>]*class="short"[^>]*>(.*?)</article>', sHtml, re.DOTALL):

        mLink = re.search(r'<h2><a href="([^"]+)">([^<]+)</a>', art)
        if not mLink:
            continue
        sEntryUrl = mLink.group(1).strip()
        sTitle    = mLink.group(2).strip()

        # Serien überspringen
        if 'Staffel' in sTitle or 'Season' in sTitle or 'serie-num' in art:
            continue

        mThumb     = re.search(r'<img src="(/uploads/[^"]+)"', art)
        sThumbnail = (URL_MAIN + mThumb.group(1)) if mThumb else ''

        mYear    = re.search(r'\((\d{4})\)"', art)
        sYear    = mYear.group(1) if mYear else ''

        mQual    = re.search(r'label-\d+">([^<]+)</div>', art)
        sQuality = mQual.group(1).strip() if mQual else ''

        mDesc  = re.search(r'class="st-line st-desc">([^<]+)', art)
        sDesc  = mDesc.group(1).strip() if mDesc else ''

        mTime    = re.search(r'class="s-red">(\d+)\s*min', art)
        sRuntime = mTime.group(1) if mTime else ''

        plot = '[B][COLOR blue]{0}[/COLOR][/B]'.format(SITE_NAME)
        if sYear:
            plot += ' [COLOR yellow]({0})[/COLOR]'.format(sYear)
        if sDesc:
            plot += '[CR]{0}'.format(sDesc[:200])

        item = {
            'title':     sTitle,
            'infoTitle': sTitle,
            'entryUrl':  sEntryUrl,
            'poster':    sThumbnail,
            'isTvshow':  False,
            'quality':   sQuality,
            'year':      sYear,
            'plot':      plot,
        }
        if sRuntime:
            item['duration'] = sRuntime

        items.append(item)
    return items


def _nextPageUrl(sHtml, sCurrentUrl):
    mPage    = re.search(r'/page/(\d+)/?$', sCurrentUrl.rstrip('/'))
    curPage  = int(mPage.group(1)) if mPage else 1
    nextPage = curPage + 1
    baseUrl  = re.sub(r'/page/\d+/?$', '', sCurrentUrl.rstrip('/'))
    sNextUrl = baseUrl + '/page/' + str(nextPage) + '/'
    if '/page/' + str(nextPage) in sHtml:
        return sNextUrl
    return None


def _parseVideoServers(sHtml):
    """Liest alle data-link Stream-URLs aus .video-servers."""
    mSection = re.search(r'class="video-servers"[^>]*>(.*?)</ul>', sHtml, re.DOTALL)
    if not mSection:
        return re.findall(r'data-link="([^"#][^"]*)"', sHtml)
    return re.findall(r'data-link="([^"#][^"]*)"', mSection.group(1))


# ---------------------------------------------------------------------------
# Plugin-Funktionen
# ---------------------------------------------------------------------------

def load():
    addDirectoryItem('Neue Filme',      'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(URL_NEUE_FILME)), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Aktuell im Kino', 'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(URL_KINO)),       SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Demnächst',       'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(URL_DEMNACHST)),  SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Genre',           'runPlugin&site=%s&function=showGenre'                  % SITE_NAME,                               SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Suche',           'runPlugin&site=%s&function=showSearch'                 % SITE_NAME,                               SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showGenre():
    for genre_name in sorted(GENRES.keys()):
        sUrl = URL_MAIN + GENRES[genre_name]
        addDirectoryItem(genre_name, 'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sUrl)), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showEntriesFromUrl():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    showEntries(entryUrl=sUrl)


def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    sUrl   = entryUrl if entryUrl else params.getValue('sUrl')

    try:
        sHtml = _request(sUrl)
    except:
        return

    if not sHtml:
        return

    items = _parseArticles(sHtml)
    if not items:
        return

    if sSearchText:
        items = [i for i in items if sSearchText.lower() in i['title'].lower()]

    xsDirectory(items, SITE_NAME)

    if bGlobal:
        return

    sNextUrl = _nextPageUrl(sHtml, sUrl)
    if sNextUrl:
        addDirectoryItem('[B]>>> Nächste Seite[/B]', 'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sNextUrl)), 'next.png', 'DefaultVideo.png')

    setEndOfDirectory(sorted=False)


def getHosters():
    items  = []
    params = ParameterHandler()
    sUrl   = params.getValue('entryUrl')
    meta   = json.loads(params.getValue('meta'))

    try:
        sHtml = _request(sUrl)
    except:
        return

    if not sHtml:
        return

    sThumbnail = meta.get('poster', '')
    sTitle     = meta.get('infoTitle', '')

    progressDialog.create(SITE_NAME, 'Suche Streams...')

    stream_urls = _parseVideoServers(sHtml)

    progressDialog.update(50, 'Prüfe Hoster...')

    hoster_count = {}
    stream_list  = []

    for sStreamUrl in stream_urls:
        if not sStreamUrl or sStreamUrl.startswith('#'):
            continue

        if sStreamUrl.startswith('//'):
            sStreamUrl = 'https:' + sStreamUrl
        elif sStreamUrl.startswith('/'):
            sStreamUrl = 'https:/' + sStreamUrl

        mHost = re.search(r'//([^/]+)/', sStreamUrl)
        if not mHost:
            continue
        sHoster = mHost.group(1)
        if '.' in sHoster:
            sHoster = sHoster[:sHoster.rindex('.')]

        priority = 0
        for hoster, prio in HOSTER_PRIORITY.items():
            if hoster in sHoster.lower():
                priority = prio
                break
        if priority < MIN_PRIORITY:
            continue

        hoster_key = sHoster.lower()
        hoster_count.setdefault(hoster_key, 0)
        if hoster_count[hoster_key] >= MAX_PER_HOSTER:
            continue
        hoster_count[hoster_key] += 1

        stream_list.append({
            'url':      sStreamUrl,
            'hoster':   sHoster.upper(),
            'priority': priority,
        })

    stream_list.sort(key=lambda x: x['priority'], reverse=True)

    total_streams = len(stream_list)
    for i, stream_data in enumerate(stream_list):
        if total_streams > 0:
            progressDialog.update(
                int(50 + (i / total_streams) * 50),
                'Prüfe {}...'.format(stream_data['hoster'])
            )
        isBlocked, finalUrl = isBlockedHoster(stream_data['url'], resolve=True)
        if not isBlocked:
            items.append((stream_data['hoster'], sTitle, meta, True, finalUrl, sThumbnail))

    progressDialog.close()

    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        return

    try:
        sHtml = _request(
            URL_SEARCH,
            postData={
                'do':        'search',
                'subaction': 'search',
                'story':     sSearchText,
            }
        )
    except:
        return

    if not sHtml:
        return

    items = _parseArticles(sHtml)
    if not items:
        return

    items = [i for i in items if sSearchText.lower() in i['title'].lower()]
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory(sorted=False)


def _search(sSearchText):
    try:
        sHtml = _request(
            URL_SEARCH,
            postData={
                'do':        'search',
                'subaction': 'search',
                'story':     sSearchText,
            }
        )
    except:
        return

    if not sHtml:
        return

    items = _parseArticles(sHtml)
    if not items:
        return

    items = [i for i in items if sSearchText.lower() in i['title'].lower()]
    xsDirectory(items, SITE_NAME)
