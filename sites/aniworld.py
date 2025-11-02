# -*- coding: utf-8 -*-
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
SITE_IDENTIFIER = 'aniworld'
SITE_NAME = 'AniWorld'
SITE_ICON = 'aniworld.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'aniworld.to')
URL_MAIN = 'https://' + DOMAIN
# URL_MAIN = 'https://aniworld.to'
URL_SERIES = URL_MAIN + '/animes'
URL_POPULAR = URL_MAIN + '/beliebte-animes'
URL_NEW_EPISODES = URL_MAIN + '/neue-episoden'
URL_LOGIN = URL_MAIN + '/login'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    username = getSetting('aniworld.user')
    password = getSetting('aniworld.pass')
    if username == '' or password == '':        
        xbmcgui.Dialog().ok('Xship Aniworld', 'Username und passwort werden benötigt')
    else:
        addDirectoryItem("Neu", 'runPlugin&site=%s&function=showNewEpisodes&sUrl=%s' % (SITE_NAME, URL_NEW_EPISODES), SITE_ICON, 'DefaultMovies.png')
        addDirectoryItem("Serien", 'runPlugin&site=%s&function=showAllSeries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
        addDirectoryItem("Populär", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_POPULAR), SITE_ICON, 'DefaultTVShows.png')
        addDirectoryItem("A-Z", 'runPlugin&site=%s&function=showValue&sCont=%s&sUrl=%s' % (SITE_NAME, 'catalogNav',URL_MAIN), SITE_ICON, 'DefaultGenre.png')
        addDirectoryItem("Genre", 'runPlugin&site=%s&function=showValue&sCont=%s&sUrl=%s' % (SITE_NAME, 'homeContentGenresList',URL_MAIN), SITE_ICON, 'DefaultGenre.png')
        addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
        setEndOfDirectory()




