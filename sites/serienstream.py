# -*- coding: utf-8 -*-
import json, sys, xbmcgui, re, random
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting, setSetting
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib import log_utils
import requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'serienstream'
SITE_NAME = 'SerienStream'
SITE_ICON = 'serienstream.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 's.to')

if DOMAIN.replace('.', '').isdigit():
    URL_MAIN = 'http://' + DOMAIN
    REFERER = 'http://' + DOMAIN
else:
    URL_MAIN = 'https://' + DOMAIN
    REFERER = 'https://' + DOMAIN

URL_HOME = URL_MAIN
URL_SERIES = URL_MAIN + '/serien'
URL_NEW_SERIES = URL_MAIN + '/serien?by=alpha'
URL_NEW_EPISODES = URL_MAIN
URL_POPULAR = URL_MAIN + '/beliebte-serien'
URL_LOGIN = URL_MAIN + '/login'
URL_SEARCH = URL_MAIN + '/suche?term='
URL_SEARCH_API = URL_MAIN + '/api/search/suggest?term='

if getSetting('bypassDNSlock') == 'true':
    setSetting('plugin_' + SITE_IDENTIFIER + '.domain', '186.2.175.5')

_HOMEPAGE_CACHE = None
_POPULAR_CACHE = None

def _norm_search_text(value):
    value = (value or '').lower()
    value = re.sub(r'\([^)]*\)', '', value)   
    value = re.sub(r'[^a-z0-9]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def _search_title_match(query, title):
    q_words = _norm_search_text(query).split()
    if not q_words:
        return False

    title_norm = _norm_search_text(title)
    
    for w in q_words:
        if w not in title_norm:
            return False
    return True

def _abs_url(url):
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return URL_MAIN + url if url.startswith('/') else URL_MAIN + '/' + url


def _normalize_series_root(url):
    if not url:
        return ''
    full = _abs_url(url).split('?', 1)[0].split('#', 1)[0].replace('\\/', '/').rstrip('/')
    full = re.sub(r'/staffel-\d+(?:/.*)?$', '', full)
    full = re.sub(r'/episode-\d+(?:/.*)?$', '', full)
    return full



def load():
    log_utils.log('========== LOAD ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    username = getSetting('serienstream.user')
    password = getSetting('serienstream.pass')

    if username == '' or password == '':
        xbmcgui.Dialog().ok('SerienStream', 'Bitte Login-Daten in den Einstellungen eintragen!')
    else:
        addDirectoryItem("Alle Serien (A-Z)", 'runPlugin&site=%s&function=allSeries&sUrl=%s&sCont=catalogNav' % (SITE_NAME, URL_NEW_SERIES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Beliebte Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_POPULAR), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Genre", 'runPlugin&site=%s&function=allSeries&sUrl=%s&sCont=homeContentGenresList' % (SITE_NAME, URL_MAIN + '/serien?by=genre'), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Neu auf S.to", 'runPlugin&site=%s&function=showNeu' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Angesagt", 'runPlugin&site=%s&function=showAngesagt' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Aktuell beliebt", 'runPlugin&site=%s&function=showAktuell' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Geheimtipps", 'runPlugin&site=%s&function=showGeheimtipps' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Suchtgefahr", 'runPlugin&site=%s&function=showSuchtgefahr' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Die Beliebtesten", 'runPlugin&site=%s&function=showBeliebtesten' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Neue Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW_SERIES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Neue Episoden", 'runPlugin&site=%s&function=showNewEpisodes&sUrl=%s' % (SITE_NAME, URL_NEW_EPISODES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()

def _getHomepage(force=False):
    global _HOMEPAGE_CACHE

    if _HOMEPAGE_CACHE is None or force:
        log_utils.log('Loading homepage (Force: %s)' % str(force), log_utils.LOGINFO, SITE_IDENTIFIER)
        oRequest = cRequestHandler(URL_HOME, ignoreErrors=True, caching=(not force))
        
        if not force:
            oRequest.cacheTime = 60 * 30  # 30 Minuten
        sContent = oRequest.request()
        
        if isinstance(sContent, bytes):
            try:
                sContent = sContent.decode('utf-8')
            except:
                sContent = str(sContent)

        _HOMEPAGE_CACHE = sContent
        log_utils.log('Homepage loaded: %d characters' % len(_HOMEPAGE_CACHE) if _HOMEPAGE_CACHE else 0, log_utils.LOGINFO, SITE_IDENTIFIER)
    else:
        log_utils.log('Using global cached homepage', log_utils.LOGINFO, SITE_IDENTIFIER)

    return _HOMEPAGE_CACHE


def _getPopular():
    global _POPULAR_CACHE

    if _POPULAR_CACHE is None:
        log_utils.log('Loading popular page for first time', log_utils.LOGINFO, SITE_IDENTIFIER)
        oRequest = cRequestHandler(URL_POPULAR, ignoreErrors=True)
        oRequest.cacheTime = 60 * 30  # 30 Minuten
        sContent = oRequest.request()
        
        if isinstance(sContent, bytes):
            try:
                sContent = sContent.decode('utf-8')
            except:
                sContent = str(sContent)
                
        _POPULAR_CACHE = sContent
        log_utils.log('Popular loaded: %d characters' % len(_POPULAR_CACHE) if _POPULAR_CACHE else 0, log_utils.LOGINFO, SITE_IDENTIFIER)
    else:
        log_utils.log('Using cached popular page', log_utils.LOGINFO, SITE_IDENTIFIER)

    return _POPULAR_CACHE
    
    
def allSeries():
    log_utils.log('========== allSeries ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sCont = params.getValue('sCont')
    
    oRequest = cRequestHandler(sUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 24  # 24 Stunden Cache
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)
    
    isMatch = False
    aResult = []

    if sCont == 'catalogNav':
        isMatch, aResult = cParser.parse(
            sHtmlContent,
            r'<a[^>]*href="([^"]*/katalog/[^"]+)"[^>]*class="[^"]*alphabet-link[^"]*"[^>]*>\s*([^<]+)\s*<'
        )
        if not isMatch:
            isMatch, aResult = cParser.parse(
                sHtmlContent,
                r'<a[^>]*href="(/katalog/[^"]+)"[^>]*class="[^"]*alphabet-link[^"]*"[^>]*>\s*([^<]+)\s*<'
            )
        if not isMatch:
            isMatch, aResult = cParser.parse(
                sHtmlContent,
                r'<a[^>]*href="([^*]katalog[^"]*)"[^>]*>\s*([A-Z0-9#-]+)\s*</a>'
            )
            
    if not isMatch and sCont == 'homeContentGenresList':
        isMatch, aResult = cParser.parse(
            sHtmlContent,
            r'<div[^>]*class="[^"]*background-1[^"]*"[^>]*>\s*<h3[^>]*>\s*([^<]+)\s*</h3>'
        )
        if isMatch and aResult:
            aResult = [(sUrl, g[0] if isinstance(g, (list, tuple)) else g) for g in aResult]

    if not isMatch or not aResult:
        log_utils.log('allSeries: No results found for sCont=%s' % sCont, log_utils.LOGWARNING, SITE_IDENTIFIER)
        xbmcgui.Dialog().ok('Info', 'Keine Einträge gefunden')
        return
    try:
        aResult.sort(key=lambda x: (not str(x[1]).strip()[0].isdigit(), str(x[1]).lower()))
    except Exception as e:
        log_utils.log('allSeries: Sort failed: %s' % str(e), log_utils.LOGWARNING, SITE_IDENTIFIER)

    for sEntryUrl, sName in aResult:
        sName = sName.strip() if isinstance(sName, str) else str(sName).strip()
        sEntryUrl = _abs_url(sEntryUrl)
        
        if sCont == 'homeContentGenresList':
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s&sGenre=%s' % (SITE_NAME, sEntryUrl, quote_plus(sName)), SITE_ICON, 'DefaultMovies.png')
        else:
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sEntryUrl), SITE_ICON, 'DefaultMovies.png')
    
    setEndOfDirectory()



def showNewEpisodes(entryUrl=False):
    log_utils.log('========== showNewEpisodes ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    if not entryUrl:
        entryUrl = URL_HOME
    
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 4  # 4 Stunden Cache
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)
    
    
    thumbMap = {}
    thumb_pattern = r'<a[^>]*href="([^"]*/serie/([^"/]+))"[^>]*>[\s\S]*?<img[^>]*(?:data-src|src)="([^"]+)"'
    isThumb, thumbResults = cParser.parse(sHtmlContent, thumb_pattern)
    if isThumb:
        for fullUrl, slug, imgUrl in thumbResults:
            if slug and imgUrl and not imgUrl.startswith('data:'):
                thumbMap[slug] = _abs_url(imgUrl)
    pattern = r'<a[^>]*class="[^"]*latest-episode-row[^"]*"[^>]*href="([^"]*/serie/([^"/]+)/staffel-(\d+)/episode-(\d+))"[^>]*>[\s\S]*?<span[^>]*class="ep-title"[^>]*[^>]*>([^<]+)</span>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch or not aResult:
        pattern2 = r'<a[^>]*class="[^"]*latest-episode-row[^"]*"[^>]*href="([^"]*/serie/([^"/]+)/staffel-(\d+)/episode-(\d+))"[^>]*>[\s\S]*?<span[^>]*class="ep-title"[^>]*title="([^"]+)"'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern2)

    if not isMatch or not aResult:
        pattern3 = r'<a[^>]*href="([^"]*/serie/([^"/]+)/staffel-(\d+)/episode-(\d+))"[^>]*class="[^"]*latest-episode-row[^"]*"[^>]*>[\s\S]*?<span[^>]*>([^<]+)</span>'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern3)

    if not isMatch or not aResult:
        log_utils.log('showNewEpisodes: No episodes found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        xbmcgui.Dialog().ok('Info', 'Keine neuen Episoden gefunden')
        return

    seen = set()
    for sUrl, sSeriesSlug, sSeason, sEpisode, sName in aResult:
        fullUrl = _abs_url(sUrl)
        if fullUrl in seen:
            continue
        seen.add(fullUrl)
        
        seriesUrl = re.sub(r'/staffel-\d+/episode-\d+$', '', fullUrl)
        displayTitle = sName.strip()
        
        try:
            seasonNo = int(sSeason)
            episodeNo = int(sEpisode)
        except Exception:
            seasonNo = 0
            episodeNo = 0
        
        if seasonNo > 0 and episodeNo > 0:
            displayTitle = '%s - S%02dE%02d' % (displayTitle, seasonNo, episodeNo)
            
        sThumbnail = thumbMap.get(sSeriesSlug, '')
        if not sThumbnail:
            sThumbnail = URL_MAIN + '/media/images/channel/thumb/' + sSeriesSlug + '?format=jpg'

        addDirectoryItem(displayTitle, 'runPlugin&site=%s&function=getHosters&sUrl=%s&entryUrl=%s&TVShowTitle=%s&sThumbnail=%s' % (SITE_NAME, fullUrl, seriesUrl, quote_plus(sName.strip()), sThumbnail), sThumbnail, 'DefaultMovies.png')

    setEndOfDirectory()



def showAngesagt():
    log_utils.log('========== showAngesagt ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    sHtmlContent = _getPopular()
    if not sHtmlContent:
        xbmcgui.Dialog().ok('Fehler', 'Konnte Seite nicht laden')
        return
    series = _parseSimple(sHtmlContent)
    _displaySeries(series)


def showNeu():
    log_utils.log('========== showNeu ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    sHtmlContent = _getHomepage()
    series = _parseNeuContent(sHtmlContent)
    if not series:
        log_utils.log('showNeu: Cache empty or corrupt, retrying fresh...', log_utils.LOGWARNING, SITE_IDENTIFIER)
        sHtmlContent = _getHomepage(force=True)
        series = _parseNeuContent(sHtmlContent)

    if series:
        _displaySeries(series)
    else:
        log_utils.log('showNeu: No series found after retry', log_utils.LOGERROR, SITE_IDENTIFIER)
        xbmcgui.Dialog().ok('Info', 'Keine Serien gefunden')


def showGeheimtipps():
    log_utils.log('========== showGeheimtipps ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    _showFromHeading('Geheimtipps')


def showSuchtgefahr():
    log_utils.log('========== showSuchtgefahr ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    _showFromHeading('Suchtgefahr')


def showBeliebtesten():
    log_utils.log('========== showBeliebtesten ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    _showFromHeading('Die Beliebtesten')


def showAktuell():
    log_utils.log('========== showAktuell ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    sHtmlContent = _getPopular()
    if not sHtmlContent:
        xbmcgui.Dialog().ok('Fehler', 'Konnte Seite nicht laden')
        return
    series = _parseSimple(sHtmlContent)
    _displaySeries(series[::2])


def _showFromHeading(heading_text):
    sHtmlContent = _getHomepage()
    series = _parseHeadingContent(sHtmlContent, heading_text)

    if not series:
        log_utils.log('Heading "%s" not found/empty, retrying fresh...' % heading_text, log_utils.LOGWARNING, SITE_IDENTIFIER)
        sHtmlContent = _getHomepage(force=True)
        series = _parseHeadingContent(sHtmlContent, heading_text)

    if series:
        _displaySeries(series)
    else:
        log_utils.log('No section found for heading: %s' % heading_text, log_utils.LOGERROR, SITE_IDENTIFIER)
        xbmcgui.Dialog().ok('Info', 'Keine Serien gefunden für: %s' % heading_text)


def _parseNeuContent(sHtmlContent):
    if not sHtmlContent: 
        return []
    pattern = 'id="section-1"[^>]*>(.*?)<div[^>]*id="section-'
    isMatch, section = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        pattern = 'id="section-1"[^>]*>(.*?)$'
        isMatch, section = cParser.parseSingleResult(sHtmlContent, pattern)

    if isMatch and section:
        return _parseNeu(section)
    return []


def _parseHeadingContent(sHtmlContent, heading_text):
    if not sHtmlContent: return []

    log_utils.log('Looking for heading: %s' % heading_text, log_utils.LOGINFO, SITE_IDENTIFIER)

    patterns = [
        '<h4[^>]*class="[^"]*mb-2[^"]*h5[^"]*fw-bold[^"]*text-primary[^"]*"[^>]*>%s</h4>.*?<ul[^>]*class="[^"]*discover-list[^"]*"[^>]*>(.*?)</ul>' % heading_text,
        '>%s</h4>.*?<ul[^>]*>(.*?)</ul>' % heading_text,
        '>%s</h4>.*?<div[^>]*class="row"[^>]*>(.*?)</div>\\s*</div>' % heading_text
    ]

    section = None
    for idx, pattern in enumerate(patterns, 1):
        isMatch, section = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatch and section:
            log_utils.log('Pattern %d matched for %s' % (idx, heading_text), log_utils.LOGINFO, SITE_IDENTIFIER)
            break

    if section:
        return _parseList(section)
    return []


def _extractThumbnail(html_content):
    patterns = [
        r'<img[^>]*data-src="([^"]+)"',
        r'<source[^>]*data-srcset="([^\s"]+)',
        r'<source[^>]*\ssrcset="([^\s"]+)',
        r'<img[^>]*src="((?:https?://[^"]+)?/media/[^"]+)"',
        r'<img[^>]*src="(https?://[^"]+/media/[^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            thumb = match.group(1)
            thumb = thumb.split()[0].rstrip(',')
            if thumb.startswith('data:'):
                continue
            return thumb
    
    return ''

def _parseSimple(sHtmlContent):
    """Parst Serien mit show-card Struktur"""
    aResult = []
    
    card_pattern = r'<a\s+href="([^"]*)"[^>]*class="[^"]*show-card[^"]*"[^>]*>(.*?)</a>'
    isMatch, cards = cParser.parse(sHtmlContent, card_pattern)
    
    if isMatch:
        for url, card_content in cards:
            if '/serie/' not in url:
                continue
            title_match = re.search(r'alt="([^"]+)"', card_content)
            if not title_match:
                title_match = re.search(r'<h6[^>]*>([^<]+)</h6>', card_content)
            title = title_match.group(1) if title_match else ''
            thumb = _extractThumbnail(card_content)
            if url and title and url not in [x[0] for x in aResult]:
                aResult.append((url, title.strip(), thumb))
                
    if not aResult:
        card_pattern2 = r'<a[^>]*class="[^"]*show-card[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        isMatch, cards = cParser.parse(sHtmlContent, card_pattern2)
        if isMatch:
            for url, card_content in cards:
                if '/serie/' not in url:
                    continue
                title_match = re.search(r'alt="([^"]+)"', card_content)
                if not title_match:
                    title_match = re.search(r'<h6[^>]*>([^<]+)</h6>', card_content)
                title = title_match.group(1) if title_match else ''
                thumb = _extractThumbnail(card_content)
                if url and title and url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))
                    
    if not aResult:
        pattern = r'<a[^>]*href="([^"]*serie/[^"]+)"[^>]*>.*?<img[^>]+(?:data-src|src)="([^"]+)"[^>]*alt="([^"]+)"'
        isMatch, results = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for url, thumb, title in results:
                if url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))

    return aResult


def _parseNeu(section_content):
    aResult = []
    
    col_pattern = r'<div[^>]*class="col[^"]*"[^>]*>(.*?)</div>\s*(?=<div[^>]*class="col|$)'
    isMatch, cols = cParser.parse(section_content, col_pattern)
    
    if isMatch:
        for col_content in cols:
            url_match = re.search(r'href="([^"]*serie/[^"]+)"', col_content)
            if not url_match:
                continue
            url = url_match.group(1)
            
            title = ''
            title_match = re.search(r'alt="([^"]+)"', col_content)
            if title_match:
                title = title_match.group(1)
            else:
                title_match = re.search(r'title="([^"]+)"', col_content)
                if title_match:
                    title = title_match.group(1)
                else:
                    title_match = re.search(r'<h6[^>]*>.*?<a[^>]*>([^<]+)</a>', col_content, re.DOTALL)
                    if title_match:
                        title = title_match.group(1)
            
            thumb = _extractThumbnail(col_content)
            
            if url and title and url not in [x[0] for x in aResult]:
                aResult.append((url, title.strip(), thumb))
                
    if not aResult:
        pattern = r'<a href="(/serie/[^"]+)"[^>]*>.*?<img[^>]+(?:data-src|src)="([^"]+)"[^>]*>.*?<h3[^>]*>\s*<span>([^<]+)</span>'
        isMatch, results = cParser.parse(section_content, pattern)
        if isMatch and results:
            for url, thumb, title in results:
                if url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))

    return aResult


def _parseList(section_content):
    aResult = []
    
    li_pattern = r'<li[^>]*class="[^"]*d-flex[^"]*"[^>]*>(.*?)</li>'
    isMatch, li_items = cParser.parse(section_content, li_pattern)

    if isMatch and li_items:
        for li_content in li_items:
            url_match = re.search(r'href="(/serie/[^"]+)"', li_content)
            if not url_match:
                url_match = re.search(r'href="([^"]*serie/[^"]+)"', li_content)
            if not url_match:
                continue
            sUrl = url_match.group(1)
            
            sTitle = ''
            title_match = re.search(r'<span[^>]*class="[^"]*d-block[^"]*fw-semibold[^"]*"[^>]*>([^<]+)</span>', li_content)
            if title_match:
                sTitle = title_match.group(1)
            else:
                title_match = re.search(r'alt="([^"]+)"', li_content)
                if title_match:
                    sTitle = title_match.group(1)
                else:
                    title_match = re.search(r'title="([^"]+)"', li_content)
                    if title_match:
                        sTitle = title_match.group(1)
            
            if not sTitle:
                continue
                
            sThumbnail = _extractThumbnail(li_content)

            if sUrl not in [x[0] for x in aResult]:
                aResult.append((sUrl, sTitle.strip(), sThumbnail))
                
    if not aResult:
        simple_pattern = r'<li[^>]*>.*?<a[^>]*href="([^"]*serie/[^"]+)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]+)"[^>]*alt="([^"]+)"'
        isMatch, results = cParser.parse(section_content, simple_pattern)
        if isMatch:
            for url, thumb, title in results:
                if url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))

    return aResult


def _displaySeries(series_list):
    if not series_list:
        return

    for sUrl, sName, sThumbnail in series_list:
        if not sUrl.startswith('http'):
            sUrl = URL_MAIN + sUrl if sUrl.startswith('/') else URL_MAIN + '/' + sUrl

        if sThumbnail:
            if not sThumbnail.startswith('http'):
                sThumbnail = URL_MAIN + sThumbnail if sThumbnail.startswith('/') else URL_MAIN + '/' + sThumbnail
        else:
            sThumbnail = SITE_ICON
            log_utils.log('No thumbnail for: %s, using default' % sName, log_utils.LOGDEBUG, SITE_IDENTIFIER)

        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, quote_plus(sName), sThumbnail, sUrl), sThumbnail, 'DefaultMovies.png')

    setEndOfDirectory()

