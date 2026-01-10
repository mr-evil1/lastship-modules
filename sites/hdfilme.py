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
SITE_IDENTIFIER = 'hdfilme'
SITE_NAME = 'HD Filme'
SITE_ICON = 'hdfilme.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'hdfilme.garden')
URL_MAIN = 'https://' + DOMAIN
# URL_MAIN = 'https://hdfilme.my'

URL_NEW = URL_MAIN + '/filme1/'
URL_KINO = URL_MAIN + '/kinofilme/'
URL_MOVIES = URL_MAIN
URL_SERIES = URL_MAIN + '/serien/'
URL_SEARCH = URL_MAIN + '/?story=%s&do=search&subaction=search'

def load():
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_NEW), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Kino", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&isTvshow=True&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showValue&Value=%s&sUrl=%s' % (SITE_NAME, 'Genre',URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Releas", 'runPlugin&site=%s&function=showValue&Value=%s&sUrl=%s' % (SITE_NAME, 'Jahres',URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Land", 'runPlugin&site=%s&function=showValue&Value=%s&sUrl=%s' % (SITE_NAME, 'Land',URL_MAIN), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()




def showValue():
    params = ParameterHandler()
    oRequest = cRequestHandler(URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '>{0}</a>(.*?)</ul>'.format(params.getValue('Value'))
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if not isMatch:
        pattern = '>{0}</(.*?)</ul>'.format(params.getValue('Value'))
        isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch:
        return
    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries(entryUrl=False, sSearchText=False,bGlobal=False):
    params = ParameterHandler()
    try: 
        isTvshow=params.getValue('isTvshow')
    except:
        isTvshow = False
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'class="item relative mt-3">.*?href="([^"]+).*?title="([^"]+).*?data-src="([^"]+)(.*?)</div></div>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        return
    items=[]
    total = len(aResult)
    for sUrl, sName, sThumbnail, sDummy in aResult:
        item={}
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isYear, sYear = cParser.parseSingleResult(sDummy, 'mt-1"><span>([\d]+)</span>')  # Release Jahr
        isDuration, sDuration = cParser.parseSingleResult(sDummy,r'<span>(\d+)\s*min</span>')

        if int(sDuration) <= 70: # Wenn Laufzeit kleiner oder gleich 70min, dann ist es eine Serie.
            isTvshow = True
        else:
            isTvshow = False
        if 'South Park: The End Of Obesity' in sName:
            isTvshow = False
        isQuality, sQuality = cParser.parseSingleResult(sDummy, '">([^<]+)</span>')  # QualitÃ¤t
        sThumbnail = URL_MAIN + sThumbnail
        if isTvshow:
            item.setdefault('season', '0')
            item.setdefault('sFunction', 'showSeasons')  # wenn abweichend! - nicht showSeasons !
        else:
            item.setdefault('sFunction', 'getHosters')  # wenn abweichend! - nicht showSeasons !
        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)  # für "Erweiterte Info"
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('sUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName))
        items.append(item)
    xsDirectory(items, SITE_NAME)

    if bGlobal: return
    if not sSearchText:# == None:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'nav_ext">.*?next">.*?href="([^"]+)')
        if isMatchNextPage:
            if sNextUrl.startswith('/'):
                sNextUrl=URL_MAIN+sNextUrl
            addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()

def showSeasons():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('sUrl') if meta.get('sUrl') else params.getValue('entryUrl')
    sThumbnail =params.getValue('poster') if params.getValue('poster') else meta.get('poster')
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'class="su-accordion collapse show"(.*?)<br>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, '#se-ac-(\d+)')
    if not isMatch:
        return
    total = len(aResult)
    for sSeason in aResult:
        addDirectoryItem('Staffel ' + str(sSeason), 'runPlugin&site=%s&function=showEpisodes&sSeason=%s&sThumbnail=%s&infoTitle=%s&sUrl=%s' % (SITE_NAME, str(sSeason),sThumbnail,meta.get('infoTitle') ,sUrl), sThumbnail, 'DefaultGenre.png')
    setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl') #if params.getValue('entryUrl') else params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sSeason = params.getValue('sSeason')
    infoTitle=params.getValue('infoTitle')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
    sHtmlContent = oRequest.request()
    pattern = '#se-ac-%s(.*?)</div></div>' % sSeason
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'Episode\s(\d+)')
    if not isMatch:
        return
    total = len(aResult)
    items=[]
    for sEpisode in aResult:
        item={}
        item.setdefault('infoTitle', infoTitle)  # für "Erweiterte Info"
        item.setdefault('title', 'Episode ' + str(sEpisode))
        item.setdefault('entryUrl', entryUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, infoTitle))
        #optionale items
        item.setdefault('sFunction', 'showEpisodeHosters')  # wenn abweichend! - nicht showSeasons !
        item.setdefault('sUrl', entryUrl)
        item.setdefault('sSeason', sSeason)
        item.setdefault('sEpisode', sEpisode)        
        item.setdefault('sThumbnail', sThumbnail)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def showEpisodeHosters():
    hosters = []
    params = ParameterHandler()
    isTvshow=False
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    sSeason = meta.get('sSeason')
    sEpisode = meta.get('sEpisode')
    sThumbnail=meta.get('sThumbnail')
    isResolve = True
    isProgressDialog=True
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '#se-ac-%s(.*?)</div></div>' % sSeason
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    items=[]
    if isMatch:
        pattern = 'x%s\sEpisode(.*?)<br' % sEpisode
        isMatch2, sHtmlLink = cParser.parseSingleResult(sHtmlContainer, pattern)
        if isMatch2:
            isMatch3, aResult = cParser().parse(sHtmlLink, 'href="([^"]+)')
            if isMatch3:
                if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
                t = 0
                if isProgressDialog: progressDialog.update(t)
                for sUrl in aResult:
                    sName = cParser.urlparse(sUrl)
                    if sUrl.startswith('//'):
                        sUrl = 'https:' + sUrl
                    sHoster=cParser.urlparse(sUrl)
                    if sUrl.startswith('/'): sUrl = 'https:' + sUrl
                    t += 100/ len(aResult)
                    if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                    elif isBlockedHoster(sHoster)[0]: continue  # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
                    elif 'outube' in sHoster:
                        sHoster=sHoster.split('.')[0]+' Trailer'
                    if isResolve:
                        isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                        if isBlocked: continue
                    elif isBlockedHoster(sUrl)[0]: continue
                    items.append((sHoster, sName,meta, isResolve, sUrl, sThumbnail))
                    t += 100 / len(aResult)
                if isProgressDialog:  progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)

