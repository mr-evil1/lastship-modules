# -*- coding: utf-8 -*- 
import json, sys,xbmcgui,re
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting as getsSetting
from resources.lib.control import setSetting as setsSetting
from resources.lib.log_utils import log, LOGDEBUG
import xbmcgui

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()


SITE_IDENTIFIER = 'streamcloud'
SITE_NAME = 'Streamcloud'
SITE_ICON = 'streamcloud.png'
DOMAIN = getsSetting('provider.' + SITE_IDENTIFIER + '.domain', 'streamcloud.my')
URL_MAIN = 'https://' + DOMAIN 


URL_KINO = URL_MAIN + '/kinofilme/'
URL_SERIES = URL_MAIN + '/serien/'
URL_FILME = URL_MAIN + '/filme/'
URL_ANIMATION = URL_MAIN + '/animation/'
URL_SEARCH = URL_MAIN + '/index.php?do=search&subaction=search&story=%s'
URL_WHAT = URL_MAIN + '/was-zu-sehen/'


# URL_MAIN = 'https://streamcloud.my/'
URL_MAINPAGE = URL_MAIN + '/streamcloud/'
URL_MOVIES = URL_MAIN + '/filme-stream/'
URL_KINO = URL_MAIN + '/kinofilme/'
URL_FAVOURITE_MOVIE_PAGE = URL_MAIN + '/beliebte-filme/'
URL_SERIES = URL_MAIN + '/serien/'
URL_NEW = URL_MAIN + '/neue-filme/'
URL_SEARCH = URL_MAIN + '/index.php?story=%s&do=search&subaction=search'