def showAllSeries(entryUrl=False, sSearchText=False):
    log_utils.log('========== showAllSeries ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()

    if not entryUrl:
        entryUrl = params.getValue('sUrl')

    letter = params.getValue('letter')

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)

    aResult = []
    
    card_mini_pattern = r'<div[^>]*class="[^"]*card-mini[^"]*"[^>]*>(.*?)</div>\s*</div>'
    isMatch, cards = cParser.parse(sHtmlContent, card_mini_pattern)
    
    if isMatch:
        for card_content in cards:
            url_match = re.search(r'href="([^"]*serie/[^"]+)"', card_content)
            if not url_match:
                continue
            url = url_match.group(1)
            
            title_match = re.search(r'<h6[^>]*>([^<]+)</h6>', card_content)
            if not title_match:
                title_match = re.search(r'alt="([^"]+)"', card_content)
            if not title_match:
                continue
            title = title_match.group(1).strip()
            if title.endswith(' backdrop'):
                title = title[:-9]
            
            thumb = _extractThumbnail(card_content)
            
            if url and title and url not in [x[0] for x in aResult]:
                aResult.append((url, title, thumb))
                
    if not aResult:
        card_pattern = r'<a\s+href="([^"]*)"[^>]*class="[^"]*show-card[^"]*"[^>]*>(.*?)</a>'
        isMatch, cards = cParser.parse(sHtmlContent, card_pattern)
        
        if isMatch:
            for url, card_content in cards:
                if '/serie/' not in url:
                    continue
                title_match = re.search(r'alt="([^"]+)"', card_content)
                if not title_match:
                    title_match = re.search(r'<h6[^>]*>([^<]+)</h6>', card_content)
                title = title_match.group(1) if title_match else ''
                thumb = _extractThumbnail(card_content)
                if url and title and url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))
                    
    if not aResult:
        pattern = r'<a[^>]*href="([^"]+/serie/[^"]+)"[^>]*>.*?<img[^>]+(?:data-src|src)="([^"]+)"[^>]+alt="([^"]+)"'
        isMatch, result = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for url, thumb, title in result:
                aResult.append((url, title, thumb))

    if not aResult:
        pattern = r'<a[^>]*href="(\\/serie\\/[^"]*)"[^>]*>(.*?)</a>'
        isMatch, result = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for url, title in result:
                aResult.append((url, title, ''))

    if not aResult:
        log_utils.log('showAllSeries: No series found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    for sUrl, sName, sThumbnail in aResult:
        if sSearchText and not sSearchText.lower() in sName.lower():
            continue

        if letter:
            first_char = sName[0].upper()
            if letter == '0-9':
                if not first_char.isdigit():
                    continue
            elif letter == '#':
                if first_char.isalnum():
                    continue
            else:
                if first_char != letter:
                    continue

        if not sUrl.startswith('http'):
            sUrl = URL_MAIN + sUrl if sUrl.startswith('/') else URL_MAIN + '/' + sUrl

        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail if sThumbnail.startswith('/') else URL_MAIN + '/' + sThumbnail

        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, quote_plus(sName), sThumbnail, sUrl), sThumbnail if sThumbnail else SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()