def getHosters():
    params = ParameterHandler()
    hosters = []
    items=[]
    meta = json.loads(params.getValue('meta'))
    isResolve = True
    isTvshow=False
    sThumbnail=meta.get('poster')
    isProgressDialog=True
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<iframe\sw.*?src="([^"]+)'
    isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        sHtmlContainer = cRequestHandler(hUrl).request()
        isMatch, aResult = cParser().parse(sHtmlContainer, 'data-link="([^"]+)')
        if isMatch:
            if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
            t = 0
            if isProgressDialog: progressDialog.update(t)
            for sUrl in aResult:
                sName = cParser.urlparse(sUrl)
                if sUrl.startswith('//'):
                    sUrl = 'https:' + sUrl
                sHoster=cParser.urlparse(sUrl)
                t += 100/ len(aResult)
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                elif isBlockedHoster(sHoster)[0]: continue  # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
                if 'outube' in sHoster:
                    sHoster=sHoster.split('.')[0]+' Trailer'
                if isResolve:
                    isBlocked, sUrl = isBlockedHoster(sUrl, resolve=isResolve)
                    if isBlocked: continue
                items.append((sHoster, sName,meta, isResolve, sUrl, sThumbnail))
            t += 100 / len(aResult)
            if isProgressDialog:  progressDialog.close()
        url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
        execute('Container.Update(%s)' % url)

def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText, sSearchText, bGlobal=False)

def _search(sSearchText):
    showEntries(URL_SEARCH % sSearchText, sSearchText, bGlobal=True)