def showValue():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, '<ul[^>]*class="%s"[^>]*>(.*?)<\\/ul>' % params.getValue('sCont'))
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, '<li>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)<\\/a>\s*<\\/li>')
    if not isMatch:
        return

    for sUrl, sName in aResult:
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME,sUrl ), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showAllSeries(entryUrl=False,sSearchText=False,bGolbal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    pattern = '<a[^>]*href="(\\/anime\\/[^"]*)"[^>]*>(.*?)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        return

    total = len(aResult)
    for sUrl, sName in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sUrl=%s' % (SITE_NAME,sName,URL_MAIN + sUrl ), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showNewEpisodes(entryUrl=False, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="col-md-[^"]*"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>\s*<strong>([^<]+)</strong>\s*<span[^>]*>([^<]+)</span>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        return
    total = len(aResult)
    for sUrl, sName, sInfo in aResult:
        sMovieTitle = sName + ' ' + sInfo
        addDirectoryItem(sMovieTitle, 'runPlugin&site=%s&function=showSeasons&sUrl=%s' % (SITE_NAME,URL_MAIN + sUrl ), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()





def showEntries(entryUrl=False, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="col-md-[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<h3>(.*?)<span[^>]*class="paragraph-end">.*?<\\/div>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        return
    items=[]
    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        sUrl=URL_MAIN + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showSeasons&TVShowTitle=%s&sThumbnail=%s&sUrl=%s' % (SITE_NAME,sName,sThumbnail,sUrl ), sThumbnail, 'DefaultGenre.png')
    if not bGlobal:
        pattern = 'pagination">.*?<a href="([^"]+)">&gt;</a>.*?</a></div>'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="hosterSiteDirectNav"[^>]*>.*?<ul>(.*?)<\\/ul>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>(.*?)<\\/a>.*?'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '<p[^>]*data-full-description="(.*?)"[^>]*>')
    isThumbnail, sThumbnail = cParser.parseSingleResult(sHtmlContent, '<div[^>]*class="seriesCoverBox"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>')
    if isThumbnail:
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
    items=[]
    total = len(aResult)
    for sUrl, sName, sNr in aResult:
        isMovie = sUrl.endswith('filme')
        item={}
        thumb=''
        desc='[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
        if isThumbnail:
            thumb=sThumbnail
        if isDesc:
            desc=sDesc
        if not isMovie:
            item.setdefault('TVShowTitle',sTVShowTitle)
            item.setdefault('sSeason', sNr)
        
        item.setdefault('infoTitle', sName)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', URL_MAIN + sUrl)
        item.setdefault('isTvshow', True)
        item.setdefault('poster',thumb)
        item.setdefault('plot', desc)
        item.setdefault('sFunction', 'showEpisodes')
        item.setdefault('sUrl', URL_MAIN + sUrl)
        item.setdefault('sThumbnail', thumb)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()





def showEpisodes():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl=meta.get('sUrl', False)
    sTVShowTitle = meta.get('TVShowTitle',True)
    sSeason = meta.get('sSeason',False)
    sThumbnail = meta.get('sThumbnail',False)
    if not sSeason:
        sSeason = '0'
    isMovieList = sUrl.endswith('filme')
    oRequest = cRequestHandler(sUrl)
    items=[]
    sHtmlContent = oRequest.request()
    oRequest.cacheTime = 60 * 60 * 4
    pattern = '<table[^>]*class="seasonEpisodesList"[^>]*>(.*?)<\\/table>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = '<tr[^>]*data-episode-season-id="(\d+).*?<a href="([^"]+).*?(?:<strong>(.*?)</strong>.*?)(?:<span>(.*?)</span>.*?)?<'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        return
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '<p[^>]*data-full-description="(.*?)"[^>]*>')
    total = len(aResult)
    for sID, sUrl2, sNameGer, sNameEng in aResult:
        sName = '%d - ' % int(sID)
        sName += sNameGer if sNameGer else sNameEng
        item={}
        if isDesc:
            desc=sDesc
        else:
            desc='[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
        if not isMovieList:
            item.setdefault('sSeason', sSeason)
            item.setdefault('sEpisode', int(sID))
        
        item.setdefault('TVShowTitle',sTVShowTitle)
        item.setdefault('infoTitle', sName) 
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', desc)        
        item.setdefault('sUrl', URL_MAIN + sUrl2)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()



def getHosters():
    params = ParameterHandler()
    hosters = []
    items=[]
    meta = json.loads(params.getValue('meta'))
    isResolve = True
    isTvshow=False
    sThumbnail=meta.get('poster')
    isProgressDialog=True
    sUrl = meta.get('sUrl')
    
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<li[^>]*episodeLink([^"]+)"\sdata-lang-key="([^"]+).*?data-link-target="([^"]+).*?<h4>([^<]+)<([^>]+)'
    isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = '<li[^>]*episodeLink([^"]+)"\sdata-lang-key="([^"]+).*?data-link-target="([^"]+).*?<h4>([^<]+)<([^>]+)'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
            t = 0
            if isProgressDialog: progressDialog.update(t)
            for sID, sLangCode, sUrl, sName, sQualy in aResult:
                sUrl = sUrl.replace('/dl/2010', '/redirect/' + sID)
                sLanguage = getSetting('prefLanguage')
                if sLanguage == '1':
                    if '2' in sLangCode:
                        continue
                    if '3' in sLangCode:
                        continue
                    if sLangCode == '1':
                        sLang = 'Deutsch'
                if sLanguage == '2':
                        continue
                if sLanguage == '3':
                    if '1' in sLangCode:
                        continue
                    if sLangCode == '2':
                        sLangCode = '3'
                        sLang = 'Japanisch mit englischen Untertitel'
                    elif sLangCode == '3':
                        sLangCode = '2'
                        sLang = 'Japanisch mit deutschen Untertitel'

                if sLanguage == '0':
                    if sLangCode == '1':
                        sLang = 'Deutsch'
                    if sLangCode == '2':
                        sLangCode = '3'
                        sLang = 'Japanisch mit englischen Untertitel'
                    elif sLangCode == '3':
                        sLangCode = '2'
                        sLang = 'Japanisch mit deutschen Untertitel'
                if 'HD' == sQualy:  
                    sQualy = '1080P'
                else:
                    sQualy = '720P'
                hoster = {'link': [sUrl, sName], 'name': sName, 'displayedName': '%s %s %s' % (sName, sQualy, sLang),
                          'languageCode': sLangCode}
                infoTitle='%s %s %s' % (sName, sQualy, sLang)
                
                item={}
                hurl=getHosterUrl([sUrl,sName])
                streamUrl=hurl[0]['streamUrl']
                isResolve=hurl[0]['resolved']
                sUrl=streamUrl

                if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
                t = 0
                if isProgressDialog: progressDialog.update(t)
                
                sHoster=cParser.urlparse(streamUrl)
                t += 100 / len(aResult)
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                if 'ayer' in sHoster: continue
                Request = cRequestHandler(sUrl, caching=False)
                Request.request()
                sUrl = Request.getRealUrl()
                if 'outube' in sHoster:
                    sHoster=sHoster.split('.')[0]+' Trailer'
                if isResolve:
                    isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                    if isBlocked: continue
                items.append((infoTitle, infoTitle, meta, isResolve, sUrl, ''))
            if isProgressDialog:  progressDialog.close()
    else:
        pattern = '<li[^>]*data-lang-key="([^"]+).*?data-link-target="([^"]+).*?<h4>([^<]+)<([^>]+)'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for sLangCode, sUrl, sName, sQualy in aResult:
                sLanguage = getSetting('prefLanguage')
                if sLanguage == '1':
                    if '2' in sLangCode:
                        continue
                    if '3' in sLangCode:
                        continue
                    if sLangCode == '1':
                        sLang = 'Deutsch'
                if sLanguage == '2':
                        continue
                if sLanguage == '3':
                    if '1' in sLangCode:
                        continue
                    if sLangCode == '2':
                        sLangCode = '3'
                        sLang = 'Japanisch mit englischen Untertitel'
                    elif sLangCode == '3':
                        sLangCode = '2'
                        sLang = 'Japanisch mit deutschen Untertitel'
                if sLanguage == '0':
                    if sLangCode == '1':
                        sLang = 'Deutsch'
                    if sLangCode == '2':
                        sLangCode = '3'
                        sLang = 'Japanisch mit englischen Untertitel'
                    elif sLangCode == '3':
                        sLangCode = '2'
                        sLang = 'Japanisch mit deutschen Untertitel'
                if 'HD' == sQualy:
                    sQualy = '1080P'
                else:
                    sQualy = '720P'
                infoTitle='%s  %s  %s' % (sName, sQualy, sLang)
                item={}
                hurl=getHosterUrl([sUrl,sName])
                streamUrl=hurl[0]['streamUrl']
                isResolve=hurl[0]['resolved']
                sUrl=streamUrl

                if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
                t = 0
                if isProgressDialog: progressDialog.update(t)
                
                sHoster=cParser.urlparse(streamUrl)
                t += 100 / len(aResult)
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                if 'ayer' in sHoster: continue
                Request = cRequestHandler(sUrl, caching=False)
                Request.request()
                sUrl = Request.getRealUrl()
                if 'outube' in sHoster:
                    sHoster=sHoster.split('.')[0]+' Trailer'
                if isResolve:
                    isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                    if isBlocked: continue
                items.append((infoTitle, infoTitle, meta, isResolve, sUrl, sThumbnail))
            if isProgressDialog:  progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def getHosterUrl(hUrl):
    if type(hUrl) == str: hUrl = eval(hUrl)
    username = getSetting('aniworld.user')
    password = getSetting('aniworld.pass')
    Handler = cRequestHandler(URL_LOGIN, caching=False)
    Handler.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    Handler.addHeaderEntry('Referer', ParameterHandler().getValue('entryUrl'))
    Handler.addParameters('email', username)
    Handler.addParameters('password', password)
    Handler.request()
    Request = cRequestHandler(URL_MAIN + hUrl[0], caching=False)
    Request.addHeaderEntry('Referer', ParameterHandler().getValue('entryUrl'))
    Request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    Request.request()
    sUrl = Request.getRealUrl()
    
    return [{'streamUrl': sUrl, 'resolved': False}]




def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    SSsearch(sSearchText, bGlobal=False)

def _search(sSearchText):
    SSsearch( sSearchText, bGlobal=True)




def SSsearch(sSearchText=False, bGlobal=False):
    params = ParameterHandler()
    params.getValue('sSearchText')
    oRequest = cRequestHandler(URL_SERIES, caching=True, ignoreErrors=True)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', 'https://aniworld.to/animes')
    oRequest.addHeaderEntry('Origin', 'https://aniworld.to')
    oRequest.addHeaderEntry('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    oRequest.cacheTime = 60 * 60 * 24
    sHtmlContent = oRequest.request()
    if not sHtmlContent:
            return
    sst = sSearchText.lower()
    pattern = '<li><a data.+?href="([^"]+)".+?">(.*?)\<\/a><\/l'

    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        return
    items=[]
    total = len(aResult[1])
    for link, title in aResult[1]:
        item={}
        if not sst in title.lower():
            continue
        else:
            try:
                sThumbnail, sDescription = getMetaInfo(link, title)
                addDirectoryItem(title, 'runPlugin&site=%s&function=showSeasons&sThumbnail=%s&TVShowTitles=%s&sName=%s&Description=%s&sUrl=%s' % (SITE_NAME,URL_MAIN + sThumbnail,title,title,sDescription,URL_MAIN + link ), sThumbnail, 'DefaultGenre.png')
            except Exception:
                addDirectoryItem(title, 'runPlugin&site=%s&function=showSeasons&TVShowTitles=%s&sName=%s&sUrl=%s' % (SITE_NAME,title,title,URL_MAIN + link ), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()



def getMetaInfo(link, title):
    oRequest = cRequestHandler(URL_MAIN + link, caching=False)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', 'https://aniworld.to/animes')
    oRequest.addHeaderEntry('Origin', 'https://aniworld.to')
    sHtmlContent = oRequest.request()
    if not sHtmlContent:
        return

    pattern = 'seriesCoverBox">.*?<img src="([^"]+)"\ al.+?data-full-description="([^"]+)"'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, pattern)
    if not aResult[0]:
        return
    for sImg, sDescr in aResult[1]:
        return sImg, sDescr