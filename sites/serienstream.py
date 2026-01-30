# -*- coding: utf-8 -*-
import json, sys, xbmcgui, re, random
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting, setSetting
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib import log_utils

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
URL_POPULAR = URL_MAIN + '/beliebte-serien'
URL_LOGIN = URL_MAIN + '/login'
URL_SEARCH = URL_MAIN + '/suche?term='

if getSetting('bypassDNSlock') == 'true':
    setSetting('plugin_' + SITE_IDENTIFIER + '.domain', '186.2.175.5')


_HOMEPAGE_CACHE = None
_POPULAR_CACHE = None


def load():
    log_utils.log('========== LOAD ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    username = getSetting('serienstream.user')
    password = getSetting('serienstream.pass')

    if username == '' or password == '':
        xbmcgui.Dialog().ok('SerienStream', 'Bitte Login-Daten in den Einstellungen eintragen!')
    else:
        addDirectoryItem("Alle Serien (A-Z)", 'runPlugin&site=%s&function=showLetters' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Angesagt", 'runPlugin&site=%s&function=showAngesagt' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Aktuell beliebt", 'runPlugin&site=%s&function=showAktuell' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Beliebte Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_POPULAR), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Neu auf S.to", 'runPlugin&site=%s&function=showNeu' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Geheimtipps", 'runPlugin&site=%s&function=showGeheimtipps' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Suchtgefahr", 'runPlugin&site=%s&function=showSuchtgefahr' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Die Beliebtesten", 'runPlugin&site=%s&function=showBeliebtesten' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
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
        oRequest = cRequestHandler('http://186.2.175.5/beliebte-serien', ignoreErrors=True)
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


def showLetters():
    log_utils.log('========== showLetters ==========', log_utils.LOGINFO, SITE_IDENTIFIER)

    letters = ['0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '#']

    for letter in letters:
        addDirectoryItem('[B]%s[/B]' % letter, 'runPlugin&site=%s&function=showAllSeries&sUrl=%s&letter=%s' % (SITE_NAME, URL_SERIES, letter), SITE_ICON, 'DefaultMovies.png')

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
            log_utils.log('_parseNeu: Found %d series with fallback' % len(results), log_utils.LOGINFO, SITE_IDENTIFIER)
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
            serie_slug = sUrl.rstrip('/').split('/')[-1]

            sThumbnail = SITE_ICON
            log_utils.log('No thumbnail for: %s, using default' % sName, log_utils.LOGDEBUG, SITE_IDENTIFIER)

        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, sName, sThumbnail, sUrl), sThumbnail, 'DefaultMovies.png')

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

    aResult = []

    pattern = '<a[^>]*href="([^"]+/serie/[^"]+)"[^>]*>.*?<img[^>]+(?:data-src|src)="([^"]+)"[^>]+alt="([^"]+)"'
    isMatch, result = cParser.parse(sHtmlContent, pattern)

    if isMatch:
        for url, thumb, title in result:
            aResult.append((url, title, thumb))

    if not aResult:
        pattern = '<a[^>]*href="(\\/serie\\/[^"]*)"[^>]*>(.*?)</a>'
        isMatch, result = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for url, title in result:
                aResult.append((url, title, ''))

    if not aResult:
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

        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, sName, sThumbnail, sUrl), sThumbnail if sThumbnail else SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()

