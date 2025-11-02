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

SITE_IDENTIFIER = 'moflix-stream'
SITE_NAME = 'Moflix-Stream'
SITE_ICON = 'moflix-stream.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'moflix-stream.xyz')
URL_MAIN = 'https://' + DOMAIN + '/'
# URL_MAIN = 'https://moflix-stream.xyz/'
URL_SEARCH = URL_MAIN + 'api/v1/search/%s?query=%s&limit=8'
URL_VALUE = URL_MAIN + 'api/v1/channel/%s?channelType=channel&restriction=&paginate=simple'
URL_HOSTER = URL_MAIN + 'api/v1/titles/%s?load=images,genres,productionCountries,keywords,videos,primaryVideo,seasons,compactCredits'


def load():
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Neue ", 'runPlugin&site=%s&function=showEntries&page=%s&sUrl=%s' % (SITE_NAME,'1', URL_VALUE % 'now-playing'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'movies'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Top Filme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'top-rated-movies'), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Serien ", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'series'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Collection ", 'runPlugin&site=%s&function=showCollections' % (SITE_NAME), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()




    


def showCollections():
    params = ParameterHandler()
    addDirectoryItem("American Pie Complete Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-american-pie-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Bud Spencer & Terence Hill Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'bud-spencer-terence-hill-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("DC Superhelden Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-dc-universum-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Ethan Hunt Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-mission-impossible-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Fast & Furious Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'fast-furious-movie-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Halloween Movie Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'halloween-movie-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Herr der Ringe Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'der-herr-der-ringe-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("James Bond Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-james-bond-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Jason Bourne Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-jason-bourne-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Jurassic Park Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-jurassic-park-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Kinder & Familienfilme", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'top-kids-liste'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Marvel Cinematic Universe Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-marvel-cinematic-universe-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Olsenbande Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-olsenbande-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Planet der Affen Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-planet-der-affen-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Rocky - The Knockout Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'rocky-the-knockout-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Star Trek Kinofilm Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-star-trek-movies-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Star Wars Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'the-star-wars-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Stirb Langsam Collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'stirb-langsam-collection'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("x-men-collection", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_VALUE % 'x-men-collection'), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()

def showEntries(entryUrl=False, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + '&page=' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=True)
    oRequest.addHeaderEntry('Referer', params.getValue('sUrl'))
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    aResults = jSearch['channel']['content']['data']
    total = len(aResults)
    if len(aResults) == 0:
        return
    items=[]
    for i in aResults:
        item={}
        sId = i['id']
        sName = i['name']
        if 'is_series' in i: isTvshow = i['is_series']
        function = 'showSeasons' if isTvshow else 'getHosters'
        if 'description' in i and i['description'] != '':
            plot= i['description']
        else:plot='[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)

        if 'poster' in i and i['poster'] != '': 
            sThumbnail=i['poster']
        else:sThumbnail=''
        mediaType='tvshow' if isTvshow else 'movie'
        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', URL_HOSTER % sId)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', plot)
        item.setdefault('sThumbnail', sThumbnail)
        item.setdefault('sName', sName)
        item.setdefault('sFunction', function)
        item.setdefault('sMediaType', mediaType)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    if not bGlobal:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showEntries&page=%s&sUrl=%s' % (SITE_NAME,int(sPageNr), entryUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showSeasons(bGlobal=False):
    
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    entryUrl = meta.get('entryUrl')
    sThumbnail = meta.get('sThumbnail')
    oRequest = cRequestHandler(entryUrl)
    mediaType=meta.get('sMediaType')
    oRequest.addHeaderEntry('Referer', entryUrl)
    oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    sDesc = jSearch['title']['description']
    aResults = jSearch['seasons']['data']
    aResults = sorted(aResults, key=lambda k: k['number'])
    total = len(aResults)
    if len(aResults) == 0:
        return
    items=[]
    sName=meta.get('sName')
    for i in aResults:
        item={}
        sId = i['title_id']
        sSeasonNr = str(i['number'])
        item.setdefault('sMediaType', mediaType)
        item.setdefault('TVShowTitle',sName)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', 'Staffel ' + sSeasonNr)
        item.setdefault('entryUrl', entryUrl)
        item.setdefault('isTvshow', True)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', sDesc)
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sUrl', entryUrl)
        item.setdefault('sSeasonNr', sSeasonNr)
        item.setdefault('sId', sId)
        item.setdefault('sFunction','showEpisodes')
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def showEpisodes(bGlobal=False):
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sId = meta.get('sId')
    sSeasonNr = meta.get('sSeasonNr')
    kName=meta.get('infoTitle')
    sUrl = URL_MAIN + 'api/v1/titles/%s/seasons/%s/episodes?perPage=100&query=&page=1' % (sId, sSeasonNr)
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', sUrl)
    oRequest.cacheTime = 60 * 60 * 4  # 4 Stunden
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    aResults = jSearch['pagination']['data']
    total = len(aResults)
    if len(aResults) == 0:
        return
    
    items=[]
    for i in aResults:
        sName = i['name']
        sEpisodeNr = str(i['episode_number'])
        sThumbnail = i['poster']
        name='Episode ' + sEpisodeNr + ' - ' + sName
        if 'description' in i and i['description'] != '': 
            desc=i['description']
        else:desc=meta.get('sDesc')
        item={}
        item.setdefault('from', 'showEpisodes')
        item.setdefault('sMediaType', 'episode')
        item.setdefault('TVShowTitle',kName)
        item.setdefault('infoTitle', kName)
        item.setdefault('title', name)
        item.setdefault('entryUrl', URL_MAIN + 'api/v1/titles/%s/seasons/%s/episodes/%s?load=videos,compactCredits,primaryVideo' % (sId, sSeasonNr, sEpisodeNr))
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', desc)        
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sSeasonNr', sSeasonNr)
        item.setdefault('sEpisodeNr', sEpisodeNr)
        items.append(item)

    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()



        

