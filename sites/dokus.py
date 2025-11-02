# -*- coding: utf-8 -*-
# Multi Scraper für Dokumentationen - Lastship Reborn Architektur
# YouTube Integration wie kids_tube.py

import json, sys, xbmc, xbmcplugin, xbmcaddon
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting, setSetting
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib import youtube_fix
import xbmcgui

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

Addon = xbmcaddon.Addon

SITE_IDENTIFIER = 'dokus'
SITE_NAME = 'Dokus'
SITE_ICON = 'dokus.png'

SITE_NAME_1 = 'Dokus4.me'
URL_MAIN_1 = 'http://www.dokus4.me/'
URL_SEARCH_1 = URL_MAIN_1 + '?s=%s'

SITE_NAME_2 = 'Dokustreams.de'
URL_MAIN_2 = 'http://dokustreams.de/'
URL_SEARCH_2 = URL_MAIN_2 + '?s=%s'

SITE_NAME_3 = 'Dokuh.de'
URL_MAIN_3 = 'http://www.dokuh.de/'
URL_SEARCH_3 = URL_MAIN_3 + '?s=%s'

SITE_NAME_6 = 'VideoGold'
URL_MAIN_6 = 'http://videogold.de/'
URL_SEARCH_6 = URL_MAIN_6 + '?s=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    if getSetting('plugin_' + SITE_IDENTIFIER, 'true') == 'true':
        if not xbmc.getCondVisibility('System.HasAddon(%s)' % 'plugin.video.youtube'):
            xbmc.executebuiltin('InstallAddon(%s)' % 'plugin.video.youtube')
    
    addDirectoryItem("[B]%s:[/B] Dokumentationen" % SITE_NAME_1, 'runPlugin&site=%s&function=showEntries_1&sUrl=%s' % (SITE_NAME, URL_MAIN_1), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("[B]%s:[/B] Genre" % SITE_NAME_1, 'runPlugin&site=%s&function=showGenre_1&sUrl=%s' % (SITE_NAME, URL_MAIN_1), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("[B]%s:[/B] Suche" % SITE_NAME_1, 'runPlugin&site=%s&function=showSearch_1' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    addDirectoryItem("[B]%s:[/B] Dokumentationen" % SITE_NAME_2, 'runPlugin&site=%s&function=showEntries_2&sUrl=%s' % (SITE_NAME, URL_MAIN_2), SITE_ICON, 'DefaultMovies.png')
    
    
    addDirectoryItem("[B]YouTube:[/B] Kanäle", 'runPlugin&site=%s&function=showYTChannels' % SITE_NAME, SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("[B]YouTube:[/B] Genre", 'runPlugin&site=%s&function=showYTGenre' % SITE_NAME, SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showGenre_1():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = 'cat-item.*?href="([^"]+)">([^<]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    for sUrl, sName in aResult:
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_1&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries_1(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = 'tbl_titel.*?title="([^"]+).*?href="([^"]+).*?src="([^"]+).*?vid_desc">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    for sName, sUrl, sThumbnail, sDesc in aResult:
        if sSearchText:
            if not cParser().search(sSearchText, sName): continue
        item = {}
        if bGlobal: sName = SITE_NAME_1 + ' - ' + sName
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('infoTitle', sName)
        try: sDesc = unescape(sDesc)
        except: pass
        item.setdefault('plot', sDesc)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    if bGlobal: return
    if sSearchText == None:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, 'rel="next" href="([^"]+)')
        if isMatchNextPage:
            addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries_1&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'DefaultVideo.png')
    setEndOfDirectory(sorted=False)

def showSearch_1():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries_1(URL_SEARCH_1 % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search_1(sSearchText):
    showEntries_1(URL_SEARCH_1 % quote_plus(sSearchText), sSearchText, bGlobal=True)

def showGenre_2():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = 'Themen.*?<ul class="sub-menu">(.*?)</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    aResult = []
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch: return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN_2 + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_2&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries_2(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + 'page/' + str(iPage) if iPage > 0 else entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = '<article id="post-.*?href="([^"]+).*?<img.*?src="([^"]+).*?>([^<]+)</a></h2>.*?<p>([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    for sUrl, sThumbnail, sName, sDesc in aResult:
        if sSearchText:
            if not cParser().search(sSearchText, sName): continue
        item = {}
        if bGlobal: sName = SITE_NAME_2 + ' - ' + sName
        
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', True)
        item.setdefault('poster', sThumbnail)
        item.setdefault('infoTitle', sName)
        item.setdefault('mediaType', 'tvshow')
        try: sDesc = unescape(sDesc)
        except: pass
        item.setdefault('plot', sDesc)
        item.setdefault('sFunction', 'showEpisodes_2')
        items.append(item)
    xsDirectory(items, SITE_NAME)
    #if bGlobal: return
    if sSearchText == None:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        
    addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries_2&sUrl=%s&page=%s' % (SITE_NAME, entryUrl,str(sPageNr)), 'next.png', 'DefaultVideo.png')
        
    setEndOfDirectory(sorted=False)

def showEpisodes_2():
    items=[]
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    
    pattern = 'yotu-videos.*?<ul>(.*?)</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    
            
    aResult = []
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'data-videoid="([^"]+).*?data-title="([^"]+).*?src="([^"]+).*?')
    if not isMatch: return
    
    for sId, sName, sThumb in aResult:
        item = {}
        
        item.setdefault('title', sName)
        item.setdefault('entryUrl', 'dokustreams.de')
        item.setdefault('sUrl', 'dokustreams.de')
        item.setdefault('sId', sId)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumb)
        item.setdefault('infoTitle', sName)
        items.append(item)
        xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def showSearch_2():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries_2(URL_SEARCH_2 % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search_2(sSearchText):
    showEntries_2(URL_SEARCH_2 % quote_plus(sSearchText), sSearchText, bGlobal=True)

def showGenre_3():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = '>Kategorien(.*?)</a></li></ul></li></ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    aResult = []
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch: return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN_3 + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_3&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries_3(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + 'page/' + str(iPage) if iPage > 0 else entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = 'class="item-thumbnail">.*?href="([^"]+).*?title="([^"]+).*?src="([^"]+).*?'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    for sUrl, sName, sThumbnail in aResult:
        if sSearchText:
            if not cParser().search(sSearchText, sName): continue
        item = {}
        if bGlobal: sName = SITE_NAME_3 + ' - ' + sName
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('infoTitle', sName)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    if bGlobal: return
    if sSearchText == None:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('page', int(sPageNr))
        params.setParam('sUrl', entryUrl)
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri(), 'next.png', 'DefaultVideo.png')
    setEndOfDirectory(sorted=False)

def showSearch_3():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries_3(URL_SEARCH_3 % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search_3(sSearchText):
    showEntries_3(URL_SEARCH_3 % quote_plus(sSearchText), sSearchText, bGlobal=True)

def showDoku_6():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = 'Formate</a>(.*?)Themen'
    with open('sdcard/doku.txt','w')as f:
        f.write(sHtmlContent)
        
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    aResult = []
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch: return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN_6 + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_6&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showThemen_6():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = 'Themen</a>(.*?)class="\swp-block-navigation-item\shas-child open-on-hover-click\swp-block-navigation-submenu">'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    aResult = []
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch: return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN_6 + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_6&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries_6(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + 'seite/' + str(iPage) if iPage > 0 else entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = '<li\sclass="wp-block-post.*?href="([^"]+).*?alt="([^"]+).*?data-src="([^"]+).*?'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch: return
    items = []
    for sUrl, sName, sThumbnail in aResult:
        if sSearchText:
            if not cParser().search(sSearchText, sName): continue
        item = {}
        if bGlobal: sName = SITE_NAME_6 + ' - ' + sName
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('infoTitle', sName)
        item.setdefault('mediaType', 'movie')
        items.append(item)
    xsDirectory(items, SITE_NAME)
    if bGlobal: return
    if sSearchText == None:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('page', int(sPageNr))
        params.setParam('sUrl', entryUrl)
        addDirectoryItem('[B]>>>[/B]', 'runPlugin&' + params.getParameterAsUri(), 'next.png', 'DefaultVideo.png')
    setEndOfDirectory(sorted=False)

def showSearch_6():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries_6(URL_SEARCH_6 % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search_6(sSearchText):
    showEntries_6(URL_SEARCH_6 % quote_plus(sSearchText), sSearchText, bGlobal=True)

def getHosters():
    isProgressDialog = True
    items = []
    sUrl = params.getValue('entryUrl')
    if sUrl.startswith('//'): sUrl = 'https:' + sUrl
    try:
        oRequest = cRequestHandler(sUrl)
        sHtmlContent = oRequest.request()
        
    except:pass
    meta = json.loads(params.getValue('meta'))
    if 'dokus4.me' in sUrl or 'dokuh.de' in sUrl:
        pattern = 'src="([^"]+)" f'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    elif 'dokustreams.de' in sUrl:
        sId = meta.get('sId', '')
        if sId:
            isMatch = True
            aResult = ['https://www.youtube.com/watch?v=' + sId]
        else:
            isMatch = False
    elif 'videogold.de' in sUrl:
        pattern = '<noscript><a\shref="([^"]+)'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    else:
        isMatch = False
    
    if isMatch:
        sThumbnail = meta.get('poster', SITE_ICON)
        sTitle = meta.get('infoTitle', 'Unbekannter Titel')
        meta.setdefault('mediatype', 'movie')
        
        if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
        t = 0
        if isProgressDialog: progressDialog.update(t)
        
        youtube_fix.YT()
        apikey = Addon('plugin.video.youtube').getSetting('youtube.api.key')
        
        for sHosterUrl in aResult:
            t += 100 / len(aResult)
            
            # YouTube Video ID extrahieren
            videoId = None
            if 'youtube.com/embed/' in sHosterUrl:
                videoId = sHosterUrl.split('/embed/')[-1].split('?')[0]
            elif 'youtube.com/watch?v=' in sHosterUrl:
                videoId = sHosterUrl.split('watch?v=')[-1]#.split('&')[0]
                
            
            elif 'youtu.be/' in sHosterUrl:
                videoId = sHosterUrl.split('youtu.be/')[-1].split('?')[0]
            
            if videoId:
                # YouTube Video - über Plugin
                sHoster = 'YouTube'
                
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                
                # YouTube Plugin URL erstellen
                if apikey == '' or apikey == None:
                    finalUrl = "plugin://plugin.video.youtube/play/?video_id=" + videoId + "&addon_id=plugin.video.lastship"
                else:
                    finalUrl = "plugin://plugin.video.youtube/play/?video_id=" + videoId
                
                isResolve = False #für YouTube Plugin URLs!
                
            
                items.append((sHoster, sTitle, meta, isResolve, finalUrl))
            else:
                # Kein YouTube - normaler Hoster
                sHoster = cParser.urlparse(sHosterUrl).upper()
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                
                isResolve = True
                #isBlocked, sHosterUrl = isBlockedHoster(sHosterUrl, resolve=isResolve)
                #if isBlocked: continue
                
                items.append((sHoster, sTitle, meta, isResolve, sHosterUrl, sThumbnail))
        
        if isProgressDialog: progressDialog.close()
    
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)

yt_addon = xbmcaddon.Addon(id='plugin.video.youtube')
apikey=yt_addon.getSetting('youtube.api.key')


def showYTChannels():
    channelslists = {
        'Channel':[
            ("ARTEde", "https://yt3.ggpht.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s240-c-k-c0x00ffffff-no-rj", "/channel/UCLLibJTCy3sXjHLVaDimnpQ"),
            ("ARTE․tv Doku", "https://yt3.ggpht.com/FQMc44rW0CmIUKRCDjKcc0BiyyDyWobqb65gsaUbdG-jH3RYQakdYUMmBWusGnyFxlGvKEkK=s240-c-k-c0x00ffffff-no-rj", "/channel/UCr7BKJBRxT66pMGVpFQxzZw"),
            ("BR24", "https://yt3.googleusercontent.com/3utKLXf5P7l9j_sTEuj6dqwSx3ff0pvflQNkuBiU9VHAT-XVz3OOw-SFcTctjFtSp5RSQo3aU7Q=s160-c-k-c0x00ffffff-no-rj", "/channel/UCcweJsCV2TUP_kzMX25U-oQ"),
            ("De Doku Akte", "https://yt3.ggpht.com/ytc/AIdro_lpEa9xCRCqx5a5t8Bh1RB-Q0wzQ_jNgczmdQj3UgfNaw=s240-c-k-c0x00ffffff-no-rj", "/channel/UCaKgcPc5U_PiTSG-K3RKG3w"),
            ("DOKU", "https://yt3.ggpht.com/8x5H67IovFv_P2CFKFSHbAzuAZv-tmtwpuV--29lC3tZMasxIYDUYDjvDt1SKVrrEBE7Xpg7SAY=s240-c-k-c0x00ffffff-no-rj", "/channel/UC4lYbU_FGJY95xSGaUF9PCA"),
            ("Dokus und mehr", "https://yt3.ggpht.com/ytc/AIdro_mLaLdZfO84aZuqG1SppQ2eEnYmBysvKBu_IZFdGUo=s240-c-k-c0x00ffffff-no-rj", "/channel/UCue9a_27UYZUpx0azinesIw"),
            ("Der Spiegel", "https://yt3.ggpht.com/ytc/AIdro_nQCxKfFs_hJhLzVDhXK_13EJjqFJNbSWM4JImydL02m68=s240-c-k-c0x00ffffff-no-rj", "/channel/UC1w6pNGiiLdZgyNpXUnA4Zw"),
            ("DMAX", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj", "/channel/UCnytvQ-VexQ43pYx6KX-DPw"),
            ("Galileo", "https://yt3.ggpht.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s240-c-k-c0x00ffffff-no-rj", "/channel/UC1XrG1M_hw8103zO2x-oivg"),
            ("Mach dich schlau! - Mystery, Doku & Space", "https://yt3.ggpht.com/QybN6XyuPAOGMomZRpRKdfJR7Y_vumGuCHhzr3vodqmvvflO11pIaHd_qlEidRaYbRYjCRA5QQ=s240-c-k-c0x00ffffff-no-rj", "/channel/UCOidlT_g7LMXlLkiGK6aTdw"),
            ("MDR DOK", "https://yt3.ggpht.com/ytc/AIdro_lYFPfGkjfEPgUxvMFD5ygFlRRoRX5X7_iS6JAHJgciIw=s240-c-k-c0x00ffffff-no-rj", "/channel/UCFxgCHRLXmaW3YUyDsikoSw"),
            ("National Geographic Deutschland", "https://yt3.ggpht.com/ytc/AIdro_kU4mJluUbaOxrPEudLfQVR5jqy-Tg7jfEdXc1qLdnC78c=s240-c-k-c0x00ffffff-no-rj", "/channel/UCLZgflun26j9V9n73zA2T5g"),
            ("NDR Doku", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj", "/channel/UCTPAHk1b-h-WGQn9cfGlw2Q"),
            ("ntv Nachrichten", "https://yt3.googleusercontent.com/ytc/AIdro_mRTjZ8IflJpkRty2Q26wo7MA1gctT0jEz-iJqBRwD43bQ=s160-c-k-c0x00ffffff-no-rj", "/channel/UCSeil5V81-mEGB1-VNR7YEA"),
            ("phoenix", "https://yt3.ggpht.com/Z8hNO57BolkhiNu-nWUuQ6h_WCwH8k11LBVEfBbjKtIabNMogzbFQ8Jjr0YS3Kr0B-7g6kk-Dw=s240-c-k-c0x00ffffff-no-rj", "/channel/UCwyiPnNlT8UABRmGmU0T9jg"),
            ("Real Wild Deutschland", "https://yt3.ggpht.com/KsrwAPzVj9CzRTXg_6F2BwNUjzS8HakOCpAZGxeAP6N1gMfXN3f1n5VbnrahL5JUx9EEIR5bmA=s240-c-k-c0x00ffffff-no-rj", "/channel/UCCf599vX34Bf8vT22RYJe0w"),
            ("SRF Dok", "https://yt3.googleusercontent.com/EXf5J9hT7Nm_3hmF6jxfUMW0cFkmfvDxWb_-Sb-2O9_eG1lUsfrYtFBPWjTEmKRd3tfhM8U5Bw=s160-c-k-c0x00ffffff-no-rj", "/channel/UCdFkj0fA6VYJaty-v8_avvg"),
            ("SWR Doku", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj", "/channel/UCK6jlnWA8t-XgUxwZJJHkQA"),
            ("Terra X History", "https://yt3.ggpht.com/UrIj1GSSPUxtrlm2mbJC98ELpgOP0zeNjuYyB3ZAXCp4lScUes4-4PkqWESPSfAMC8eYC6mObA=s240-c-k-c0x00ffffff-no-rj", "/channel/UCA3mpqm67CpJ13YfA8qAnow"),
            ("Welt der Wunder", "https://yt3.ggpht.com/ytc/AIdro_kvhxXUtVXav_qwl4bPJlsivUSCX0-oHX32rGUrs9B05Wo=s240-c-k-c0x00ffffff-no-rj", "/channel/UCBk6ZmyoyX1kLl-w17B0V1A"),
            ("WDR Doku", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj", "/channel/UCUuab1dctZzN5ZmRmQnTzkg"),
            ("XL Doku Deutschland", "https://yt3.googleusercontent.com/tCRuC1qvXA39Q7AeVQOK4x6n1dYtsIE_v8NVCkJqNcKkSJfuvsk2dQ0nLlILZT9Gz_x9Fqyw9A=s160-c-k-c0x00ffffff-no-rj", "/channel/UCYaNwUGngT8hljZRSZVTvUg"),
            ("XL Geschichte", "https://yt3.googleusercontent.com/A2reg275ar2WKAHCosLxo-WZtUkoqwcr0BAXE5xB0SyU40_GsZYOPBefISvYky24uSJksyp4wPw=s160-c-k-c0x00ffffff-no-rj", "/channel/UCllLzS9TIgsD3E970AoSMnA"),
            ("ZDFinfo Dokus & Reportagen", "https://yt3.ggpht.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s240-c-k-c0x00ffffff-no-rj", "/channel/UC7FeuS5wwfSR9IwOPkBV7SQ"),
    	    ],}




    for List in channelslists['Channel']:
        name = List[0]
        id = List[2]
        icon = List[1]
        if apikey == '' or apikey == None:
            sUrl="plugin://plugin.video.youtube" + id + "/?addon_id=plugin.video.xstream"
        else:
            sUrl="plugin://plugin.video.youtube" + id + "/"
            

        addDirectoryItem(name, sUrl, icon, 'DefaultFolder.png', isAction=False)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def showYTGenre():
    channellist = [
        ("Arbeit, Beruf & Leben", "Arbeit", "youtube.png"),
        ("Autos, Technik & Wissen", "Autos", "youtube.png"),
        ("Ernährung, Kochen & Essen", "Ernährung", "youtube.png"),
        ("Geschichte, Kultur & Gesellschaft", "Geschichte", "youtube.png"),
        ("Gesundheit, Medizin & Wissen", "Gesundheit", "youtube.png"),
        ("Kriminalität, Sucht & Gewalt", "Kriminalität", "youtube.png"),
        ("Musik, Klang & Rock", "Musik", "youtube.png"),
        ("Natur, Tiere & die Erde", "Natur", "youtube.png"),
        ("Wirtschaft, Finanzen & Politik", "Wirtschaft", "youtube.png"),
        ("Wissenschaft, Universum & Ufos", "Wissenschaft", "youtube.png"),
    ]

    for name, id, icon in channellist:
        addDirectoryItem(name, 'runPlugin&site=%s&function=showYTLists&id=%s&icon=%s' % (SITE_NAME, id,icon), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showYTLists():
    youtube_fix.YT()
    params = ParameterHandler()
    id = params.getValue('id')
    apikey = Addon('plugin.video.youtube').getSetting('youtube.api.key')
    
    sublist = {
        'Arbeit': [
            ("Architektur & Design | ARTE", "playlist/PLhGeNYH-50Kanjb7dddNt0ywYBX39NAm7", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("China | ARTE", "playlist/PLlQWnS27jXh94iIRrSqPzlfDOaWjdSfAU", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Helden der Baustelle | DMAX Motor", "playlist/PLu791Jb5lWoCOzceiS6SDeGW_u1s7x-0h", "https://yt3.googleusercontent.com/Nx3PWjIZtuLMfc5fye7PNIiZYEupPoEWxxjkxgzyPN-2-J-tbwQpr5ztqC9g-s-8435JDRvrUA=s160-c-k-c0x00ffffff-no-rj"),
            ("Kinder & Familie | WDR", "playlist/PLeVHoee00PXs9DuUuSohGq2GbnZZcnGJF", "https://yt3.googleusercontent.com/Nx3PWjIZtuLMfc5fye7PNIiZYEupPoEWxxjkxgzyPN-2-J-tbwQpr5ztqC9g-s-8435JDRvrUA=s160-c-k-c0x00ffffff-no-rj"),
            ("Anders Reisen & Arbeiten | WDR", "playlist/PLeVHoee00PXuKl5EIcyErW5ku-yyqhkNE", "https://yt3.googleusercontent.com/Nx3PWjIZtuLMfc5fye7PNIiZYEupPoEWxxjkxgzyPN-2-J-tbwQpr5ztqC9g-s-8435JDRvrUA=s160-c-k-c0x00ffffff-no-rj"),
            ("Außergewöhnlich leben | WDR", "playlist/PLeVHoee00PXulyH000ptJ21w-BoNEqFVL", "https://yt3.googleusercontent.com/Nx3PWjIZtuLMfc5fye7PNIiZYEupPoEWxxjkxgzyPN-2-J-tbwQpr5ztqC9g-s-8435JDRvrUA=s160-c-k-c0x00ffffff-no-rj"),
            ("Dokus und Reportagen | ZDFinfo", "playlist/PLo0xoJDmhYEacg7venaFlOYWsWlXu8_0_", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Deutschland 24/7 - Ohne uns läuft nichts! | DMAX", "playlist/PL-83LnmN43mZJ6ZmgzcvI1-HSmL6avP83", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("THW - Wahre Helden im Einsatz | NDR", "PLMJjvZqoYSrD4QZi6dDiuUj5AA4-aIJ6P", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Unternehmen | SWR", "playlist/PLF4F26D09B2C4FF18", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Galileo testet Berufe | ProSieben", "playlist/PLg_KHB2Fiu4eTR4SFQjDdhapk0yj4bD4I", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
            ("Schrecklich schöne Bausünden | ARTE", "playlist/PLhGeNYH-50KaS92AY2VQLKg81Q18DKaeM", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Autos': [
            ("Auto Motor und Sport", "channel/UCLINPbYQ9sy6qc-TqtBeVnw", "https://yt3.googleusercontent.com/ytc/AIdro_k3FanN1l7rSijwXIXpP-hRkFk2CSYQi84W6xruiu23iCA=s160-c-k-c0x00ffffff-no-rj"),
            ("Auto Bild", "channel/UCJrXOOtvmGn4CF7aYaJwuHA", "https://yt3.googleusercontent.com/ytc/AIdro_nQEoz8_Bl0N9F1XX_Kp0ceWTJYzXhmkdYJdDO3HFYP7A=s160-c-k-c0x00ffffff-no-rj"),
            ("Auto Zeitung", "channel/UCHwc6w57Q3S8CSHWergMJWg", "https://yt3.googleusercontent.com/ytc/AIdro_mqA44JCYCHj9Klaq8xwV4gwHufq5oT5Jr4r4hBy7Q8ODzJ=s160-c-k-c0x00ffffff-no-rj"),
            ("JP Performance GmbH", "channel/UC1-VOKyTJrgLiBeiJqzeIUQ", "https://yt3.googleusercontent.com/VD-_UIQmAWviblV4ju2op5ksCiI405YMkhEqU3GoTYa3GRnE8aYLCz_N73DXDO8f2ochm7oJ=s160-c-k-c0x00ffffff-no-rj"),
            ("Limora Oldtimer", "channel/UCT-7FHrVJGFSniI8YhiCfIg", "https://yt3.googleusercontent.com/ytc/AIdro_kabpiOxSiXA2xNotYZP-FCYygBliD5NfqzodSaZ5kq_w=s160-c-k-c0x00ffffff-no-rj"),
            ("Strassenklassiker", "channel/UCx7LHFyEJzIgQ96jhpPeV5g", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj"),
            ("Max Carshop | DMAX", "playlist/PL-83LnmN43mbvMjyKvjqGqXiiRzl-llb5", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Speed Cops | DMAX", "playlist/PL-83LnmN43mZAGslLyLbkhtFPHAzom9Tg", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Steel Buddies | Staffel 8 | DMAX", "playlist/PL-83LnmN43mZCqnCtGp8RgOv3Iy2ZlPCd", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Steel Buddies | Staffel 11 | DMAX", "playlist/PL-83LnmN43mYQI7JHNCT3H0pI3MDUcWa3", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Cash für Chrom | Staffel 3 | DMAX", "playlist/PL-83LnmN43mYN4PyKYSQfwTJ03yVWWAnE", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Overhaulin - Aufgemotzt und Abgefahrn | DMAX", "playlist/PL-83LnmN43maV9n1M4VsjrbTuKOVyPnPj", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Fast N' Loud | DMAX", "playlist/PL-83LnmN43maCpqDqNfWQRp4-HkGOe0bG", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Ernährung': [
            ("Kiki and Koko | @beagleskiko", "channel/UCMPw97JErllU6MQ8tnaMcLg", "https://yt3.googleusercontent.com/vvQyMcFuDLfn3sHdBh43u-YyvuU0421fXszR9ZvzYUyEafnWjcA7zEGtV7l28z9XLhRH5EIj=s160-c-k-c0x00ffffff-no-rj"),
            ("WELT Food", "channel/UCITYOgOaytxZWlBVK6q5apw", "https://yt3.googleusercontent.com/YjfuJ48M0oKjPkcc5jPxutzb_NI_Ty9qQMvBM0Q9E_599sDWQR73GFq1Iww2z49_en2l4IwJ3A=s160-c-k-c0x00ffffff-no-rj"),
            ("Doku rund um's Essen, Kultur und Armut Weltweit | Best4ever", "playlist/PLrH_VmNS2hgXwe-o7F8amXWzoEOK6JM9U", "https://yt3.googleusercontent.com/ytc/AIdro_mKBLdCXVlFCdK9S52WXllejLSUPQsQfoE6ahZyvU4rJA=s160-c-k-c0x00ffffff-no-rj"),
            ("Brot & Stulle | NDR", "playlist/PLMJjvZqoYSrBYyf9kjKVQhyPO01-Gp92w", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Norddeutsche Imbiss-Kultur | NDR", "playlist/PLMJjvZqoYSrCZ1tbtR3GgX1cP-8vd-X7i", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Plätzchen-Werkstatt | SWR", "playlist/PLqcJ1tIeqh4jvH-9SpAkvXGnxZuROZhUr", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Koch ein! | SWR", "playlist/PLqcJ1tIeqh4h4qdELDWsuRIXeET6qSsJw", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Ernährung | SWR", "playlist/PLqcJ1tIeqh4jJqs305xUwKDDzeX13m7IB", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Lifestyle & Kochen | SWR", "playlist/PLqcJ1tIeqh4gldQL3sRGywM_1njJtUmMe", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Oma kocht am besten | SWR", "playlist/PLqcJ1tIeqh4hKc4oVoeky-N_-s7_O4lsk", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Galileo Burger | ProSieben", "playlist/PLg_KHB2Fiu4dreS90s4c4ZvGdJKDWTkdK", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
            ("Galileo FoodScan | ProSieben", "playlist/PLg_KHB2Fiu4ci4ewc2K9LYqhzsahTWIWo", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
            ("Galileo FoodScan | ProSieben", "playlist/PLg_KHB2Fiu4ci4ewc2K9LYqhzsahTWIWo", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
            ("Kulinarik | ARTE", "playlist/PLhGeNYH-50KbReiEQw8W-aBBRQMn5q0jG", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Fast and Good | ARTE", "playlist/PLhGeNYH-50KYvZj4C4RTX6Zb0SVGb38Ds", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Kochen und Rezepte | HR", "playlist/PLBoP5sAJK3ft5-1Gj9vPhx5Dr1MDspOxI", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
            ("Kochs anders | HR", "playlist/PLBoP5sAJK3fvTQ5ZIdZBQUxvD2bjlb6l6", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
            ("Einfach lecker | HR", "playlist/PLBoP5sAJK3fsaqG0C-6ksCio0jokHInpe", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Geschichte': [
            ("Kunst | ARTE", "playlist/PLhGeNYH-50KYd7Rw7hw25cvk57gB5RT-S", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Die Mythen der Wikinger | ARTE", "playlist/PLlQWnS27jXh-A2EdHJ8nOpYq6_UdOpy-S", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Eine Geschichte des Antisemitismus | ARTE", "playlist/PLlQWnS27jXh8McGW6dctPIaZixmfa_-sP", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Der Amerikanische Bürgerkrieg | ARTE", "playlist/PLlQWnS27jXh9_Po60UOaxj0Cawlu4gbKY", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Skandale & Politik | WDR", "playlist/PLeVHoee00PXuSbteBjTrg9MTEXRP-Gq58", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj"),
            ("Historisch und abgründig | ZDFinfo", "playlist/PLo0xoJDmhYEbGMoU6Y5Wy6pS9s7-3Ond3", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Andere Länder, andere Sitten | ZDFinfo", "playlist/PLo0xoJDmhYEaziLbtuOpgChskPjVIYpg-", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Umwelt und Nachhaltigkeit | ZDFinfo", "playlist/PLo0xoJDmhYEYzDcLGYFqK9gPpuMBWQHmi", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Geschichte und Europa | ZDFinfo", "playlist/PLo0xoJDmhYEbcQTzcQ3F9IikTpIHoTniR", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Jugoslawienkriege | ZDFinfo", "playlist/PLo0xoJDmhYEYXd48Cks4zyeaq48GVgiGP", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Unsere Geschichte | NDR", "playlist/PLMJjvZqoYSrBSUNUjlJcqjevsWB3zgCoa", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Griechenland: Von den Gipfeln bis ans Meer | WELT", "playlist/PLslDofkqdKI96RKNyrSlsa3s_xDhIoEWJ", "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("Gesellschaft | SWR", "playlist/PLqcJ1tIeqh4g_M3O2KSXOT91owaYyfb34", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Hitler privat | SPIEGEL TV", "playlist/PLuiYhcgFTmqCjQ7eYtpbUWf1oJtLujmHq", "https://yt3.googleusercontent.com/ytc/AIdro_nQCxKfFs_hJhLzVDhXK_13EJjqFJNbSWM4JImydL02m68=s160-c-k-c0x00ffffff-no-rj"),
            ("Der Zweite Weltkrieg | SPIEGEL TV", "playlist/PLuiYhcgFTmqAi8SWk6p1iC4zESvcO0mDt", "https://yt3.googleusercontent.com/ytc/AIdro_nQCxKfFs_hJhLzVDhXK_13EJjqFJNbSWM4JImydL02m68=s160-c-k-c0x00ffffff-no-rj"),
            ("30 Jahre Mauerfall | SPIEGEL TV", "playlist/PLuiYhcgFTmqDdxOuhl4yAJ7KCiXK3jYij", "https://yt3.googleusercontent.com/ytc/AIdro_nQCxKfFs_hJhLzVDhXK_13EJjqFJNbSWM4JImydL02m68=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Gesundheit': [
            ("Krankheit & Gesundheit | WDR", "playlist/PLeVHoee00PXvtH9M66B9qcVOprg9eqPPj", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj"),
            ("Liebe & Sex | WDR", "PLeVHoee00PXuR8r-W2f2f8j60MixKDlCw", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj"),
            ("Gesundheit | SWR", "playlist/PLqcJ1tIeqh4g4c-CBS5997U4uFa2aCsZN", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Wissen | SWR", "playlist/PLqcJ1tIeqh4j21kT9PTEtdwXr0axLdNEF", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Gesundheit | ARTE", "playlist/PLlQWnS27jXh_S3iOhmygd8hqRBNLyrBAW", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Unser Baby | HR", "playlist/PLBoP5sAJK3fthq_2OFmxID4G_cfQ111cr", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
            ("Notfall Krankenhaus | HR", "playlist/PLBoP5sAJK3fv5fIS8gEjIa_22IBBvTKzu", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
            ("Kinderarzt Berwald | HR", "playlist/PLBoP5sAJK3ftkNwmI8fOxTZ1jjGsQDTeE", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
            ("Die Gesundmacher | HR", "playlist/PLBoP5sAJK3fsO8MIQBxCwI8e0a19lRb1n", "https://yt3.googleusercontent.com/AESs0cOwQhi4Zlxmye5TGtsdlR-le5I-VgdvirAiX97--C8wwFOHG-osatCZLfWuybEXeJB0sg=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Kriminalität': [
            ("Süchtig nach Dopamin | ARTE", "playlist/PLhGeNYH-50KaGfPTo2_sl_yxVByNEfLTO", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Welt im Terror | ARTE", "playlist/PLlQWnS27jXh-SJ3lGY0kUb02WduOmw_TQ", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Alles zum Thema Drogen | ARTE", "playlist/PLlQWnS27jXh9McmOSmrMFzshYO4WOWcMG", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Nachtstreife | SWR", "playlist/PLqFRvy_OBSDpCgH03yvVVu9lPCBA3RN9V", "https://yt3.ggpht.com/k05Upm6oh65EuJnNPvYnBJpaxBrj-RWNNBS0BS70yw5Az0JoPw6_MpfA96_yNUSv1ObQn5hX=s240-c-k-c0x00ffffff-no-rj"),
            ("Crime & Justiz | WDR", "playlist/PLeVHoee00PXuiVpqioBWVuGpnFjwmK9EU", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj"),
            ("Hinter Gittern | ZDFinfo", "playlist/PLo0xoJDmhYEZ0TuKyDavuZXwCJf5cLyjz", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("True Crime | ZDFinfo", "playlist/PLo0xoJDmhYEZU3al7C0if6-wDVUrLSSdM", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Tatort Internet | ZDFinfo", "playlist/PLo0xoJDmhYEYCjvayqOEQ1faH2tm9dOgr", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Gangs und Clans | ZDFinfo", "playlist/PLo0xoJDmhYEZUCp5UF3iV5J81o99gg0oT", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Polizei im Einsatz | ZDFinfo", "playlist/PLo0xoJDmhYEbQ_-tMI1Jext3BXQUep6sU", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Verbrechen und Mord | ZDFinfo", "playlist/PLo0xoJDmhYEYKrB5-czkUjEiCP-oNlttC", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Border Control: Schwedens Grenzschützer | DMAX", "playlist/PL-83LnmN43maC8SPvHyz5heHhlYsCBi-2", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Verbrechen & Justiz | NDR", "playlist/PLMJjvZqoYSrBum1QtGLeDwwR1nVIqHS-g", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Natur': [
            ("Natur & Umwelt | WDR", "playlist/PLeVHoee00PXsPbMnu_R_d2n1AbEbBCyKi", "https://yt3.googleusercontent.com/ytc/AIdro_lvqTnZ71kiSPuVGl0MwB94uktdGVECDzVrVNiUj5Yl0g=s160-c-k-c0x00ffffff-no-rj"),
            ("Die Natur hinter den Mythen | ARTE", "playlist/PLlQWnS27jXh81J4EexYTn1AjPQh7cpgNa", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Mächtige Winde | ARTE", "playlist/PLlQWnS27jXh_A3o1EVe9WNmPz1saMcmDP", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Unser Wasser - Faszinierende Wunderwelten | ARTE", "playlist/PLlQWnS27jXh-nOtc4iaDn58AxlWdMcznl", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Home Rescue - Wohnen in der Wildnis | DMAX", "playlist/PL-83LnmN43mZ3_asZCua7i7g9ILnutj6e", "https://yt3.googleusercontent.com/iW1EB5wkDE76d08Jy6yRO5JX_06EokRm85rBLovQOQ-jTrhuoCbxD_t7T9DuGvGTnGNhMwJS=s160-c-k-c0x00ffffff-no-rj"),
            ("Geschichten am Wasser | NDR", "playlist/PLMJjvZqoYSrD8HWA0zVEJvTfr0J1STo2u", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Abenteuer Kanu-Tour | NDR", "playlist/PLMJjvZqoYSrD8HWA0zVEJvTfr0J1STo2u", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("#wetterextrem | NDR", "playlist/PLMJjvZqoYSrAPvLvHEZwzEaunnaFGGo6B", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("NaturNah | NDR", "playlist/PLMJjvZqoYSrDDPHqBwAanhHtA1D9BWkgI", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Hanseblick | NDR", "playlist/PLMJjvZqoYSrDqbkkjJkGuWuUmiz2YlYnv", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Nordseereport | NDR", "playlist/PLMJjvZqoYSrCgXhI_S9JT2DD5v7rmyCv3", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("Ostseereport | NDR", "playlist/PLMJjvZqoYSrAs3QxoP7kYZ8LPJO2oR2Lm", "https://yt3.googleusercontent.com/ytc/AIdro_lCawKvOSn5yZPta-q7z-OH0jiOphq0cjhyPMst4dDsAa8=s160-c-k-c0x00ffffff-no-rj"),
            ("LOST PLACES - Doku Serie | WELT", "playlist/PLslDofkqdKI_520q4xOI31tK63E-KyobL", "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("Wetter & Klima | WELT", "playlist/PLslDofkqdKI-8ensvM5eAoBHoeRuEQbVu",  "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("Die schönsten Reiseziele der Welt I Real Wild Deutschland", "playlist/PLSwXKep2Ci4FuCAEOMCf5skJ-o781_ybh", "https://yt3.googleusercontent.com/KsrwAPzVj9CzRTXg_6F2BwNUjzS8HakOCpAZGxeAP6N1gMfXN3f1n5VbnrahL5JUx9EEIR5bmA=s160-c-k-c0x00ffffff-no-rj"),
            ("Tierdokumentationen | Real Wild Deutschland", "playlist/PLSwXKep2Ci4FFqhP83ZBT-Ajlj8iL4XgJ", "https://yt3.googleusercontent.com/KsrwAPzVj9CzRTXg_6F2BwNUjzS8HakOCpAZGxeAP6N1gMfXN3f1n5VbnrahL5JUx9EEIR5bmA=s160-c-k-c0x00ffffff-no-rj"),
            ("Geniale Natur: clever und erstaunlich | Real Wild Deutschland", "playlist/PLSwXKep2Ci4EIjsXmudXsxaJqbpofGDm9", "https://yt3.googleusercontent.com/KsrwAPzVj9CzRTXg_6F2BwNUjzS8HakOCpAZGxeAP6N1gMfXN3f1n5VbnrahL5JUx9EEIR5bmA=s160-c-k-c0x00ffffff-no-rj"),
            ("Naturschutz | Real Wild Deutschland", "playlist/PLSwXKep2Ci4Fz6i7XTBPmeN0vse6kmkVK", "https://yt3.googleusercontent.com/KsrwAPzVj9CzRTXg_6F2BwNUjzS8HakOCpAZGxeAP6N1gMfXN3f1n5VbnrahL5JUx9EEIR5bmA=s160-c-k-c0x00ffffff-no-rj"),
            ("Faszinierende Natur | Real Wild Deutschland", "playlist/PLSwXKep2Ci4Fc18-vym377ywEN-Y-zW54", "https://yt3.googleusercontent.com/KsrwAPzVj9CzRTXg_6F2BwNUjzS8HakOCpAZGxeAP6N1gMfXN3f1n5VbnrahL5JUx9EEIR5bmA=s160-c-k-c0x00ffffff-no-rj"),
            ("Tierisch Galileo | ProSieben", "playlist/PLg_KHB2Fiu4cp-ofOvFcdkqkXj8UZhNkb", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Musik': [
            ("DJPaoloMontiOfficial", "channel/UCHKb9guNj_pRq2OQ1QWgSAg", "https://yt3.googleusercontent.com/umHjglKoKH-POESb1cXGsCCY3kdrsOrpicNn8D5QoY52KI5Lk7EETCtED7Ii_asWvhyMaE_cXrA=s160-c-k-c0x00ffffff-no-rj"),
            ("Mix Akták Retro Party", "channel/UCfzTaGgL5NT7BblA7eiyFYg", "https://yt3.googleusercontent.com/1XYO899bDtvgdg27NehA2_1lXFaHmaysiF7wU5XtuzjFIu7kzX_5CGIQs5X0GRz70eGUqzN1eMY=s160-c-k-c0x00ffffff-no-rj"),
            ("Mr.Stephen - Hit Maker ", "channel/UC9TUDA88MhhBmc0IS78DBoA", "https://yt3.googleusercontent.com/k_FJkpPO7gIWSqJupHwr1hTiXAgjap2QRrdaJMtuR4oAgRS5_RNWAAKRvDs9Aa1f2l4WG_91Pw=s160-c-k-c0x00ffffff-no-rj"),
            ("HBz", "channel/UCj6ljqIWs4Sfk3TBIn1xP6Q", "https://yt3.googleusercontent.com/ytc/AIdro_nj9Ll2_o0VuyJpbI7K3tChWr_SUypT9eH5BuK1ZyrBBV4=s160-c-k-c0x00ffffff-no-rj"),
            ("Moreno J Remixes", "channel/UCJqyF-E8VW75fQz61ftchzg", "https://yt3.googleusercontent.com/zKjmrFXhlzaXsL29KBa06TazK2PJZr5180AaKcdk9eSAxM_gJrzU_SV8EdegguTqJ4QztOKbew=s160-c-k-c0x00ffffff-no-rj"),
            ("Mashup Mixes", "channel/UC_MRLN4C-I0sApga0TrH7Sw", "https://yt3.googleusercontent.com/ytc/AIdro_kp3Jwpa8TLTMbDEyq4Fbppg3jr18Y3dZ5Wc4FNi0T93g=s160-c-k-c0x00ffffff-no-rj"),
            ("N&T Party", "channel/UCC9rwt1T2i4klATksN6prdQ", "https://yt3.googleusercontent.com/ytc/AIdro_nLWadIzMDdiXcTIR0lHk78Tr7UGdQ3gSvL-QRDBQSnYg=s160-c-k-c0x00ffffff-no-rj"),
            ("Best Remixes Channel", "channel/UCmpqeOzl0kdzEBpGni1kh1w", "https://yt3.googleusercontent.com/ytc/AIdro_lFw-qBchdHY68UifRatZ2rLYyFnfnwTSgtQna3WZZRAw=s160-c-k-c0x00ffffff-no-rj"),
            ("ZILITIK", "channel/UCEMmEHUY8JLErkizCPuUk_w", "https://yt3.googleusercontent.com/w8EYJ2IH_ZqzpLS9wqt47VcuT3ENK_Q6W7d406AlY4d3UYZI3oafzAuNPKr6FEjs8ZuiOXi1bw=s160-c-k-c0x00ffffff-no-rj"),
            ("DJ Happy Vibes", "channel/UC5LrfTmOrn-4R6tvltTOIRg", "https://yt3.googleusercontent.com/ytc/AIdro_mXiNbV6MyHIOOUeXbz4aIuR_2NTbUVcqvoB9JNU6UJIAg=s160-c-k-c0x00ffffff-no-rj"),
            ("Top Hits 80s - Ohrwürmer der 80er Jahre", "playlist/PLd5xnond3B5Q76AHn0yU7iuCU5j7b4DLi", "https://yt3.googleusercontent.com/AyjYEnhHw62pOnBagaJwDqEjHTSXMqYno6m1bOxnk7t60KaJybbzq8QV8IpCNtKOYNgaP2FHiCg=s160-c-k-c0x00ffffff-no-rj"),
            ("90er Party Hits", "playlist/PLILCJF6YwPP-Uk6R539eCrqIUKaJOCyZ-", "https://yt3.googleusercontent.com/ytc/AIdro_m_q1gNRBvL1PCtss-fL81oeFCgx7m4q9iprHw52EhOdqg=s160-c-k-c0x00ffffff-no-rj"),
            ("Martin Davis", "channel/UCqcBhsHlUuwQaI-il7xlcYQ", "https://yt3.googleusercontent.com/ytc/AIdro_m_q1gNRBvL1PCtss-fL81oeFCgx7m4q9iprHw52EhOdqg=s160-c-k-c0x00ffffff-no-rj"),
            ("2000er Hits Playlist", "playlist/PLJNXa5V1YTQT-Um4F8dVit4Uuu2Ag8NqG", "https://yt3.googleusercontent.com/U0EyubzYWFpfTGMwatogyyO-pOnjMs2AIsWIG7FTF4GlxZx4Q2Pjgcxwb97CMHkmk_easYC5JA=s160-c-k-c0x00ffffff-no-rj"),
            ("Trampsta", "channel/UCOlxGyNCuzG8xm5ogYM6OOQ", "https://yt3.googleusercontent.com/ytc/AIdro_kqguRLm3O5_6sPkiqLVWev2L6GLTnnXd6GZeCvyr2a9Rw=s160-c-k-c0x00ffffff-no-rj"),
            ("Die Prinzen", "channel/UCvkPFtR30EM6wXu5Dy07p-g", "https://yt3.googleusercontent.com/F7c2A2Vo_9IxQrCKYvbRQVS-e9gr00wcE1qU4SXet7owfI8NNtLZhUJlCs8ZU5FgiYRVVJgLgis=s160-c-k-c0x00ffffff-no-rj"),
            ("MaxRiven", "channel/UCb7G5XdA9I8sNxC-3E3maFQ", "https://yt3.googleusercontent.com/ytc/AIdro_nQIbgFExwRCDB0NnZl1IX-APNWkz4ugpdLg2C0LTACui8=s160-c-k-c0x00ffffff-no-rj"),
            ("Musik | ARTE", "playlist/PLhGeNYH-50KYyCOpar7RnUF3ycN0jIi7F", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Wirtschaft': [
            ("Industrie und Wirtschaft – Dokus und Reportagen kompakt | ZDFinfo", "playlist/PLo0xoJDmhYEZYhZe1a0LcS_BMOoQZEZcB", "https://yt3.googleusercontent.com/ytc/AIdro_nPZhGyR2qcxE745O7Xa0O1jzqTtIxuOyLFQLnZ7R9Dx6c=s160-c-k-c0x00ffffff-no-rj"),
            ("Der Tag: News, Politik, Panorama, Wirtschaft und Sport | WELT", "playlist/PLslDofkqdKI9iy5ns0XnD8f7lvoSnnTot", "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("LTW 2024 Brandenburg | phoenix", "playlist/PLoeytWjTuSuqRGjrqNduz1WuLgCBe7PUg", "https://yt3.googleusercontent.com/Z8hNO57BolkhiNu-nWUuQ6h_WCwH8k11LBVEfBbjKtIabNMogzbFQ8Jjr0YS3Kr0B-7g6kk-Dw=s160-c-k-c0x00ffffff-no-rj"),
            ("Bundestag 2024 | phoenix", "playlist/PLoeytWjTuSur7r-5DIpm4RE3clHBokEU5", "https://yt3.googleusercontent.com/Z8hNO57BolkhiNu-nWUuQ6h_WCwH8k11LBVEfBbjKtIabNMogzbFQ8Jjr0YS3Kr0B-7g6kk-Dw=s160-c-k-c0x00ffffff-no-rj"),
            ("Europawahl 2024 | Rechtsruck in der EU? | phoenix", "playlist/PLoeytWjTuSurgOmUfemNWL2pI4O6npoK7", "https://yt3.googleusercontent.com/Z8hNO57BolkhiNu-nWUuQ6h_WCwH8k11LBVEfBbjKtIabNMogzbFQ8Jjr0YS3Kr0B-7g6kk-Dw=s160-c-k-c0x00ffffff-no-rj"),
            ("#Gamescom2022 | phoenix", "playlist/PLoeytWjTuSuowLmvkg4azapIw3r4M2icx", "https://yt3.googleusercontent.com/Z8hNO57BolkhiNu-nWUuQ6h_WCwH8k11LBVEfBbjKtIabNMogzbFQ8Jjr0YS3Kr0B-7g6kk-Dw=s160-c-k-c0x00ffffff-no-rj"),
            ("ntv Faktenzeichen | N-TV", "playlist/PLwneNHYIBCIQO-vQ_N_xdb9daLVGc5aBh", "https://yt3.googleusercontent.com/ytc/AIdro_mRTjZ8IflJpkRty2Q26wo7MA1gctT0jEz-iJqBRwD43bQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Weltwirtschaftsforum WEF | N-TV", "playlist/PLwneNHYIBCISLENJlZUKMfE4gMQnGO95Q", "https://yt3.googleusercontent.com/ytc/AIdro_mRTjZ8IflJpkRty2Q26wo7MA1gctT0jEz-iJqBRwD43bQ=s160-c-k-c0x00ffffff-no-rj"),
            ("ntv Wirtschaft | N-TV", "playlist/PLwneNHYIBCIQDX9Tkvy5-xeBOqOpiwR1h", "https://yt3.googleusercontent.com/ytc/AIdro_mRTjZ8IflJpkRty2Q26wo7MA1gctT0jEz-iJqBRwD43bQ=s160-c-k-c0x00ffffff-no-rj"),
            ("ntv Nachrichten | N-TV", "playlist/PLwneNHYIBCISaAk_rizKfxde9OjT40Xz1", "https://yt3.googleusercontent.com/ytc/AIdro_mRTjZ8IflJpkRty2Q26wo7MA1gctT0jEz-iJqBRwD43bQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Universum | phoenix", "playlist/PL2TzD1hFT-xlhOsrV865Tie5-mbMJ9h1P", "https://yt3.googleusercontent.com/Z8hNO57BolkhiNu-nWUuQ6h_WCwH8k11LBVEfBbjKtIabNMogzbFQ8Jjr0YS3Kr0B-7g6kk-Dw=s160-c-k-c0x00ffffff-no-rj"),
        ],

        'Wissenschaft': [
            ("Das Universum entdecken | ARTE", "playlist/PLlQWnS27jXh9zChHrrOkFrpYBYIKLitu8", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("42 - Die Antwort auf fast alles | ARTE", "playlist/PLlQWnS27jXh_ofqIJZH7vdOkQ-p_w9gKw", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Wissenschaftsdokus | ARTE", "playlist/PLlQWnS27jXh9_eNjMwbuhNhlwEmjQRr-q", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Couchwissen | ARTE", "playlist/PLhGeNYH-50Ka-CHu6q-dytZJT4uRLKxY7", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Der Mensch, die Natur, das Abenteuer | ARTE", "playlist/PLlQWnS27jXh_WXZtlemAN3V0li9Gi57Cn", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Europa und das Weltall | ARTE", "playlist/PLlQWnS27jXh9o5zB_sBlecHpKkejRI8SI", "https://yt3.googleusercontent.com/ytc/AIdro_lK_Yng-tiFUXYY2ukKBmdtzqSazAH7iPHda9YgHX3JVZQ=s160-c-k-c0x00ffffff-no-rj"),
            ("DOKUS: Raumfahrt | WELT", "playlist/PLslDofkqdKI_KNyed3YcuDhKcE9RxtfMt", "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("Expedition Sternenhimmel | WELT", "playlist/PLslDofkqdKI_VYfR6q5au7iLpdce84asE", "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("Mysterien und Paranormales | WELT", "playlist/PLslDofkqdKI87XYQ68rgbCOMSCWJPGgvs", "https://yt3.googleusercontent.com/warJ1-zqcnR1n0LMK6ONepLoYwFcQS9u-noc8bl0-Uk6Lfbd8vIuXPEgDk6bjs34vp8FZpM5yw=s160-c-k-c0x00ffffff-no-rj"),
            ("Aliens, Ufo, Geister, Monster, Horror und vieles mehr | Mach dich schlau!", "playlist/PL2TzD1hFT-xnsecdrlXpNyM3EkvAgUEcs", "https://yt3.googleusercontent.com/QybN6XyuPAOGMomZRpRKdfJR7Y_vumGuCHhzr3vodqmvvflO11pIaHd_qlEidRaYbRYjCRA5QQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Out of Place Artefakte | Mach dich schlau!", "playlist/PL2TzD1hFT-xnkM_8_KC7yrelq1C9_3aKk", "https://yt3.googleusercontent.com/QybN6XyuPAOGMomZRpRKdfJR7Y_vumGuCHhzr3vodqmvvflO11pIaHd_qlEidRaYbRYjCRA5QQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Universum | Mach dich schlau!", "playlist/PL2TzD1hFT-xlhOsrV865Tie5-mbMJ9h1P", "https://yt3.googleusercontent.com/QybN6XyuPAOGMomZRpRKdfJR7Y_vumGuCHhzr3vodqmvvflO11pIaHd_qlEidRaYbRYjCRA5QQ=s160-c-k-c0x00ffffff-no-rj"),
            ("Unterhaltung | SPIEGEL TV", "playlist/PL084070CE355CB92A", "https://yt3.googleusercontent.com/ytc/AIdro_nQCxKfFs_hJhLzVDhXK_13EJjqFJNbSWM4JImydL02m68=s160-c-k-c0x00ffffff-no-rj"),
            ("Science & Galileo | ProSieben", "playlist/PLg_KHB2Fiu4fc88rrCum8XMaB69WcRNUi", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
            ("Galileo Wissenscountdown | ProSieben", "playlist/PLg_KHB2Fiu4eQGBwmccma9Tua-XVK_wEf", "https://yt3.googleusercontent.com/g_I4TuM3r7n7ukBZH-R4Tp4eKabz1OA_F6bOfuacGWDZky-MC8jbyywxLWbQlb3exNaBjE-ICL8=s160-c-k-c0x00ffffff-no-rj"),
        ],
    }
    for List in sublist[id]:
        name = List[0]
        id = List[1]
        icon = List[2]
        if apikey == '' or apikey == None:
            sUrl="plugin://plugin.video.youtube/" + id + "/?addon_id=plugin.video.xstream"
        else:
            sUrl="plugin://plugin.video.youtube/" + id + "/"
        
        addDirectoryItem(name, sUrl, icon, 'DefaultFolder.png', isAction=False)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