def load():
    log('[%s] Load %s' % (SITE_NAME, SITE_NAME), LOGDEBUG)
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Kino", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showSeries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showGenre&sUrl=%s' % (SITE_NAME, URL_MAINPAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Releas", 'runPlugin&site=%s&function=showYears&sUrl=%s' % (SITE_NAME, URL_MAINPAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Länder", 'runPlugin&site=%s&function=showCountry&sUrl=%s' % (SITE_NAME, URL_MAINPAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % (SITE_NAME), SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showGenre(entryUrl=False):
    log('[%s] showGenre called with entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()    
    pattern = '>Genres<.*?</div></div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch:
        log('[%s] showGenre: No matches found' % SITE_NAME, LOGDEBUG)
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        if sUrl.startswith('/'): sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        if 'Serie' in sName:
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
        else:
            addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showYears(entryUrl=False):
    log('[%s] showYears called with entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '>Ers.*?</div></div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href=\'([^\']+).*?>([^<]+)')
    if not isMatch:
        log('[%s] showYears: No matches found' % SITE_NAME, LOGDEBUG)
        return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'): sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showCountry(entryUrl=False): 
    log('[%s] showCountry called with entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '">Land.*?</div></div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch:
        log('[%s] showCountry: No matches found' % SITE_NAME, LOGDEBUG)
        cGui().showInfo()
        return
    aResult = sorted(aResult, key=lambda x: x[1].lower())
    log('[%s] showCountry: Found %d countries' % (SITE_NAME, len(aResult)), LOGDEBUG)
    for sUrl, sName in aResult:
        if sUrl.startswith('/'): sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showEntries(entryUrl=False, sSearchText=False,bGlobal=False):
    log('[%s] showEntries called - entryUrl: %s, sSearchText: %s, bGlobal: %s' % (SITE_NAME, entryUrl, sSearchText, bGlobal), LOGDEBUG)
    
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    if not params.getValue('isTvshow'):
        isTvshow = False
    else:
        isTvshow=params.getValue('isTvshow')
    
    log('[%s] showEntries - isTvshow: %s' % (SITE_NAME, isTvshow), LOGDEBUG)
    
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'class="thumb".*?title="([^"]+).*?href="([^"]+).*?src="([^"]+).*?_year">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    
    if not isMatch:
        log('[%s] showEntries: No matches found' % SITE_NAME, LOGDEBUG)
        return
    
    log('[%s] showEntries: Found %d entries' % (SITE_NAME, len(aResult)), LOGDEBUG)
    
    items=[]
    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        if sSearchText:
            pattern = '\\b%s\\b' % sSearchText.lower()
            if not cParser().search(pattern , sName.lower()): continue
        item = {}
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        if isTvshow:
            item.setdefault('sFunction', 'showEpisodes')
        else:
            item.setdefault('season', '0')
            item.setdefault('sFunction', 'getHosters')

        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
        items.append(item)
    
    log('[%s] showEntries: Displaying %d items' % (SITE_NAME, len(items)), LOGDEBUG)
    xsDirectory(items, SITE_NAME)

    if bGlobal: return
    if not sSearchText:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, '"nav_ext.*?>\d[1-9]+<.*?href="([^"]+).*?</div>')
        if isMatchNextPage:
            log('[%s] showEntries: Next page found: %s' % (SITE_NAME, sNextUrl), LOGDEBUG)
            params.setParam('sUrl', sNextUrl)
            addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showSeries(entryUrl=False,sSearchText=False,bGlobal=False):
    log('[%s] showSeries called - entryUrl: %s, sSearchText: %s, bGlobal: %s' % (SITE_NAME, entryUrl, sSearchText, bGlobal), LOGDEBUG)
    
    params = ParameterHandler()
    isTvshow=False
    try:
        meta = json.loads(params.getValue('meta'))
        entryUrl=meta['entryUrl']
        log('[%s] showSeries: Got meta - entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    except Exception as e:
        log('[%s] showSeries: No meta or error: %s' % (SITE_NAME, str(e)), LOGDEBUG)
        pass
    
    if not entryUrl: entryUrl = params.getValue('sUrl')
    log('[%s] showSeries: Using entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    
    isTvShow =False
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    
    log('[%s] showSeries: HTML Content length: %d' % (SITE_NAME, len(sHtmlContent)), LOGDEBUG)
    
    pattern = 'class="thumb".*?title="([^"]+).*?href="([^"]+).*?src="([^"]+).*?_year">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    
    if not isMatch:
        log('[%s] showSeries: No matches found with pattern' % SITE_NAME, LOGDEBUG)
        return
    
    log('[%s] showSeries: Found %d series' % (SITE_NAME, len(aResult)), LOGDEBUG)
    
    items=[]
    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear in aResult:
        log('[%s] showSeries: Processing - Name: %s, URL: %s' % (SITE_NAME, sName, sUrl), LOGDEBUG)
        
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        item={}
        if isTvshow:
            infoTitle, sSE = aName
            item.setdefault('season', sSE)
            item.setdefault('sFunction', 'showEpisodes')
        else:
            infoTitle = sName
        
        sThumbnail = URL_MAIN + sThumbnail
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, infoTitle))
        
        if sUrl.startswith('/'): sUrl = URL_MAIN + sUrl
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('isTvshow',isTvshow)
        item.setdefault('entryUrl', sUrl)
        params.setParam('entryUrl', sUrl)
        item.setdefault('title', sName)
        params.setParam('title', sName)
        item.setdefault('poster', sThumbnail)
        params.setParam('poster', sThumbnail)
        
        log('[%s] showSeries: Adding directory item - %s' % (SITE_NAME, sName), LOGDEBUG)
        addDirectoryItem(sName,  'runPlugin&site=%s&function=showEpisodes&sThumbnail=%s&title=%s&sUrl=%s' % (SITE_NAME, sThumbnail,sName,sUrl), sThumbnail, sThumbnail)

    if not sSearchText:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, '"nav_ext.*?>\d[1-9]+<.*?href="([^"]+).*?</div>')
        if isMatchNextPage:
            log('[%s] showSeries: Next page found: %s' % (SITE_NAME, sNextUrl), LOGDEBUG)
            params.setParam('sUrl', sNextUrl)
            params.setParam('function', 'showSeries')
            params.setParam('site',SITE_NAME)
            addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showSeries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showEpisodes(entryUrl=None):
    log('[%s] showEpisodes called with entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    
    params = ParameterHandler()
    title=''
    if not entryUrl: entryUrl = params.getValue('sUrl')
    
    log('[%s] showEpisodes: Using entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)
    
    try:
        title=params.getValue('title')
        log('[%s] showEpisodes: Title: %s' % (SITE_NAME, title), LOGDEBUG)
    except Exception as e:
        log('[%s] showEpisodes: Error getting title: %s' % (SITE_NAME, str(e)), LOGDEBUG)
        pass
    
    sThumbnail = params.getValue('sThumbnail')
    if not sThumbnail:
        sThumbnail='DefaultVideo.png'
    
    log('[%s] showEpisodes: Thumbnail: %s' % (SITE_NAME, sThumbnail), LOGDEBUG)
    
    sHtmlContent = cRequestHandler(entryUrl).request()
    log('[%s] showEpisodes: HTML Content length: %d' % (SITE_NAME, len(sHtmlContent)), LOGDEBUG)
    
    isMatch, aResult = cParser.parse(sHtmlContent, 'data-num="([^"]+)')
    
    if not isMatch:
        log('[%s] showEpisodes: No episodes found' % SITE_NAME, LOGDEBUG)
        return
    
    log('[%s] showEpisodes: Found %d episodes' % (SITE_NAME, len(aResult)), LOGDEBUG)
    
    total = len(aResult)
    items=[]
    for sName in aResult:
        log('[%s] showEpisodes: Processing episode: %s' % (SITE_NAME, sName), LOGDEBUG)
        item={}
        item.setdefault('infoTitle', title)
        item.setdefault('title', 'Staffel '+sName.split('x')[0]+' Episode '+sName.split('x')[1])
        item.setdefault('entryUrl', entryUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
        item.setdefault('episode', sName)
        item.setdefault('function', 'getHosters')
        items.append(item)
    
    log('[%s] showEpisodes: Displaying %d items' % (SITE_NAME, len(items)), LOGDEBUG)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters():
    log('[%s] getHosters called' % SITE_NAME, LOGDEBUG)
    
    params = ParameterHandler()
    hosters = []
    items=[]
    meta = json.loads(params.getValue('meta'))
    
    log('[%s] getHosters: Meta: %s' % (SITE_NAME, str(meta)), LOGDEBUG)
    
    isResolve = False
    isProgressDialog=True
    sUrl = ParameterHandler().getValue('entryUrl')
    
    log('[%s] getHosters: Entry URL: %s' % (SITE_NAME, sUrl), LOGDEBUG)
    
    sHtmlContent = cRequestHandler(sUrl).request()
    log('[%s] getHosters: HTML Content length: %d' % (SITE_NAME, len(sHtmlContent)), LOGDEBUG)
    

    cloudflare_detected = False
    if 'cloudflare' in sHtmlContent.lower() or 'cf-browser-verification' in sHtmlContent.lower() or 'checking your browser' in sHtmlContent.lower():
        cloudflare_detected = True
        log('[%s] getHosters: Cloudflare protection detected in page content!' % SITE_NAME, LOGDEBUG)
    
    if meta.get('episode'):
        episode = meta['episode']
        log('[%s] getHosters: Episode mode - episode: %s' % (SITE_NAME, episode), LOGDEBUG)
        pattern = 'data-num="{0}".*?data-link="([^"]+)'.format(episode)
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        log('[%s] getHosters: Episode pattern match: %s, found %d links' % (SITE_NAME, isMatch, len(aResult) if isMatch else 0), LOGDEBUG)
        
        if not isMatch:
            log('[%s] getHosters: No episode links found' % SITE_NAME, LOGDEBUG)
            if cloudflare_detected:
                xbmcgui.Dialog().notification(
                    '[B]%s[/B]' % SITE_NAME,
                    'Stream durch Cloudflare-Schutz blockiert',
                    SITE_ICON,
                    5000
                )
            return
    else:

        pattern = '<iframe.*?src="([^"]+).*?allowfull'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        log('[%s] getHosters: Movie iframe match: %s, found %d links' % (SITE_NAME, isMatch, len(aResult) if isMatch else 0), LOGDEBUG)
        
        if not isMatch:
            log('[%s] getHosters: No movie iframe found' % SITE_NAME, LOGDEBUG)
            if cloudflare_detected:
                xbmcgui.Dialog().notification(
                    '[B]%s[/B]' % SITE_NAME,
                    'Stream durch Cloudflare-Schutz blockiert',
                    SITE_ICON,
                    5000
                )
            return
        
        try:
            iframe_url = aResult[0]
            if iframe_url.startswith('/'): iframe_url = 'https:' + iframe_url
            log('[%s] getHosters: Loading iframe URL: %s' % (SITE_NAME, iframe_url), LOGDEBUG)
            sHtmlContent = cRequestHandler(iframe_url, bypass_dns=True).request()
            log('[%s] getHosters: Fetched iframe content length: %d' % (SITE_NAME, len(sHtmlContent)), LOGDEBUG)
            
            if 'cloudflare' in sHtmlContent.lower() or 'cf-browser-verification' in sHtmlContent.lower():
                cloudflare_detected = True
                log('[%s] getHosters: Cloudflare protection detected in iframe content!' % SITE_NAME, LOGDEBUG)
        except Exception as e:
            log('[%s] getHosters: Error loading iframe: %s' % (SITE_NAME, str(e)), LOGDEBUG)
            if cloudflare_detected:
                xbmcgui.Dialog().notification(
                    '[B]%s[/B]' % SITE_NAME,
                    'Stream durch Cloudflare-Schutz blockiert',
                    SITE_ICON,
                    5000
                )
            return
        
        isMatch, aResult = cParser().parse(sHtmlContent, 'data-link="([^"]+)')
        log('[%s] getHosters: data-link matches in iframe: %s, found %d links' % (SITE_NAME, isMatch, len(aResult) if isMatch else 0), LOGDEBUG)
        
        if not isMatch:
            log('[%s] getHosters: No data-link found in iframe' % SITE_NAME, LOGDEBUG)
            if cloudflare_detected:
                xbmcgui.Dialog().notification(
                    '[B]%s[/B]' % SITE_NAME,
                    'Stream durch Cloudflare-Schutz blockiert',
                    SITE_ICON,
                    5000
                )
            return
    log('[%s] getHosters: Found %d hoster links' % (SITE_NAME, len(aResult)), LOGDEBUG)
    
    sThumbnail = meta['poster']
    if meta.get('episode'):
        meta.setdefault('mediatype', 'episode')
        try:
            season, episode_num = meta['episode'].split('x')
            meta['season'] = season
            meta['episode'] = episode_num
            infoTitle = meta['infoTitle'] + ' S%sE%s' % (season, episode_num)
        except:
            infoTitle = meta['infoTitle']
    else:
        meta.setdefault('mediatype', 'movie')
        pattern = 'fsynopsis"><p>([^<]+)'
        isMatch, sDesc = cParser().parseSingleResult(sHtmlContent, pattern)
        infoTitle = meta['infoTitle']
        if isMatch:
            try:
                if 'plot' in meta:
                    meta.pop('plot')
                sDesc = unescape(sDesc)
            except: 
                pass
            sDesc = sDesc.replace("\r", "").replace("\n", "")
            meta.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]{2}'.format(SITE_NAME, infoTitle, quote(sDesc)))
    
    if isProgressDialog: 
        progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
    t = 0
    if isProgressDialog: 
        progressDialog.update(t)
    
    cloudflare_blocked_count = 0
    
    for sUrl in aResult:
        if sUrl.startswith('/'): 
            sUrl = 'https:' + sUrl
        elif sUrl.startswith('//'): 
            sUrl = 'https:' + sUrl
        
        sHoster = cParser.urlparse(sUrl)
        log('[%s] getHosters: Processing hoster: %s - URL: %s' % (SITE_NAME, sHoster, sUrl), LOGDEBUG)
        
        t += 100 / len(aResult)
        if isProgressDialog: 
            progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
        
        if 'ayer' in sHoster: 
            log('[%s] getHosters: Skipping player: %s' % (SITE_NAME, sHoster), LOGDEBUG)
            continue
        
        if 'outube' in sHoster:
            sHoster = sHoster.split('.')[0] + ' Trailer'
            log('[%s] getHosters: Marking as trailer: %s' % (SITE_NAME, sHoster), LOGDEBUG)
        
        if isBlockedHoster(sUrl)[0]: 
            log('[%s] getHosters: URL %s is blocked (no resolver available)' % (SITE_NAME, sUrl), LOGDEBUG)
            cloudflare_blocked_count += 1
            continue
        
        items.append((sHoster, infoTitle, meta, isResolve, sUrl, sThumbnail))
        log('[%s] getHosters: Added hoster: %s (isResolve: %s)' % (SITE_NAME, sHoster, isResolve), LOGDEBUG)
    
    if isProgressDialog: 
        progressDialog.close()
    
    log('[%s] getHosters: Total items added: %d' % (SITE_NAME, len(items)), LOGDEBUG)
    
    if len(items) == 0:
        log('[%s] getHosters: No valid hosters found!' % SITE_NAME, LOGDEBUG)
        if cloudflare_detected or cloudflare_blocked_count > 0:
            xbmcgui.Dialog().notification(
                '[B]%s - Cloudflare Schutz[/B]' % SITE_NAME,
                'Alle Streams sind durch Cloudflare-Schutz blockiert',
                SITE_ICON,
                7000
            )
            log('[%s] getHosters: Cloudflare protection blocked all hosters' % SITE_NAME, LOGDEBUG)
        return
    
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    log('[%s] getHosters: Execute Container.Update with: %s' % (SITE_NAME, url), LOGDEBUG)
    execute('Container.Update(%s)' % url)


def showSearch():
    log('[%s] showSearch called' % SITE_NAME, LOGDEBUG)
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    log('[%s] showSearch: Search text: %s' % (SITE_NAME, sSearchText), LOGDEBUG)
    showEntries(URL_SEARCH % sSearchText, sSearchText, bGlobal=False)

def _search(sSearchText):
    log('[%s] _search called with: %s' % (SITE_NAME, sSearchText), LOGDEBUG)
    showEntries(URL_SEARCH % sSearchText, sSearchText, bGlobal=True)