def showEntries(entryUrl=False):
    log_utils.log('========== showEntries ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    
    sGenre = params.getValue('sGenre')

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)

    aResult = []
    isMatch = False
    
    if sGenre:
        escaped = re.escape(sGenre)
        isBlock, sContainer = cParser.parseSingleResult(
            sHtmlContent,
            r'<div[^>]*class="[^"]*background-1[^"]*"[^>]*>\s*<h3[^>]*>\s*%s\s*</h3>[\s\S]*?</div>\s*<ul[^>]*class="[^"]*series-list[^"]*"[^>]*>([\s\S]*?)</ul>' % escaped
        )
        if isBlock and sContainer:
            isMatch, aResult = cParser.parse(
                sContainer,
                r'<a[^>]*href="([^"]*/serie/[^"]+)"[^>]*>\s*([^<]+)\s*</a>'
            )
            
    if not isMatch:
        isMatch, aResult = cParser.parse(
            sHtmlContent,
            r'<li[^>]*class="[^"]*series-item[^"]*"[^>]*>\s*<a[^>]*href="([^"]*/serie/[^"]+)"[^>]*>([^<]+)</a>'
        )
        
    if not isMatch:
        card_pattern = r'<a\s+href="([^"]*)"[^>]*class="[^"]*show-card[^"]*"[^>]*>(.*?)</a>'
        isMatch, cards = cParser.parse(sHtmlContent, card_pattern)
        if isMatch:
            for url, card_content in cards:
                if '/serie/' not in url:
                    continue
                title_match = re.search(r'alt="([^"]+)"', card_content)
                if not title_match:
                    title_match = re.search(r'<h6[^>]*>([^<]+)</h6>', card_content)
                title = title_match.group(1) if title_match else ''
                thumb = _extractThumbnail(card_content)
                if url and title and url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))
                    
    if not aResult:
        card_pattern2 = r'<a[^>]*class="[^"]*show-card[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        isMatch, cards = cParser.parse(sHtmlContent, card_pattern2)
        if isMatch:
            for url, card_content in cards:
                if '/serie/' not in url:
                    continue
                title_match = re.search(r'alt="([^"]+)"', card_content)
                title = title_match.group(1) if title_match else ''
                thumb = _extractThumbnail(card_content)
                if url and title and url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))
                    
    if not aResult:
        isMatch, aResult = cParser.parse(
            sHtmlContent,
            r'<a[^>]*href="([^"]*/serie/[^"]+)"[^>]*class="[^"]*show-cover[^"]*"[^>]*>[\s\S]*?<img[^>]+alt="([^"]+)"'
        )
        
    if not aResult:
        pattern = r'<a[^>]*href="([^"]+/serie/[^"]+)"[^>]*>.*?<img[^>]+(?:data-src|src)="([^"]+)"[^>]+alt="([^"]+)"'
        isMatch, result = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for url, thumb, title in result:
                if url not in [x[0] for x in aResult]:
                    aResult.append((url, title, thumb))

    if not aResult:
        log_utils.log('showEntries: No entries found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    
    thumbMap = {}
    if 'show-card' in sHtmlContent or 'show-cover' in sHtmlContent:
        isThumb, thumbResult = cParser.parse(
            sHtmlContent,
            r'<a[^>]*href="([^"]*/serie/[^"]+)"[^>]*>[\s\S]*?<img[^>]*(?:data-src|src)="([^"]+)"[^>]*>'
        )
        if isThumb:
            for tUrl, tImg in thumbResult:
                key = _normalize_series_root(tUrl)
                if key and key not in thumbMap:
                    thumbMap[key] = _abs_url(tImg)
                    
    seen = set()
    for item in aResult:
        if len(item) == 2:
            sUrl, sName = item
            sThumbnail = ''
        else:
            sUrl, sName, sThumbnail = item[0], item[1], item[2] if len(item) > 2 else ''
        
        sUrl = sUrl.strip()
        sName = sName.strip() if isinstance(sName, str) else str(sName).strip()
        
        if not sUrl or not sName:
            continue
        
        fullUrl = _normalize_series_root(sUrl)
        if '/serie/' not in fullUrl:
            continue
        
        key = (fullUrl.lower(), sName.lower())
        if key in seen:
            continue
        seen.add(key)
        
        if not sThumbnail:
            sThumbnail = thumbMap.get(fullUrl, '')
        
        sUrl = _abs_url(sUrl)
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = _abs_url(sThumbnail)

        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, quote_plus(sName), sThumbnail, sUrl), sThumbnail if sThumbnail else SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()