def showEntries(entryUrl=False):
    log_utils.log('========== showEntries ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()

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
                title = title_match.group(1) if title_match else ''
                thumb = _extractThumbnail(card_content)
                
                if url and title and url not in [x[0] for x in aResult]:
                    aResult.append((url, title.strip(), thumb))

    if not aResult:
        pattern = r'<a[^>]*href="([^"]+/serie/[^"]+)"[^>]*>.*?<img[^>]+(?:data-src|src)="([^"]+)"[^>]+alt="([^"]+)"'
        isMatch, result = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for url, thumb, title in result:
                if url not in [x[0] for x in aResult]:
                    aResult.append((url, title, thumb))

    if not aResult:
        return

    for sUrl, sName, sThumbnail in aResult:
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, sName, sThumbnail, sUrl), sThumbnail if sThumbnail else SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sThumbnailFromList = params.getValue('sThumbnail') or ''

    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()

    pattern = r'<a[^>]*href="([^"]*/staffel-\d+)"[^>]*data-season-pill="(\d+)"[^>]*>\s*(\d+)\s*<'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, r'<div[^>]*class="series-description"[^>]*>.*?<span[^>]*class="description-text">([^<]+)</span>')
    

    sThumbnail = ''
    thumb_patterns = [
        r'<img[^>]*data-src="([^"]+)"[^>]*class="[^"]*img-fluid[^"]*w-100[^"]*"',
        r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*img-fluid[^"]*w-100[^"]*"',
        r'<picture[^>]*>.*?<img[^>]*(?:data-)?src="([^"]+)"',
    ]
    
    for pattern in thumb_patterns:
        thumb_match = re.search(pattern, sHtmlContent, re.DOTALL)
        if thumb_match:
            sThumbnail = thumb_match.group(1)
            if not sThumbnail.startswith('http'):
                sThumbnail = URL_MAIN + sThumbnail if sThumbnail.startswith('/') else URL_MAIN + '/' + sThumbnail
            break
    

    if not sThumbnail and sThumbnailFromList:
        sThumbnail = sThumbnailFromList

    for sUrl, sNr, _ in aResult:
        sName = 'Staffel %s' % sNr
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEpisodes&TVShowTitle=%s&sThumbnail=%s&sSeason=%s&sUrl=%s' % (SITE_NAME, sTVShowTitle, sThumbnail, sNr, sUrl), sThumbnail if sThumbnail else SITE_ICON, 'DefaultMovies.png')

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

    pattern = r'onclick="window.location=\'([^\']+)\'".*?episode-number-cell">\s*(\d+).*?episode-title-ger"[^>]*>([^<]*)<.*?episode-title-eng"[^>]*>([^<]*)<'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    items = []
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, r'<div[^>]*class="series-description"[^>]*>.*?<span[^>]*class="description-text">([^<]+)</span>')

    for sUrl2, sID, sNameGer, sNameEng in aResult:
        sName = '%d - ' % int(sID)
        sName += sNameGer if sNameGer else sNameEng

        sUrl2 = sUrl2 if sUrl2.startswith('http') else URL_MAIN + sUrl2

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
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('sUrl')

    oRequest = cRequestHandler(sUrl, caching=False)
    sHtmlContent = oRequest.request()

    progressDialog.create('SerienStream', 'Suche Streams...')

    pattern = r'<button[^>]*class="[^"]*link-box[^"]*"[^>]*data-play-url="([^"]+)"[^>]*data-provider-name="([^"]+)"[^>]*data-language-id="([^"]+)"'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        progressDialog.close()
        return

    items = []
    sLanguage = getSetting('prefLanguage', '0')
    t = 0

    for sUrl, sName, sLang in aResult:
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
            hurl = getHosterUrl([sUrl, sName])
            streamUrl = hurl[0]['streamUrl']
            isResolve = hurl[0]['resolved']

            t += 100 / len(aResult)
            progressDialog.update(int(t), sName + sLangLabel)

            if not isBlockedHoster(streamUrl)[0]:
                displayName = sName + sLangLabel
                
                items.append((displayName, displayName, meta, isResolve, streamUrl, meta.get('sThumbnail')))
        except:
            continue

    progressDialog.close()

    if not items:
        return

    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def getHosterUrl(hUrl):
    if type(hUrl) == str:
        hUrl = eval(hUrl)

    Request = cRequestHandler(URL_MAIN + hUrl[0], caching=False)
    Request.addHeaderEntry('Referer', params.getValue('entryUrl') or URL_MAIN)
    Request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    Request.request()
    sUrl = Request.getRealUrl()

    if 'voe' in hUrl[1].lower():
        if 'voe' in sUrl and 'voe.sx' not in sUrl:
            from urllib.parse import urlparse
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
    oRequest = cRequestHandler(URL_SEARCH + sSearchText, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()

    if not sHtmlContent:
        return

    sst = sSearchText.lower()

    pattern = r'<a[^>]*href="([^"]+/serie/[^"]+)"[^>]*class="[^"]*show-cover[^"]*"[^>]*>.*?<h6[^>]*class="show-title[^"]*"[^>]*>([^<]+)</h6>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        pattern = r'<a[^>]*href="([^"]+/serie/[^"]+)"[^>]*class="[^"]*show-cover[^"]*"[^>]*>.*?<img[^>]+alt="([^"]+)"'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    for sUrl, sName in aResult:
        if not sst in sName.lower():
            continue

        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sUrl=%s' % (SITE_NAME, sName, sUrl), SITE_ICON, 'DefaultGenre.png')

    setEndOfDirectory()