def showSearchEntries(entryUrl=False, bGlobal=False, sSearchText=''):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.addHeaderEntry('Referer', entryUrl)
    jSearch = json.loads(oRequest.request())
    if not jSearch: return
    aResults = jSearch['results']
    total = len(aResults)
    if len(aResults) == 0:
        return
    isTvshow = False
    items=[]
    for i in aResults:
        item={}
        if 'person' in i['model_type']: continue # 
        sId = i['id']
        sName = i['name']
        sYear = str(i['release_date'].split('-')[0].strip())
        if sSearchText.lower() and not cParser().search(sSearchText, sName.lower()): continue
        if 'is_series' in i: isTvshow = i['is_series']
        function = 'showSeasons' if isTvshow else 'getHosters'
        if 'description' in i and i['description'] != '':
            plot= i['description']
        else:plot='[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)

        if 'poster' in i and i['poster'] != '': 
            sThumbnail=i['poster']
        else:sThumbnail=''
        mediaType='tvshow' if isTvshow else 'movie'
        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', URL_HOSTER % sId)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', plot)
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sName', sName)
        item.setdefault('function', function)
        item.setdefault('sMediaType', mediaType)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()





        

def getHosters(bGlobal=False):
    
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl')
    isResolve = False
    isTvshow=False
    sThumbnail=meta.get('poster')
    isProgressDialog=True
    hosters = []
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', sUrl)
    jSearch = json.loads(oRequest.request())  # 
    if not jSearch: return
    
    if meta.get('sMediaType') == 'movie':
        aResults = jSearch['title']['videos']
    else:
        aResults = jSearch['episode']['videos']
    if len(aResults) == 0:
        return
    items=[]
    if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
    t = 0
        
    for i in aResults:
        item={}
        sQuality = str(i['quality'])
        if 'None' in sQuality: sQuality = '720p'
        sUrl = i['src']
        if 'Mirror' in i['name']:
            sName = cParser.urlparse(sUrl)
        else:
            sName = i['name'].split('-')[0].strip()
        if 'Poophq' in sName:
            sName = 'Veev'
        if 'Moflix-Stream.Click' in sName:
            sName = 'FileLions'
        if 'Moflix-Stream.Day' in sName:
            sName = 'VidGuard'
        #sName = sName.split('.')[0].strip()
        streamUrl=sUrl
        
        infoTitle=cParser.urlparse(sUrl)

        sHoster=cParser.urlparse(streamUrl)
        t += 100 / len(aResults)
        if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
                
        Request = cRequestHandler(streamUrl, caching=False)
        Request.request()
        sUrl = Request.getRealUrl()
        if 'outube' in sHoster:
            sHoster=sHoster.split('.')[0]+' Trailer'
        items.append((sName, infoTitle, meta, False, sUrl, sThumbnail))
    if isProgressDialog:  progressDialog.close()
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)





def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)



def _search(bGlobal, sSearchText):
    sID1 = quote(sSearchText)
    sID2 = cParser().quotePlus(sSearchText)
    showSearchEntries(URL_SEARCH % (sID1, sID2), False, sSearchText)