def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sThumbnailFromList = params.getValue('sThumbnail') or ''

    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)

    pattern = r'<a[^>]*href="([^"]*/staffel-\d+)"[^>]*data-season-pill="(\d+)"[^>]*>\s*(\d+)\s*<'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, r'<div[^>]*class="series-description"[^>]*>.*?<span[^>]*class="description-text">([^<]+)</span>')
    
    
    sThumbnail = ''
    thumb_patterns = [
        r'show-cover-mobile[\s\S]*?<img[^>]*(?:data-src|src)="([^"]+)"',
        r'show-cover[^>]*>[\s\S]*?<img[^>]*(?:data-src|src)="([^"]+)"',
        r'<img[^>]*(?:data-src|src)="([^"]*/media/images/channel/[^"]+)"',
        r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*img-fluid[^"]*w-100[^"]*"',
        r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*img-fluid[^"]*w-100[^"]*"',
        r'<picture[^>]*>.*?<img[^>]*(?:data-)?src="([^"]+)"',
    ]
    
    for pattern in thumb_patterns:
        thumb_match = re.search(pattern, sHtmlContent, re.DOTALL)
        if thumb_match:
            sThumbnail = thumb_match.group(1)
            sThumbnail = _abs_url(sThumbnail)
            break
    
    if not sThumbnail and sThumbnailFromList:
        sThumbnail = sThumbnailFromList

    for sSeasonUrl, sNr, _ in aResult:
        sName = 'Staffel %s' % sNr
        sSeasonUrl = _abs_url(sSeasonUrl)
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEpisodes&TVShowTitle=%s&sThumbnail=%s&sSeason=%s&sUrl=%s' % (SITE_NAME, quote_plus(sTVShowTitle), sThumbnail, sNr, sSeasonUrl), sThumbnail if sThumbnail else SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sSeason = params.getValue('sSeason') or '0'
    sThumbnail = params.getValue('sThumbnail') or ''

    isMovieList = sUrl.endswith('filme')

    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 4
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)

    pattern = r'onclick="window.location=\'([^\']+)\'".*?episode-number-cell">\s*(\d+).*?episode-title-ger"[^>]*>([^<]*)<.*?episode-title-eng"[^>]*>([^<]*)<'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    items = []
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, r'<div[^>]*class="series-description"[^>]*>.*?<span[^>]*class="description-text">([^<]+)</span>')

    for sUrl2, sID, sNameGer, sNameEng in aResult:
        sName = '%d - ' % int(sID)
        sName += sNameGer if sNameGer else sNameEng

        sUrl2 = _abs_url(sUrl2)

        item = {}
        item['TVShowTitle'] = sTVShowTitle
        item['title'] = sName
        item['infoTitle'] = sName
        item['sUrl'] = sUrl2
        item['entryUrl'] = sUrl
        item['isTvshow'] = False
        item['poster'] = sThumbnail
        item['sThumbnail'] = sThumbnail
        item['fanart'] = sThumbnail
        item['plot'] = sDesc if isDesc else ''
        item['mediatype'] = 'movie' if isMovieList else 'episode'

        if not isMovieList:
            item['season'] = int(sSeason)
            item['episode'] = int(sID)

        items.append(item)

    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()



