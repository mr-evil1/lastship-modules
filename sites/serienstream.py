# -*- coding: utf-8 -*-
import json, sys, xbmcgui, re
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
    proxy = 'true'
    log_utils.log('Using IP/Proxy: %s' % DOMAIN, log_utils.LOGDEBUG, SITE_IDENTIFIER)
else:
    URL_MAIN = 'https://' + DOMAIN
    REFERER = 'https://' + DOMAIN
    proxy = 'false'
    log_utils.log('Using domain: %s' % DOMAIN, log_utils.LOGDEBUG, SITE_IDENTIFIER)

URL_SERIES = URL_MAIN + '/serien'
URL_NEW_SERIES = URL_MAIN + '/neu'
URL_NEW_EPISODES = URL_MAIN + '/neue-episoden'
URL_POPULAR = URL_MAIN + '/beliebte-serien'
URL_LOGIN = URL_MAIN + '/login'

if getSetting('bypassDNSlock') == 'true':
    setSetting('plugin_' + SITE_IDENTIFIER + '.domain', '186.2.175.5')
    log_utils.log('DNS Bypass activated - switching to 186.2.175.5', log_utils.LOGINFO, SITE_IDENTIFIER)


def load():
    """Menu structure of the site plugin"""
    log_utils.log('========== LOAD START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    username = getSetting('serienstream.user')
    password = getSetting('serienstream.pass')
    
    log_utils.log('Username configured: %s' % ('Yes' if username else 'No'), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    log_utils.log('Password configured: %s' % ('Yes' if password else 'No'), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    if username == '' or password == '':
        log_utils.log('No credentials - showing dialog', log_utils.LOGWARNING, SITE_IDENTIFIER)
        xbmcgui.Dialog().ok('SerienStream', 'Bitte Login-Daten in den Einstellungen eintragen!')
    else:
        log_utils.log('Building menu items', log_utils.LOGDEBUG, SITE_IDENTIFIER)
        addDirectoryItem("Alle Serien", 'runPlugin&site=%s&function=showAllSeries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Neue Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW_SERIES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Neue Folgen", 'runPlugin&site=%s&function=showNewEpisodes&sUrl=%s' % (SITE_NAME, URL_NEW_EPISODES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Beliebte Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_POPULAR), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Von A-Z", 'runPlugin&site=%s&function=showValue&sCont=%s&sUrl=%s' % (SITE_NAME, 'catalogNav', URL_MAIN), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Genre", 'runPlugin&site=%s&function=showValue&sCont=%s&sUrl=%s' % (SITE_NAME, 'homeContentGenresList', URL_MAIN), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()
    log_utils.log('========== LOAD END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def showValue():
    log_utils.log('========== showValue START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    log_utils.log('Fetching URL: %s' % sUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    log_utils.log('HTML content length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, '<ul[^>]*class="%s"[^>]*>(.*?)<\\/ul>' % params.getValue('sCont'))
    if isMatch:
        log_utils.log('Container found', log_utils.LOGDEBUG, SITE_IDENTIFIER)
        isMatch, aResult = cParser.parse(sContainer, '<li>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)<\\/a>\s*<\\/li>')
    if not isMatch:
        log_utils.log('No matches found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    log_utils.log('Found %d items' % len(aResult), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    for sUrl, sName in aResult:
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()
    log_utils.log('========== showValue END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def showAllSeries(entryUrl=False, sSearchText=False, bGlobal=False):
    log_utils.log('========== showAllSeries START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    
    log_utils.log('URL: %s' % entryUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    pattern = '<a[^>]*href="(\\/serie\\/[^"]*)"[^>]*>(.*?)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    
    if not isMatch:
        log_utils.log('No series found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    log_utils.log('Found %d series' % len(aResult), log_utils.LOGINFO, SITE_IDENTIFIER)
    total = len(aResult)
    for sUrl, sName in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&mediatype=%s&sUrl=%s' % (SITE_NAME, sName, 'tvshow', URL_MAIN + sUrl), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()
    log_utils.log('========== showAllSeries END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def showNewEpisodes(entryUrl=False, bGlobal=False):
    log_utils.log('========== showNewEpisodes START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    
    log_utils.log('URL: %s' % entryUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 4
    sHtmlContent = oRequest.request()
    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    pattern = '<div[^>]*class="col-md-[^"]*"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>\s*<strong>([^<]+)</strong>\s*<span[^>]*>([^<]+)</span>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    
    if not isMatch:
        log_utils.log('No episodes found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    log_utils.log('Found %d new episodes' % len(aResult), log_utils.LOGINFO, SITE_IDENTIFIER)
    total = len(aResult)
    for sUrl, sName, sInfo in aResult:
        sMovieTitle = sName + ' ' + sInfo
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&mediatype=%s&sUrl=%s' % (SITE_NAME, sMovieTitle, 'tvshow', URL_MAIN + sUrl), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()
    log_utils.log('========== showNewEpisodes END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def showEntries(entryUrl=False, bGlobal=False):
    log_utils.log('========== showEntries START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    
    log_utils.log('URL: %s' % entryUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    pattern = '<div[^>]*class="col-md-[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?data-src="([^"]*).*?<h3>(.*?)<span[^>]*class="paragraph-end">.*?</div>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    
    if not isMatch:
        log_utils.log('No entries found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return
    
    log_utils.log('Found %d entries' % len(aResult), log_utils.LOGINFO, SITE_IDENTIFIER)
    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        sThumbnail = URL_MAIN + sThumbnail
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&mediatype=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, sName, 'tvshows', sThumbnail, URL_MAIN + sUrl), sThumbnail, 'DefaultMovies.png')

    if not bGlobal:
        pattern = 'pagination">.*?<a href="([^"]+)">&gt;</a>.*?</a></div>'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            log_utils.log('Next page found: %s' % sNextUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
            params.setParam('sUrl', sNextUrl)
            addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()
    log_utils.log('========== showEntries END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def showSeasons():
    log_utils.log('========== showSeasons START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    
    log_utils.log('URL: %s' % sUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    log_utils.log('TV Show: %s' % sTVShowTitle, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    pattern = '<div[^>]*class="hosterSiteDirectNav"[^>]*>.*?<ul>(.*?)<\\/ul>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        log_utils.log('Navigation container found', log_utils.LOGDEBUG, SITE_IDENTIFIER)
        pattern = '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>.*?'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    
    if not isMatch:
        log_utils.log('No seasons found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    log_utils.log('Found %d seasons/movies' % len(aResult), log_utils.LOGINFO, SITE_IDENTIFIER)
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '<p[^>]*data-full-description="(.*?)"[^>]*>')
    isThumbnail, sThumbnail = cParser.parseSingleResult(sHtmlContent, '<div[^>]*class="seriesCoverBox"[^>]*>.*?data-src="([^"]*)"[^>]*>')
    if isThumbnail:
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        log_utils.log('Thumbnail: %s' % sThumbnail, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    else:
        sThumbnail = ''

    total = len(aResult)
    for sUrl, sName, sNr in aResult:
        isMovie = sUrl.endswith('filme')
        if 'Alle Filme' in sName:
            sName = 'Filme'

        mediatype = 'season' if not isMovie else 'movie'
        log_utils.log('Adding - %s (Type: %s)' % (sName, mediatype), log_utils.LOGDEBUG, SITE_IDENTIFIER)
        
        if not isMovie:
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showEpisodes&TVShowTitle=%s&mediatype=%s&sThumbnail=%s&sSeason=%s&sUrl=%s' % (SITE_NAME, sName, mediatype, sThumbnail, sNr, URL_MAIN + sUrl), sThumbnail, 'DefaultMovies.png')
        else:
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showEpisodes&TVShowTitle=%s&mediatype=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME, sName, mediatype, sThumbnail, URL_MAIN + sUrl), sThumbnail, 'DefaultMovies.png')
    setEndOfDirectory()
    log_utils.log('========== showSeasons END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def showEpisodes():
    log_utils.log('========== showEpisodes START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sSeason = params.getValue('sSeason')
    sThumbnail = params.getValue('sThumbnail')
    
    log_utils.log('URL: %s' % sUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    log_utils.log('Show: %s, Season: %s' % (sTVShowTitle, sSeason), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    if not sSeason:
        sSeason = '0'
    
    isMovieList = sUrl.endswith('filme')
    log_utils.log('Is movie list: %s' % isMovieList, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 4
    sHtmlContent = oRequest.request()
    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    pattern = '<table[^>]*class="seasonEpisodesList"[^>]*>(.*?)</table>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        log_utils.log('Episodes table found', log_utils.LOGDEBUG, SITE_IDENTIFIER)
        if isMovieList == True:
            pattern = '<tr[^>]*data-episode-season-id="(\\d+).*?<a href="([^"]+)">\\s([^<]+).*?<strong>([^<]+)'
            isMatch, aResult = cParser.parse(sContainer, pattern)
            if not isMatch:
                pattern = '<tr[^>]*data-episode-season-id="(\\d+).*?<a href="([^"]+)">\\s([^<]+).*?<span>([^<]+)'
                isMatch, aResult = cParser.parse(sContainer, pattern)
        else:
            pattern = '<tr[^>]*data-episode-season-id="(\\d+).*?<a href="([^"]+).*?(?:<strong>(.*?)</strong>.*?)?(?:<span>(.*?)</span>.*?)?<'
            isMatch, aResult = cParser.parse(sContainer, pattern)
    
    if not isMatch:
        log_utils.log('No episodes found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return
    
    log_utils.log('Found %d episodes' % len(aResult), log_utils.LOGINFO, SITE_IDENTIFIER)
    items = []
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '<p[^>]*data-full-description="(.*?)"[^>]*>')
    total = len(aResult)
    
    for sID, sUrl2, sNameGer, sNameEng in aResult:
        sName = '%d - ' % int(sID)
        if isMovieList == True:
            sName += sNameGer + '- ' + sNameEng
        else:
            sName += sNameGer if sNameGer else sNameEng
        
        mediatype = 'episode' if not isMovieList else 'movie'
        log_utils.log('Episode %s: %s (URL: %s)' % (sID, sName, URL_MAIN + sUrl2), log_utils.LOGDEBUG, SITE_IDENTIFIER)
        
        item = {}
        item.setdefault('TVShowTitle', sTVShowTitle)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', sDesc if isDesc else '')
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sUrl', URL_MAIN + sUrl2)
        item.setdefault('mediatype', mediatype)
        items.append(item)
    
    log_utils.log('Calling xsDirectory with %d items' % len(items), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()
    log_utils.log('========== showEpisodes END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def getHosters():
    """Get hosters with progressDialog and Container.Update"""
    log_utils.log('========== getHosters START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    hosters = []
    meta = json.loads(params.getValue('meta'))
    isResolve = True
    isProgressDialog = True
    sUrl = meta.get('sUrl')
    
    log_utils.log('Episode URL: %s' % sUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    log_utils.log('Meta: %s' % str(meta), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    if isProgressDialog:
        progressDialog.create('SerienStream', 'Suche Streams...')
        log_utils.log('Progress dialog created', log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    items = []
    t = 0
    
    pattern = '<li[^>]*data-lang-key="([^"]+).*?data-link-target="([^"]+).*?<h4>([^<]+)<([^>]+)'
    pattern2 = 'itemprop="keywords".content=".*?Season...([^"]+).S.*?'
    
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    aResult2 = cParser.parse(sHtmlContent, pattern2)
    
    if not isMatch:
        log_utils.log('No hosters found in HTML', log_utils.LOGWARNING, SITE_IDENTIFIER)
        if isProgressDialog:
            progressDialog.close()
        return
    
    log_utils.log('Found %d hosters' % len(aResult), log_utils.LOGINFO, SITE_IDENTIFIER)
    sLanguage = getSetting('prefLanguage', '0')
    log_utils.log('Preferred language: %s' % sLanguage, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    for sLang, sUrl, sName, sQuality in aResult:
        log_utils.log('Processing hoster: %s (Lang: %s, URL: %s)' % (sName, sLang, sUrl), log_utils.LOGDEBUG, SITE_IDENTIFIER)
        
        # Language filtering
        if sLanguage == '1':
            if '2' in sLang or '3' in sLang:
                log_utils.log('Skipping %s - wrong language' % sName, log_utils.LOGDEBUG, SITE_IDENTIFIER)
                continue
            if sLang == '1':
                sLang = '(DE)'
        elif sLanguage == '2':
            if '1' in sLang or '3' in sLang:
                log_utils.log('Skipping %s - wrong language' % sName, log_utils.LOGDEBUG, SITE_IDENTIFIER)
                continue
            if sLang == '2':
                sLang = '(EN)'
        elif sLanguage == '0':
            if sLang == '1':
                sLang = '(DE)'
            elif sLang == '2':
                sLang = '(EN)'
            elif sLang == '3':
                sLang = '(EN) Sub: (DE)'
        
        # Quality detection
        if aResult2[0] and 'HD' in aResult2[1]:
            sQuality = '720'
        else:
            sQuality = '480'
        
        log_utils.log('%s - Language: %s, Quality: %s' % (sName, sLang, sQuality), log_utils.LOGDEBUG, SITE_IDENTIFIER)
        
        try:
            log_utils.log('Getting hoster URL for %s' % sName, log_utils.LOGDEBUG, SITE_IDENTIFIER)
            hurl = getHosterUrl([sUrl, sName])
            streamUrl = hurl[0]['streamUrl']
            isResolve = hurl[0]['resolved']
            sUrl = streamUrl
            
            log_utils.log('Stream URL: %s' % streamUrl, log_utils.LOGDEBUG, SITE_IDENTIFIER)
            log_utils.log('Resolved: %s' % isResolve, log_utils.LOGDEBUG, SITE_IDENTIFIER)
            
            sHoster = cParser.urlparse(streamUrl)
            t += 100 / len(aResult)
            if isProgressDialog:
                progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
            
            if 'outube' in sHoster:
                sHoster = sHoster.split('.')[0] + ' Trailer'
                log_utils.log('YouTube trailer detected: %s' % sHoster, log_utils.LOGDEBUG, SITE_IDENTIFIER)
            
            if isResolve:
                isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                if isBlocked:
                    log_utils.log('Hoster %s is blocked (resolved)' % sName, log_utils.LOGWARNING, SITE_IDENTIFIER)
                    continue
            elif isBlockedHoster(sUrl)[0]:
                log_utils.log('Hoster %s is blocked' % sName, log_utils.LOGWARNING, SITE_IDENTIFIER)
                continue
            
            items.append((sHoster, sName, meta, isResolve, sUrl, meta.get('sThumbnail')))
            log_utils.log('Added hoster: %s (%s)' % (sHoster, sUrl), log_utils.LOGINFO, SITE_IDENTIFIER)
            
        except Exception as e:
            log_utils.log('ERROR processing hoster %s: %s' % (sName, str(e)), log_utils.LOGERROR, SITE_IDENTIFIER)
            continue
    
    if isProgressDialog:
        progressDialog.close()
        log_utils.log('Progress dialog closed', log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    log_utils.log('Total hosters added: %d' % len(items), log_utils.LOGINFO, SITE_IDENTIFIER)
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    log_utils.log('Container.Update URL: %s' % url, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    execute('Container.Update(%s)' % url)
    log_utils.log('========== getHosters END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def getHosterUrl(hUrl):
    """Get real hoster URL after login"""
    log_utils.log('========== getHosterUrl START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    if type(hUrl) == str:
        hUrl = eval(hUrl)
    
    log_utils.log('Input hUrl: %s' % str(hUrl), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    username = getSetting('serienstream.user')
    password = getSetting('serienstream.pass')
    
    log_utils.log('Username: %s' % username, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    log_utils.log('Logging in to: %s' % URL_LOGIN, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    # Login
    Handler = cRequestHandler(URL_LOGIN, caching=False)
    Handler.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    Handler.addHeaderEntry('Referer', ParameterHandler().getValue('entryUrl'))
    Handler.addParameters('email', username)
    Handler.addParameters('password', password)
    Handler.request()
    log_utils.log('Login request completed', log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    # Get redirect URL
    redirect_url = URL_MAIN + hUrl[0]
    log_utils.log('Requesting redirect from: %s' % redirect_url, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    Request = cRequestHandler(redirect_url, caching=False)
    Request.addHeaderEntry('Referer', ParameterHandler().getValue('entryUrl'))
    Request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    Request.request()
    sUrl = Request.getRealUrl()
    
    log_utils.log('Final stream URL: %s' % sUrl, log_utils.LOGINFO, SITE_IDENTIFIER)
    log_utils.log('========== getHosterUrl END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    """Show search dialog"""
    log_utils.log('========== showSearch START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    try:
        from resources.lib.gui.gui import cGui
        sSearchText = cGui().showKeyBoard()
    except:
        dialog = xbmcgui.Dialog()
        sSearchText = dialog.input('Suche', type=xbmcgui.INPUT_ALPHANUM)
    
    log_utils.log('Search text: %s' % sSearchText, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    if not sSearchText:
        log_utils.log('No search text entered', log_utils.LOGDEBUG, SITE_IDENTIFIER)
        return
    
    SSsearch(sSearchText, bGlobal=False)
    log_utils.log('========== showSearch END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def _search(sSearchText):
    """Search function for global search"""
    log_utils.log('Global search called with: %s' % sSearchText, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    SSsearch(sSearchText, bGlobal=True)


def SSsearch(sSearchText=False, bGlobal=False):
    """Main search function"""
    log_utils.log('========== SSsearch START ==========', log_utils.LOGINFO, SITE_IDENTIFIER)
    log_utils.log('Search text: %s, Global: %s' % (sSearchText, bGlobal), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    params = ParameterHandler()
    params.getValue('sSearchText')
    
    log_utils.log('Fetching series list from: %s' % URL_SERIES, log_utils.LOGDEBUG, SITE_IDENTIFIER)
    oRequest = cRequestHandler(URL_SERIES, caching=True, ignoreErrors=True)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', REFERER + '/serien')
    oRequest.addHeaderEntry('Origin', REFERER)
    oRequest.addHeaderEntry('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    
    if not sHtmlContent:
        log_utils.log('No HTML content received', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    log_utils.log('HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    sst = sSearchText.lower()
    pattern = '<li><a data.+?href="([^"]+)".+?">(.*?)\<\/a><\/l'
    
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        log_utils.log('No search results found', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return

    log_utils.log('Total series in list: %d' % len(aResult[1]), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    total = len(aResult[1])
    found = 0
    
    for link, title in aResult[1]:
        if not sst in title.lower():
            continue
        
        found += 1
        log_utils.log('Match #%d: %s' % (found, title), log_utils.LOGDEBUG, SITE_IDENTIFIER)
        
        try:
            sThumbnail, sDescription = getMetaInfo(link, title)
            log_utils.log('Got metadata for: %s' % title, log_utils.LOGDEBUG, SITE_IDENTIFIER)
            addDirectoryItem(title, 'runPlugin&site=%s&function=showSeasons&sThumbnail=%s&TVShowTitles=%s&sName=%s&Description=%s&sUrl=%s' % (SITE_NAME, URL_MAIN + sThumbnail, title, title, sDescription, URL_MAIN + link), sThumbnail, 'DefaultGenre.png')
        except Exception as e:
            log_utils.log('Could not get metadata for %s: %s' % (title, str(e)), log_utils.LOGWARNING, SITE_IDENTIFIER)
            addDirectoryItem(title, 'runPlugin&site=%s&function=showSeasons&TVShowTitles=%s&sName=%s&sUrl=%s' % (SITE_NAME, title, title, URL_MAIN + link), SITE_ICON, 'DefaultGenre.png')
    
    log_utils.log('Search results: %d matches found' % found, log_utils.LOGINFO, SITE_IDENTIFIER)
    setEndOfDirectory()
    log_utils.log('========== SSsearch END ==========', log_utils.LOGINFO, SITE_IDENTIFIER)


def getMetaInfo(link, title):
    """Get metadata for series"""
    log_utils.log('Getting metadata for: %s (Link: %s)' % (title, link), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    
    oRequest = cRequestHandler(URL_MAIN + link, caching=False)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', REFERER + '/serien')
    oRequest.addHeaderEntry('Origin', REFERER)

    sHtmlContent = oRequest.request()
    if not sHtmlContent:
        log_utils.log('No HTML content for metadata', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return '', ''

    log_utils.log('Metadata HTML length: %d' % len(sHtmlContent), log_utils.LOGDEBUG, SITE_IDENTIFIER)
    pattern = 'seriesCoverBox">.*?data-src="([^"]+).*?data-full-description="([^"]+)"'
    
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        log_utils.log('No metadata found in HTML', log_utils.LOGWARNING, SITE_IDENTIFIER)
        return '', ''

    for sImg, sDescr in aResult[1]:
        log_utils.log('Metadata found - Thumbnail: %s' % sImg, log_utils.LOGDEBUG, SITE_IDENTIFIER)
        return sImg, sDescr
    
    return '', ''
