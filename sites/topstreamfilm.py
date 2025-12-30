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
import resolveurl as resolver
SITE_IDENTIFIER = 'topstreamfilm'
SITE_NAME = 'Topstreamfilm'
SITE_ICON = 'topstreamfilm.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'www.topstreamfilm.live')

URL_MAIN = 'https://' + DOMAIN

URL_ALL = URL_MAIN + '/filme-online-sehen/'
URL_MOVIES = URL_MAIN + '/beliebte-filme-online/'
URL_KINO = URL_MAIN + '/kinofilme/'
URL_SERIES = URL_MAIN + '/serien/'
URL_SEARCH = URL_MAIN + '/?story=%s&do=search&subaction=search'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    addDirectoryItem("Neues", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_ALL), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showMovieMenu&sUrl=%s' % (SITE_NAME, URL_ALL), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Jahr", 'runPlugin&site=%s&function=showValue&Value=%s' % (SITE_NAME, 'YAHRE'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showValue&Value=%s' % (SITE_NAME,'KATEGORIEN'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Land", 'runPlugin&site=%s&function=showValue&Value=%s' % (SITE_NAME,'LAND'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()




def showMovieMenu():
    params = ParameterHandler()
    addDirectoryItem("Neues", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Neue Kinofilme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme diese Woche im Trend", 'runPlugin&site=%s&function=showEntries&Value=%s&sUrl=%s' % (SITE_NAME,'FILM DER WOCHE', URL_KINO), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showValue():
    params = ParameterHandler()
    oRequest = cRequestHandler(URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '>{0}</a>(.*?)</ul>'.format(params.getValue('Value'))
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        if params.getValue('Value')=='YAHRE':
            isMatch, aResult = cParser.parse(sHtmlContainer, r"<a href='(.*?)'>(\d{4})</a>")

        else:
            isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')

    if not isMatch:
        return

    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showEntries(entryUrl=False,sSearchText=False,bGlobal=False):
    params = ParameterHandler()
    isTvshow = False
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'TPostMv">.*?href="([^"]+).*?data-src="([^"]+).*?Title">([^<]+)(.*?)</li>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        return
    items=[]
    total = len(aResult)
    for sUrl, sThumbnail, sName, sDummy in aResult:
        if sName:
            sName = sName.split('- Der Film')[0].strip() # Name nach dem - abschneiden und Array [0] nutzen
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isYear, sYear = cParser.parseSingleResult(sDummy, 'Year">([\d]+)</span>')  # Release Jahr
        isDuration, sDuration = cParser.parseSingleResult(sDummy, 'time">([\d]+)')  # Laufzeit
        if int(sDuration) <= int('70'): # Wenn Laufzeit kleiner oder gleich 70min, dann ist es eine Serie.
            isTvshow = True
        else:
            isTvshow = False
        if 'South Park: The End Of Obesity' in sName:
            isTvshow = False
        value= 'showSeasons' if isTvshow else 'getHosters'


        isQuality, sQuality = cParser.parseSingleResult(sDummy, 'Qlty">([^<]+)</span>')  # QualitÃ¤t
        isDesc, sDesc = cParser.parseSingleResult(sDummy, 'Description"><p>([^<]+)')  # Beschreibung
        sThumbnail = URL_MAIN + sThumbnail
        mediatype='tvshow' if isTvshow else 'movie'
        if isDesc:
            desc=sDesc
        else:
            desc='[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
        item={}
        item.setdefault('TVShowTitle',sName)
        item.setdefault('infoTitle', sName)  # für "Erweiterte Info"
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', desc)
        #optionale items
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sUrl', entryUrl)
        item.setdefault('sFunction',value)
        item.setdefault('mediatype',mediatype)
        item.setdefault('sDesc',desc)

        items.append(item)
    xsDirectory(items, SITE_NAME)

    if not bGlobal:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'href="([^"]+)">Next')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))

    sUrl = meta.get('entryUrl')
    sThumbnail = meta.get('sThumbnail')
    sName=meta.get('TVShowTitle')
    isDesc = meta.get('sDesc')
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    pattern = '<div class="tt_season">(.*)</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, '"#season-(\d+)')
    if not isMatch:
        return
    total = len(aResult)
    items=[]
    for sSeason in aResult:


        item={}
        item.setdefault('TVShowTitle',sName)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', 'Staffel ' + str(sSeason))
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', True)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', isDesc)
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sFunction','showEpisodes')
        item.setdefault('mediatype','episodes')
        item.setdefault('sSeason',sSeason)

        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def showEpisodes():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sName=meta.get('TVShowTitle')
    entryUrl = meta.get('entryUrl')
    sThumbnail = meta.get('sThumbnail')
    sSeason = meta.get('sSeason')
    isDesc = meta.get('sDesc')
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 4
    sHtmlContent = oRequest.request()
    pattern = 'id="season-%s(.*?)</ul>' % sSeason
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'data-title="Episode\s(\d+)')
    if not isMatch:
        return
    items=[]
    total = len(aResult)
    for sEpisode in aResult:
        item={}
        item.setdefault('TVShowTitle',sName)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', 'Episode ' + str(sEpisode))
        item.setdefault('entryUrl', entryUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', isDesc)
        #optionale items
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sFunction','showEpisodeHosters')
        item.setdefault('mediatype','episodes')
        item.setdefault('sSeason',sSeason)
        item.setdefault('episode',sEpisode)
        items.append(item)

    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()





def showEpisodeHosters():
    hosters = []
    params = ParameterHandler()
    # Parameter laden
    meta = json.loads(params.getValue('meta'))
    isProgressDialog=True
    isResolve = False
    isTvshow=False
    sUrl = meta.get('entryUrl')
    sSeason = meta.get('sSeason')
    sEpisode = meta.get('episode')
    sThumbnail=meta.get('sThumbnail')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'id="season-%s">(.*?)</ul>' % sSeason
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
    t = 0
    items=[]
    if isMatch:
        pattern = '>%s</a>(.*?)</li>' % sEpisode
        isMatch, sHtmlLink = cParser.parseSingleResult(sHtmlContainer, pattern)
        if isMatch:
            isMatch, aResult = cParser().parse(sHtmlLink, 'data-link="([^"]+)')
            if isMatch:
                for sUrl in aResult:
                    sName = cParser.urlparse(sUrl)
                    if sUrl.startswith('//'):
                        sUrl = 'https:' + sUrl
                    sUrl=resolver.resolve(sUrl)
                    streamUrl=sUrl
                    infoTitle=cParser.urlparse(sUrl)

                    sHoster=cParser.urlparse(streamUrl)
                    t += 100 / len(aResult)
                    if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                    if 'outube' in sHoster:
                        sHoster=sHoster.split('.')[0]+' Trailer'
                    items.append((sName, infoTitle, meta, False, sUrl, sThumbnail))
                if isProgressDialog:  progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)







def getHosters():
    hosters = []
    params = ParameterHandler()
    isProgressDialog=True
    isResolve = True
    isTvshow=False
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    sThumbnail=meta.get('sThumbnail')
    if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
    t = 0
    items=[]
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<iframe.*?src="([^"]+)'
    isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        sHtmlContainer = cRequestHandler(hUrl).request()
        isMatch, aResult = cParser().parse(sHtmlContainer, 'data-link="([^"]+)')
        if isMatch:
            sQuality = '720'
            for sUrl in aResult:
                sName = cParser.urlparse(sUrl)
                if sUrl.startswith('//'):
                    sUrl = 'https:' + sUrl
                sName = cParser.urlparse(sUrl)
                streamUrl=sUrl
                infoTitle=cParser.urlparse(sUrl)

                sHoster=cParser.urlparse(streamUrl)
                t += 100 / len(aResult)
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)


                if 'outube' in sHoster:
                    sHoster=sHoster.split('.')[0]+' Trailer'
                if not "einecloud" in sName:
                    items.append((sName, infoTitle, meta, False, sUrl, sThumbnail))
        if isProgressDialog:  progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)





def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText),sSearchText,bGlobal=False)



def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText),sSearchText,bGlobal=True)