def getHosters():
    log_utils.log('========== getHosters ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    
    metaStr = params.getValue('meta')
    if metaStr:
        try:
            meta = json.loads(metaStr)
            sUrl = meta.get('sUrl')
        except:
            sUrl = params.getValue('sUrl')
            meta = {}
    else:
        sUrl = params.getValue('sUrl')
        meta = {'sUrl': sUrl, 'sThumbnail': params.getValue('sThumbnail') or ''}

    if not sUrl:
        return

    oRequest = cRequestHandler(sUrl, caching=False)
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)

    progressDialog.create('SerienStream', 'Suche Streams...')

    pattern = r'<button[^>]*class="[^"]*link-box[^"]*"[^>]*data-play-url="([^"]+)"[^>]*data-provider-name="([^"]+)"[^>]*data-language-id="([^"]+)"'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        progressDialog.close()
        return

    items = []
    sLanguage = getSetting('prefLanguage', '0')
    t = 0

    for sHosterUrl, sName, sLang in aResult:
        if sLanguage == '1' and sLang != '1':
            continue
        elif sLanguage == '2' and sLang != '2':
            continue

        if sLang == '1':
            sLangLabel = ' (DE)'
        elif sLang == '2':
            sLangLabel = ' (EN)'
        elif sLang == '3':
            sLangLabel = ' (EN/DE-Sub)'
        else:
            sLangLabel = ''

        try:
            hurl = getHosterUrl([sHosterUrl, sName])
            streamUrl = hurl[0]['streamUrl']
            isResolve = hurl[0]['resolved']

            t += 100 / len(aResult)
            progressDialog.update(int(t), sName + sLangLabel)

            if not isBlockedHoster(streamUrl)[0]:
                displayName = sName + sLangLabel
                items.append((displayName, displayName, meta, isResolve, streamUrl, meta.get('sThumbnail', '')))
        except:
            continue

    progressDialog.close()

    if not items:
        return

    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def getHosterUrl(hUrl):
    if isinstance(hUrl, str):
        hUrl = eval(hUrl)

    target_url = URL_MAIN + hUrl[0]
    referer = ParameterHandler().getValue('entryUrl') or URL_MAIN

    headers = {
        'Referer': referer,
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = session.get(target_url, headers=headers, timeout=10)
        sUrl = response.url  
    except:
        sUrl = target_url
    

    if 'voe' in hUrl[1].lower():
        if 'voe' in sUrl and 'voe.sx' not in sUrl:
            parsed = urlparse(sUrl)
            sUrl = sUrl.replace(parsed.netloc, 'voe.sx')

    return [{'streamUrl': sUrl, 'resolved': False}]



def showSearch():
    try:
        from resources.lib.gui.gui import cGui
        sSearchText = cGui().showKeyBoard()
    except:
        sSearchText = xbmcgui.Dialog().input('Suche', type=xbmcgui.INPUT_ALPHANUM)

    if sSearchText:
        SSsearch(sSearchText)


def _search(sSearchText):
    SSsearch(sSearchText, bGlobal=True)


def SSsearch(sSearchText=False, bGlobal=False):
    if not sSearchText:
        return
    quoted = quote(sSearchText)
    aResult = []
    seen = set()
    try:
        oRequest = cRequestHandler(URL_SEARCH_API + quoted, caching=False, ignoreErrors=True)
        oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        sApiContent = oRequest.request()

        if sApiContent:
            data = json.loads(sApiContent)
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ['shows', 'series', 'movies', 'results']:
                    if key in data and isinstance(data[key], list):
                        items.extend(data[key])
            
            for item in items:
                title = (item.get('name') or item.get('title') or '').strip()
                link = (item.get('url') or item.get('link') or '').strip()
                
                if not title or not link: continue
                if sSearchText.lower() in title.lower() or _search_title_match(sSearchText, title):
                    full_url = _abs_url(link)
                    if full_url not in seen:
                        thumb = (item.get('image') or item.get('img') or '').strip()
                        if not thumb:
                            slug = full_url.rstrip('/').split('/')[-1]
                            thumb = URL_MAIN + '/media/images/channel/thumb/' + slug + '.png'
                        
                        seen.add(full_url)
                        aResult.append((full_url, title, _abs_url(thumb)))
    except:
        pass
    if not aResult:
        oRequest = cRequestHandler(URL_SEARCH + quote_plus(sSearchText), ignoreErrors=True)
        sHtmlContent = oRequest.request()

        if sHtmlContent:
            patterns = [
                r'href="([^"]+/serie/[^"]+)"[^>]*>[\s\S]*?<img[^>]+alt="([^"]+)"',
                r'href="(/serie/[^"]+)"[^>]*title="([^"]+)"',
                r'href="(/serie/[^"]+)"[^>]*>([^<]+)</a>'
            ]
            for p in patterns:
                isMatch, html_res = cParser.parse(sHtmlContent, p)
                if isMatch:
                    for sUrl, sName in html_res:
                        if sSearchText.lower() in sName.lower():
                            full_url = _abs_url(sUrl)
                            if full_url not in seen:
                                slug = full_url.rstrip('/').split('/')[-1]
                                thumb = URL_MAIN + '/media/images/channel/thumb/' + slug + '.png'
                                seen.add(full_url)
                                aResult.append((full_url, sName, thumb))
                                
    if not aResult:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Treffer für: ' + sSearchText)
        return

    for sUrl, sName, sThumbnail in aResult:
        addDirectoryItem(
            sName,
            'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s'
            % (SITE_NAME, quote_plus(sName), sThumbnail, sUrl),
            sThumbnail,
            'DefaultGenre.png'
        )

    setEndOfDirectory()


def getMetaInfo(link, title):
    oRequest = cRequestHandler(_abs_url(link), caching=False)
    sHtmlContent = oRequest.request()
    
    if isinstance(sHtmlContent, bytes):
        try:
            sHtmlContent = sHtmlContent.decode('utf-8')
        except:
            sHtmlContent = str(sHtmlContent)
    
    if not sHtmlContent:
        return '', ''

    patterns = [
        r'show-cover-mobile[\s\S]*?(?:data-src|src)="([^"]+)"[\s\S]*?class="series-description"[\s\S]*?<span[^>]*class="description-text">([^<]+)</span>',
        r'<img[^>]*(?:data-src|src)="([^"]*/media/images/channel/[^"]+)"[\s\S]*?class="series-description"[\s\S]*?<span[^>]*class="description-text">([^<]+)</span>',
        r'<img[^>]*(?:data-src|src)="([^"]+)"[\s\S]*?class="series-description"[\s\S]*?<span[^>]*class="description-text">([^<]+)</span>'
    ]
    
    for pattern in patterns:
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if not isMatch:
            continue
        for sImg, sDescr in aResult:
            return _abs_url(sImg), sDescr
    
    return '', ''
