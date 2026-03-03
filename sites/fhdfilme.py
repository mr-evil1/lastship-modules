# -*- coding: utf-8 -*-
import json, xbmcgui
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import quote_plus, getSetting
from resources.lib.indexers.navigatorXS import navigator

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'fhdfilme'
SITE_NAME = 'FHD Filme'
SITE_ICON = 'fhdfilme.png'

DOMAIN   = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'hdfilme.party')
URL_MAIN = 'https://' + DOMAIN

URL_NEW    = URL_MAIN + '/filme1/'
URL_KINO   = URL_MAIN + '/kinofilme/'
URL_MOVIES = URL_MAIN
URL_SERIES = URL_MAIN + '/serien/'
URL_SEARCH = URL_MAIN + '/?story=%s&do=search&subaction=search'


def load():
    addDirectoryItem('Neu',    'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW),    SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Kino',   'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO),   SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Serien', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Filme',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Genre',  'runPlugin&site=%s&function=showValue&Value=Genre&sUrl=%s'  % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Jahr',   'runPlugin&site=%s&function=showValue&Value=Jahres&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Land',   'runPlugin&site=%s&function=showValue&Value=Land&sUrl=%s'   % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('Suche',  'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showValue():
    params   = ParameterHandler()
    sValue   = params.getValue('Value')
    oRequest = cRequestHandler(URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = '>{0}</(.*?)</a[^<]*</div>'.format(sValue)
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch:
        pattern = '>{0}</a>(.*?)</ul>'.format(sValue)
        isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch:
        setEndOfDirectory()
        return
    isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch:
        setEndOfDirectory()
        return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showEntries(entryUrl=False, sSearchText=False, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')

    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()

    pattern = 'class="item relative mt-3">.*?href="([^"]+).*?title="([^"]+).*?data-src="([^"]+)(.*?)</div></div>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        setEndOfDirectory()
        return

    items = []
    for sUrl, sName, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue

        isYear,     sYear     = cParser.parseSingleResult(sDummy, r'mt-1">[^<]*<span>([\d]+)</span>')
        isDuration, sDuration = cParser.parseSingleResult(sDummy, r'<span>([\d]+)\smin</span>')
        isQuality,  sQuality  = cParser.parseSingleResult(sDummy, '">([^<]+)</span>')

        isTvshow = (isDuration and int(sDuration) <= 70)
        if 'South Park: The End Of Obesity' in sName:
            isTvshow = False

        sThumbnail = URL_MAIN + sThumbnail
        infoTitle  = sName
        if bGlobal:
            sName = SITE_NAME + ' - ' + sName

        item = {
            'title':     sName,
            'infoTitle': infoTitle,
            'entryUrl':  sUrl,
            'sUrl':      sUrl,
            'poster':    sThumbnail,
            'year':      sYear if isYear else '',
            'plot':      '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, infoTitle),
            'isTvshow':  True,
            'mediatype': 'tvshow' if isTvshow else 'movie',
            'sFunction': 'showSeasons' if isTvshow else 'getHosters',
        }
        if isTvshow:
            item['season'] = '0'
        items.append(item)

    xsDirectory(items, SITE_NAME)

    if not bGlobal and not sSearchText:
        isMatchNext, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'nav_ext">.*?next">.*?href="([^"]+)')
        if isMatchNext:
            if sNextUrl.startswith('/'):
                sNextUrl = URL_MAIN + sNextUrl
            addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showSeasons():
    params     = ParameterHandler()
    meta       = json.loads(params.getValue('meta'))
    sUrl       = meta.get('sUrl') or meta.get('entryUrl') or ''
    sThumbnail = meta.get('poster') or ''
    infoTitle  = meta.get('infoTitle') or meta.get('title') or ''

    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()

    pattern = 'class="su-accordion collapse show"(.*?)<br>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, r'#se-ac-(\d+)')
    if not isMatch:
        setEndOfDirectory()
        return

    for sSeason in aResult:
        addDirectoryItem(
            'Staffel ' + str(sSeason),
            'runPlugin&site=%s&function=showEpisodes&sSeason=%s&sThumbnail=%s&infoTitle=%s&sUrl=%s' % (
                SITE_NAME, str(sSeason),
                quote_plus(sThumbnail), quote_plus(infoTitle), quote_plus(sUrl)
            ),
            sThumbnail or SITE_ICON, 'DefaultTVShows.png')
    setEndOfDirectory()


def showEpisodes():
    params     = ParameterHandler()
    entryUrl   = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sSeason    = params.getValue('sSeason')
    infoTitle  = params.getValue('infoTitle')

    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 4
    sHtmlContent = oRequest.request()

    pattern = '#se-ac-%s(.*?)</div></div>' % sSeason
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, r'Episode\s(\d+)')
    if not isMatch:
        setEndOfDirectory()
        return

    items = []
    for sEpisode in aResult:
        items.append({
            'title':      'Episode ' + str(sEpisode),
            'infoTitle':  infoTitle,
            'entryUrl':   entryUrl,
            'sUrl':       entryUrl,
            'poster':     sThumbnail or '',
            'plot':       '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, infoTitle),
            'sSeason':    sSeason,
            'sEpisode':   str(sEpisode),
            'sThumbnail': sThumbnail or '',
            'isTvshow':   True,
            'mediatype':  'episode',
            'sFunction':  'showEpisodeHosters',
        })
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def showEpisodeHosters():
    params     = ParameterHandler()
    meta_str   = params.getValue('meta')
    meta       = json.loads(meta_str)
    sUrl       = meta.get('entryUrl') or meta.get('sUrl') or ''
    sSeason    = meta.get('sSeason') or ''
    sEpisode   = meta.get('sEpisode') or ''
    sThumbnail = meta.get('sThumbnail') or meta.get('poster') or ''
    sTitle     = meta.get('infoTitle') or meta.get('title') or ''

    sHtmlContent = cRequestHandler(sUrl, ignoreErrors=True).request()

    pattern = '#se-ac-%s(.*?)</div></div>' % sSeason
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch:
        setEndOfDirectory()
        return

    pattern2 = r'x%s\sEpisode(.*?)<br' % sEpisode
    isMatch2, sHtmlLink = cParser.parseSingleResult(sHtmlContainer, pattern2)
    if not isMatch2:
        setEndOfDirectory()
        return

    isMatch3, aResult = cParser().parse(sHtmlLink, 'href="([^"]+)')
    if not isMatch3:
        setEndOfDirectory()
        return

    hosters = []
    for sUrl in aResult:
        if 'youtube' in sUrl:
            continue
        if sUrl.startswith('//'):
            sUrl = 'https:' + sUrl
        sName = cParser.urlparse(sUrl).split('.')[0].strip()
        hosters.append([sName, sTitle, meta_str, 0, sUrl, sThumbnail])
        #                                        ^ 0 statt False → resolved=0 → resolveurl wird aufgerufen

    if hosters:
        oNavigator.showHosters(json.dumps(hosters))
    else:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Streams gefunden', SITE_ICON, 3000)
        setEndOfDirectory()


def getHosters():
    params     = ParameterHandler()
    meta_str   = params.getValue('meta') or '{}'
    meta       = json.loads(meta_str)
    sThumbnail = meta.get('poster') or ''
    sTitle     = meta.get('infoTitle') or meta.get('title') or ''
    sUrl       = params.getValue('entryUrl') or meta.get('entryUrl') or meta.get('sUrl') or ''

    sHtmlContent = cRequestHandler(sUrl, ignoreErrors=True).request()

    pattern = r'<iframe\sw.*?src="([^"]+)'
    isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch:
        xbmcgui.Dialog().notification(SITE_NAME, 'Kein iframe gefunden', SITE_ICON, 3000)
        setEndOfDirectory()
        return

    sHtmlContainer = cRequestHandler(hUrl, ignoreErrors=True).request()
    isMatch, aResult = cParser().parse(sHtmlContainer, 'data-link="([^"]+)')
    if not isMatch:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Links gefunden', SITE_ICON, 3000)
        setEndOfDirectory()
        return

    hosters = []
    for sUrl in aResult:
        if 'youtube' in sUrl:
            continue
        if sUrl.startswith('//'):
            sUrl = 'https:' + sUrl
        sName = cParser.urlparse(sUrl).split('.')[0].strip()
        hosters.append([sName, sTitle, meta_str, 0, sUrl, sThumbnail])
        #                                        ^ 0 statt False → resolved=0 → resolveurl wird aufgerufen

    if hosters:
        oNavigator.showHosters(json.dumps(hosters))
    else:
        xbmcgui.Dialog().notification(SITE_NAME, 'Keine Streams gefunden', SITE_ICON, 3000)
        setEndOfDirectory()


def getHosterUrl(sUrl=False):
    if not sUrl:
        sUrl = params.getValue('sUrl')
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        return
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=False)
    setEndOfDirectory()


def _search(sSearchText):
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=True)
