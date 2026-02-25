# -*- coding: utf-8 -*-
import json, sys, requests, time
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting, setSetting
import xbmcgui

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

def get_url():
    url = "https://raw.githubusercontent.com/mr-evil1/megakino/main/megakino-url.json"
    try:
        current_domain = requests.get(url, timeout=5).json().get("url")
        return current_domain
    except Exception:
        return 'megakino.do'

SITE_IDENTIFIER = 'megakino'
SITE_NAME = 'Megakino'
SITE_ICON = 'megakino.png'
SITE_DOMAIN = get_url()
DOMAIN = getSetting('provider.'+ SITE_IDENTIFIER +'.domain', SITE_DOMAIN)
URL_MAIN = 'https://' + DOMAIN
URL_KINO = URL_MAIN + '/kinofilme/'
URL_MOVIES = URL_MAIN + '/films/'
URL_SERIES = URL_MAIN + '/serials/'
URL_ANIMATION = URL_MAIN + '/multfilm/'
URL_DOKU = URL_MAIN + '/documentary/'
URL_SEARCH = URL_MAIN + '/index.php?do=search&subaction=search&story=%s'

def getHtmlContent(url):
    oRequest = cRequestHandler(url, bypass_dns=True)
    oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    sHtmlContent = oRequest.request()
    if sHtmlContent and ('yg=token' in sHtmlContent or '?y=token' in sHtmlContent):
        token_url = URL_MAIN + '/index.php?yg=token'
        oTokenRequest = cRequestHandler(token_url, bypass_dns=True)
        oTokenRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        oTokenRequest.addHeaderEntry('Referer', url)
        oTokenRequest.request()
        time.sleep(0.5)
        sHtmlContent = oRequest.request()
    return sHtmlContent

def load():
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&sUrl=%s/' % (SITE_NAME, URL_MAIN ), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Aktuelle Filme im Kino", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Animationsfilme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_ANIMATION), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Dokumentationen", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_DOKU), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showGenre&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()

def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = getHtmlContent(entryUrl)
    if not sHtmlContent: return
    pattern = '<div\s+class="side-block__title">Genres</div>(.*?)</ul>\s*</div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'href="([^"]+)">([^<]+)</a>'
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
        if isMatch:
            for sUrl, sName in aResult:
                if sUrl.startswith('/'): sUrl = URL_MAIN + sUrl
                addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = getHtmlContent(entryUrl)
    if not sHtmlContent: return
    pattern = '<a[^>]*class="poster grid-item[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*alt="([^"]+)"[^>]*>.*?<div class="poster__label">([^<]*)</div>.*?<div class="poster__text[^>]*>([^<]*)</div>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        pattern = '<a[^>]*class="poster grid-item[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*data-src="([^"]+)"[^>]*alt="([^"]+)"'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if not isMatch: return
    items = []
    for entry in aResult:
        sUrl = entry[0]
        sThumbnail = entry[1]
        sName = entry[2]
        sQuality = entry[3] if len(entry) > 3 else ""
        sDesc = entry[4] if len(entry) > 4 else ""
        if sSearchText:
            if not sSearchText.lower() in sName.lower(): continue
        if sThumbnail.startswith('/'): sThumbnail = URL_MAIN + sThumbnail
        elif sThumbnail.startswith('//'): sThumbnail = 'https:' + sThumbnail
        if sUrl.startswith('/'): sUrl = URL_MAIN + sUrl
        isTvshow = any(x in sUrl.lower() for x in ['/serials/', '/multfilm/']) or any(x in sName.lower() for x in ['staffel', 'season'])
        item = {'infoTitle': sName, 'title': sName, 'entryUrl': sUrl, 'isTvshow': isTvshow, 'poster': sThumbnail, 'quality': sQuality}
        if isTvshow:
            item['sFunction'] = 'showEpisodes'
            isMatchS, aNameS = cParser.parseSingleResult(sName, '(.*?)\s+-\s+Staffel\s+(\d+)')
            if isMatchS:
                item['infoTitle'], item['season'] = aNameS
            else:
                item['season'] = '1'
        item['plot'] = '[B][COLOR blue]{0}[/COLOR][/B][CR]{1}'.format(SITE_NAME, sDesc.strip() if sDesc else sName)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    if bGlobal: return
    pattern = '<div class="pagination__btn-loader[^>]*>.*?<a href="([^"]+)"'
    isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatchNextPage:
        if sNextUrl.startswith('/'): sNextUrl = URL_MAIN + sNextUrl
        params.setParam('sUrl', sNextUrl)
        addDirectoryItem('[B]>>> Nächste Seite[/B]', 'runPlugin&' + params.getParameterAsUri(), 'next.png', 'DefaultVideo.png')
    setEndOfDirectory(sorted=False)

def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    sHtmlContent = getHtmlContent(sUrl)
    if not sHtmlContent: return
    pattern = '<option\s+value="ep([^"]+)">([^<]+)</option>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    for sEpId, sEpName in aResult:
        item = {'title': sEpName, 'entryUrl': sUrl, 'poster': meta.get("poster"), 'season': meta.get("season", "1"), 'episode': sEpId, 'infoTitle': meta.get("infoTitle")}
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def getHosters():
    items = []
    sUrl = params.getValue('entryUrl')
    sHtmlContent = getHtmlContent(sUrl)
    if not sHtmlContent: return
    meta = json.loads(params.getValue('meta'))
    if meta.get('isTvshow', False):
        epId = meta.get('episode')
        pattern = r'id="ep%s"[^>]*>(.*?)</select>' % epId
        isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, pattern)
        if isMatch: isMatch, aResult = cParser().parse(sContainer, 'value="([^"]+)"')
    else:
        pattern = '<iframe.*?src=(?:"|)([^"\\s>]+)'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        sThumbnail = meta.get('poster')
        sTitle = meta.get('infoTitle')
        progressDialog.create(SITE_NAME, 'Suche Streams...')
        for i, hUrl in enumerate(aResult):
            if 'youtube' in hUrl: continue
            if hUrl.startswith('//'): hUrl = 'https:' + hUrl
            progressDialog.update(int((i / len(aResult)) * 100), 'Prüfe Hoster...')
            sHoster = cParser.urlparse(hUrl).split('.')[0].replace('https://', '').upper()
            isBlocked, finalUrl = isBlockedHoster(hUrl, resolve=True)
            if not isBlocked: items.append((sHoster, sTitle, meta, True, finalUrl, sThumbnail))
        progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)

def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search(sSearchText):
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=True)
