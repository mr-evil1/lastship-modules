# -*- coding: utf-8 -*-
import json, sys, xbmcgui, re
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting, setSetting
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.log_utils import log
from json import loads
oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'kinox'
SITE_NAME = 'KinoX'
SITE_ICON = 'kinox.png'

DOMAIN = getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'www12.kinoz.to')
URL_MAIN = 'https://' + DOMAIN
URL_NEWS = URL_MAIN + '/index.php'
URL_CINEMA_PAGE = URL_MAIN + '/Kino-Filme.html'
URL_GENRE_PAGE = URL_MAIN + '/Genre.html'
URL_MOVIE_PAGE = URL_MAIN + '/Movies.html'
URL_SERIE_PAGE = URL_MAIN + '/Series.html'
URL_DOCU_PAGE = URL_MAIN + '/Documentations.html'
URL_FAVOURITE_MOVIE_PAGE = URL_MAIN + '/Popular-Movies.html'
URL_FAVOURITE_SERIE_PAGE = URL_MAIN + '/Popular-Series.html'
URL_FAVOURITE_DOCU_PAGE = URL_MAIN + '/Popular-Documentations.html'
URL_LATEST_MOVIE_PAGE = URL_MAIN + '/Latest-Movies.html'
URL_LATEST_SERIE_PAGE = URL_MAIN + '/Latest-Series.html'
URL_LATEST_DOCU_PAGE = URL_MAIN + '/Latest-Documentations.html'
URL_SEARCH = URL_MAIN + '/Search.html?q=%s'
URL_MIRROR = URL_MAIN + '/aGET/Mirror/'
URL_EPISODE_URL = URL_MAIN + '/aGET/MirrorByEpisode/'
URL_AJAX = URL_MAIN + '/aGET/List/'
URL_LANGUAGE = URL_MAIN + '/aSET/PageLang/1'


def load():
    
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showNews&sUrl=%s&page=%s&mediaType=%s' % (SITE_NAME, URL_NEWS, 1, 'news'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme", 'runPlugin&site=%s&function=showMovieMenu&sUrl=%s&mediaType=%s' % (SITE_NAME, URL_MOVIE_PAGE, 'movie'), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showSeriesMenu&sUrl=%s&mediaType=%s&page=1' % (SITE_NAME, URL_SERIE_PAGE, 'series'), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Dokus", 'runPlugin&site=%s&function=showDocuMenu&sUrl=%s&mediaType=%s&page=1' % (SITE_NAME, URL_DOCU_PAGE, 'documentation'), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def __createMenuEntry(oGui, sFunction, sLabel, dOutputParameter):
    parms = ParameterHandler()
    
    try:
        for param, value in dOutputParameter.items():
            parms.setParam(param, value)
    except Exception as e:
        logger.error("Can't add parameter to menu entry with label: %s: %s" % (sLabel, e))
    
    sPluginUrl = 'runPlugin&site=%s&function=%s' % (SITE_NAME, sFunction)
    
    for k, v in dOutputParameter.items():
        sPluginUrl += '&%s=%s' % (k, quote(str(v)))
    
    addDirectoryItem(sLabel, sPluginUrl, SITE_ICON, 'DefaultGenre.png')


def showMovieMenu():
    addDirectoryItem("Kino", 'runPlugin&site=%s&function=showCinemaMovies' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("A-Z", 'runPlugin&site=%s&function=showCharacters&sUrl=%s&page=1&mediaType=movie' % (SITE_NAME,URL_MOVIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showGenres&sUrl=%s' % (SITE_NAME,URL_FAVOURITE_MOVIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Beliebte Filme", 'runPlugin&site=%s&function=showFavItems&sUrl=%s' % (SITE_NAME, URL_FAVOURITE_MOVIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Neueste Filme", 'runPlugin&site=%s&function=showFavItems&sUrl=%s' % (SITE_NAME, URL_LATEST_MOVIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showSeriesMenu():
    addDirectoryItem("A-Z", 'runPlugin&site=%s&function=showCharacters&sUrl=%s&page=1&mediaType=series' % (SITE_NAME,URL_SERIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Beliebte Serien", 'runPlugin&site=%s&function=showFavItems&sUrl=%s' % (SITE_NAME, URL_FAVOURITE_SERIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Neueste Serien", 'runPlugin&site=%s&function=showFavItems&sUrl=%s' % (SITE_NAME, URL_LATEST_SERIE_PAGE), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showDocuMenu():
    addDirectoryItem("A-Z", 'runPlugin&site=%s&function=showCharacters&sUrl=%s&page=1&mediaType=documentation' % (SITE_NAME,URL_DOCU_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Beliebte Dokus", 'runPlugin&site=%s&function=showFavItems&sUrl=%s' % (SITE_NAME, URL_FAVOURITE_DOCU_PAGE), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Neueste Dokus", 'runPlugin&site=%s&function=showFavItems&sUrl=%s' % (SITE_NAME, URL_LATEST_DOCU_PAGE), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def __createLanguage(sLangID):
    return {'1': 'DE', '2': 'EN', '4': 'ZA', '5': 'ES', '6': 'FR', '7': 'TR',
            '8': 'JA', '9': 'AR', '11': 'IT', '12': 'HR', '13': 'SR',
            '14': 'BS', '15': 'DE / EN', '16': 'NL', '17': 'KO',
            '24': 'EL', '25': 'RU', '26': 'HI', }.get(sLangID, sLangID)


def __checkSubLanguage(sTitle):
    if ' subbed*' not in sTitle:
        return [sTitle, '']
    temp = sTitle.split(' *')
    subLang = temp[-1].split('subbed*')[0].strip()
    title = ' '.join(temp[0:-1]).strip()
    return [title, 'de'] if subLang == 'german' else [title, subLang]


def __getHtmlContent(sUrl=None, ignoreErrors=False):
    parms = ParameterHandler()
    if sUrl is None and not parms.exist('sUrl'):
        logger.error('There is no url we can request.')
        return False
    elif sUrl is None:
        sUrl = parms.getValue('sUrl')
    sPrefLang = __getPreferredLanguage()
    oRequest = cRequestHandler(sUrl, ignoreErrors=ignoreErrors)
    sPrefLang = __getPreferredLanguage()
    oRequest.addHeaderEntry('Cookie', sPrefLang + 'ListDisplayYears=Always;')
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    return oRequest.request()


def __getPreferredLanguage():
    sLanguage = getSetting('prefLanguage', '1')
    if sLanguage == '1':
        sPrefLang = 'ListNeededLanguage=25%2C24%2C26%2C2%2C5%2C6%2C7%2C8%2C11%2C15%2C16%2C9%2C12%2C13%2C14%2C17%2C4'
    elif sLanguage == '2':
        sPrefLang = 'ListNeededLanguage=25%2C24%2C26%2C5%2C6%2C7%2C8%2C11%2C15%2C16%2C9%2C12%2C13%2C14%2C17%2C4%2C1'
    else:
        sPrefLang = ''
    return sPrefLang


def __displayItems(sGui, sHtmlContent):
    parms = ParameterHandler()
    items = []
    
    pattern = '<td class="Icon"><img width="16" height="11" src="/gr/sys/lng/(\d+).png" alt="language"></td>' + \
              '.*?title="([^\"]+)".*?<td class="Title">.*?<a href="([^\"]+)" onclick="return false;">([^<]+)</a> <span class="Year">([0-9]+)</span>'
    
    aResult = cParser.parse(sHtmlContent, pattern)
    if not aResult[0]:
        logger.error('Could not find an item')
        return

    for aEntry in aResult[1]:
        item = {}
        sTitle = aEntry[3]
        sTitle, subLang = __checkSubLanguage(sTitle)
        sLang = __createLanguage(aEntry[0])
        sUrl = URL_MAIN + aEntry[2]
        sYear = aEntry[4]

        if aEntry[1] == 'movie' or aEntry[1] == 'cinema':
            mediaType = 'movie'
        elif aEntry[1] == 'series':
            mediaType = 'series'
        else:
            mediaType = 'documentation'
            
        sFullTitle = "%s (%s) [%s]" % (sTitle, sYear, sLang)
        
        item.setdefault('poster', '')
        
        item.setdefault('title', sFullTitle)
        item.setdefault('sUrl', sUrl)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('infoTitle', sTitle)
        item.setdefault('year', sYear)
        item.setdefault('lang', sLang)
        item.setdefault('mediaType', mediaType)

        item.setdefault('sFunction', 'parseMovieEntrySite')
        
        if mediaType == 'series':
            item.setdefault('isTvshow', True)
        else:
            item.setdefault('isTvshow', False)

        items.append(item)

    xsDirectory(items, SITE_NAME)


def showFavItems():
    sHtmlContent = __getHtmlContent()
    __displayItems(False, sHtmlContent)
    setEndOfDirectory()


def showNews():
    parms = ParameterHandler()
    sUrl = parms.getValue('sUrl')
    pattern = '<div class="Opt leftOpt Headlne"><h1>([a-zA-Z0-9\s.]+)</h1></div>\s*(?:<div.*?)?<div class="Opt rightOpt Hint">Insgesamt: (.*?)</div>'
    sHtmlContent = __getHtmlContent(sUrl)
    aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        for aEntry in aResult[1]:
            sTitle = str(aEntry[0]) + ' (' + str(aEntry[1]) + ')'
            dOutputParameter = {'sUrl': URL_NEWS, 'page': 1, 'mediaType': 'news', 'sNewsTitle': aEntry[0]}
            __createMenuEntry(False, 'parseNews', sTitle, dOutputParameter)
    setEndOfDirectory()





def parseNews():
    parms = ParameterHandler()
    sUrl = parms.getValue('sUrl')
    sNewsTitle = parms.getValue('sNewsTitle')
    if 'Serien' in sNewsTitle and 'Filme' not in sNewsTitle:
        mediaType = 'series'
    else:
        mediaType = 'movie'
    pattern = '<div class="Opt leftOpt Headlne"><h1>' + sNewsTitle \
              + '</h1></div>(.*?)<div class="ModuleFooter">'
    sHtmlContent = __getHtmlContent(sUrl)
    aResult = cParser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        logger.info("Can't get any news")
        oGui.setEndOfDirectory()
        return

    pattern = '<td class="Icon"><img src="/gr/sys/lng/(\d+).png" alt="language" width="16" height="11".*?<td class="Title.*?rel="([^"]+)"><(?:a|span) href="([^\"]+)".*?class="OverlayLabel">([^<]+)(?:<span class="EpisodeDescr">)?([^<]+)'
    aResult = cParser.parse(aResult[1][0], pattern)
    if not aResult[0]:
        logger.info("Can't get any news")
        oGui.setEndOfDirectory()
        return
    total = len(aResult[1])

    items = []

    for aEntry in aResult[1]:
        item={}
        
        sLang = __createLanguage(aEntry[0])
        sTitle = aEntry[3] + aEntry[4]
        if sTitle.endswith(': '):
            sTitle = sTitle[:-2]
        sTitle, subLang = __checkSubLanguage(sTitle)
        
        sThumbnail=URL_MAIN + str(aEntry[1])
        sUrl = aEntry[2]
        aUrl = sUrl.split(',')
        if len(aUrl) > 0:
            sUrl = aUrl[0]
            item.setdefault('lang', sLang)
            item.setdefault('title', sTitle)
            item.setdefault('infoTitle', sTitle)
            item.setdefault('sUrl', URL_MAIN + sUrl)
            item.setdefault('entryUrl', URL_MAIN + sUrl)
            item.setdefault('poster', sThumbnail)
            item.setdefault('sublang', subLang)
            item.setdefault('sFunction', 'parseMovieEntrySite')
            
            if mediaType == 'series':
                item.setdefault('isTvshow', True)
                item.setdefault('mediaType', mediaType)
            else:
                item.setdefault('isTvshow', False)
                item.setdefault('mediaType', mediaType)
            items.append(item)
            
    
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def showCharacters():
    parms = ParameterHandler()
    if parms.exist('sUrl') and parms.exist('page') and parms.exist('mediaType'):
        siteUrl = parms.getValue('sUrl')
        mediaType=parms.getValue('mediaType')
        sHtmlContent = __getHtmlContent(siteUrl)
        pattern = 'class="LetterMode.*?>([^>]+)</a>'
        aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        for aEntry in aResult[1]:
            dOutputParameter = {}
            dOutputParameter['character']=aEntry[0]
            dOutputParameter['mediaType'] = mediaType
            if parms.exist('mediaTypePageId'):
                dOutputParameter['mediaTypePageId'] = parms.getValue('mediaTypePageId')
                
            __createMenuEntry(False, 'ajaxCall', aEntry, dOutputParameter)
    setEndOfDirectory()


def showGenres():
    logger.info('load displayGenreSite')
    pattern = '<td class="Title"><a.*?href="/Genre/([^"]+)">([^<]+)</a>.*?Tipp-([0-9]+).html">'
    sHtmlContent = __getHtmlContent(URL_GENRE_PAGE)
    aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        for aEntry in aResult[1]:
            iGenreId = aEntry[2]
            __createMenuEntry(False, 'showCharacters', aEntry[1], {'page': 1, 'mediaType': 'fGenre', 'mediaTypePageId': iGenreId, 'sUrl': URL_MOVIE_PAGE})
    setEndOfDirectory()


def showCinemaMovies():
    logger.info('load displayCinemaSite')
    _cinema(False)
    setEndOfDirectory()


def _cinema(oGui):
    items = []
    pattern = '<div class="Opt leftOpt Headlne"><a title="(.*?)" href="(.*?)">.*?src="(.*?)".*?class="Descriptor">(.*?)</div.*?/lng/([0-9]+).png".*?IMDb:</b> (.*?) /'
    sHtmlContent = __getHtmlContent(URL_CINEMA_PAGE)
    aResult = cParser.parse(sHtmlContent, pattern)
    if not aResult[0]: return
    
    for aEntry in aResult[1]:
        item = {}
        sMovieTitle = aEntry[0]
        lang = __createLanguage(aEntry[4])
        rating = aEntry[5]
        sUrl = URL_MAIN + str(aEntry[1])
        thumbnail = URL_MAIN + str(aEntry[2])
        
        sFullTitle = "%s [%s]" % (sMovieTitle, lang)
        
        item.setdefault('title', sFullTitle)
        item.setdefault('infoTitle', sMovieTitle)
        item.setdefault('sUrl', sUrl)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('poster', thumbnail)
        item.setdefault('plot', aEntry[3])
        item.setdefault('rating', rating)
        item.setdefault('isTvshow', False)
        item.setdefault('sFunction', 'parseMovieEntrySite')
        
        items.append(item)
    
    xsDirectory(items, SITE_NAME)


def parseMovieEntrySite():
    log('[KINOX] ==================== parseMovieEntrySite START ====================')
    parms = ParameterHandler()
    log('[KINOX] STEP 1: ParameterHandler erstellt')
    
    parms = json.loads(parms.getValue('meta'))
    log('[KINOX] STEP 2: Meta-Parameter geladen: %s' % str(parms))
    
    if not 'sUrl' in parms:
        log('[KINOX] FEHLER: Keine sUrl in Parametern gefunden!')
        return
    
    sUrl = parms.get('sUrl')
    log('[KINOX] STEP 3: URL extrahiert: %s' % sUrl)
    
    sHtmlContent = __getHtmlContent(sUrl)
    log('[KINOX] STEP 4: HTML-Content abgerufen (Länge: %d Zeichen)' % len(sHtmlContent) if sHtmlContent else 'FEHLER: Kein Content!')
    
    sMovieTitle = __createMovieTitle(sHtmlContent)
    log('[KINOX] STEP 5: Movie-Titel erstellt: %s' % sMovieTitle)
    
    result = cParser.parse(sHtmlContent, '<div class="Grahpics">.*?<img src="([^"]+)"')
    thumbnail = URL_MAIN + str(result[1][0]) if result[0] else False
    log('[KINOX] STEP 6: Thumbnail erstellt: %s' % thumbnail)
    
    bIsSerie =__isSerie(sHtmlContent)
    log('[KINOX] STEP 7: Ist Serie? %s' % ('JA' if bIsSerie else 'NEIN'))
    
    if bIsSerie:
        log('[KINOX] STEP 8: Serie wird verarbeitet...')
        items = []
        aSeriesItems = parseSerieSite(sHtmlContent)
        log('[KINOX] STEP 9: Serie-Items geparst, Ergebnis: %s' % str(aSeriesItems[0]))
        
        if not aSeriesItems[0]: 
            log('[KINOX] FEHLER: Keine Staffeln gefunden!')
            setEndOfDirectory()
            return
        
        log('[KINOX] STEP 10: Anzahl Staffeln gefunden: %d' % len(aSeriesItems[1]))
        for seasonNum in aSeriesItems[1]:
            log('[KINOX]   -> Erstelle Staffel %s' % seasonNum)
            
            item = {}
            seasonTitle = '%s - Staffel %s' % (sMovieTitle, seasonNum)
            
            
            item.setdefault('title', seasonTitle)
            item.setdefault('infoTitle', sMovieTitle)
            item.setdefault('sUrl', sUrl)
            item.setdefault('entryUrl', sUrl)
            item.setdefault('season', seasonNum)
            item.setdefault('poster', thumbnail)
            item.setdefault('isTvshow', True)
            item.setdefault('sFunction', 'showEpisodes')
            
            items.append(item)
        
        log('[KINOX] STEP 11: %d Staffel-Items erstellt, rufe xsDirectory auf...' % len(items))
        xsDirectory(items, SITE_NAME)
        setEndOfDirectory()
        log('[KINOX] ==================== parseMovieEntrySite ENDE (Serie) ====================')
        
    else:
        log('[KINOX] STEP 8: Film wird verarbeitet...')
        logger.info('Movie')
        showHosters()
        log('[KINOX] ==================== parseMovieEntrySite ENDE (Film) ====================')
        return


def showEpisodes():
    log('[KINOX] ==================== showEpisodes START ====================')
    
    parms = ParameterHandler()
    log('[KINOX] STEP 1: ParameterHandler erstellt')
    
    parms = json.loads(parms.getValue('meta'))
    log('[KINOX] STEP 2: Meta-Parameter geladen: %s' % str(parms))
    
    sUrl = parms.get('sUrl')
    log('[KINOX] STEP 3: URL: %s' % sUrl)
    
    seasonNum = parms.get('season')
    log('[KINOX] STEP 4: Season Nummer: %s (Typ: %s)' % (seasonNum, type(seasonNum).__name__))
    
    if seasonNum is None:
        log('[KINOX] FEHLER: seasonNum ist None!')
        setEndOfDirectory()
        return
    
    sHtmlContent = __getHtmlContent(sUrl)
    log('[KINOX] STEP 5: HTML-Content abgerufen (Länge: %d Zeichen)' % len(sHtmlContent) if sHtmlContent else 'FEHLER: Kein Content!')
    
    sMovieTitle = __createMovieTitle(sHtmlContent)
    log('[KINOX] STEP 6: Movie-Titel: %s' % sMovieTitle)
    
    result = cParser.parse(sHtmlContent, '<div class="Grahpics">.*?<img src="([^"]+)"')
    thumbnail = URL_MAIN + str(result[1][0]) if result[0] else False
    log('[KINOX] STEP 7: Thumbnail: %s' % thumbnail)
    
    log('[KINOX] STEP 8: Rufe parseSerieEpisodes auf mit seasonNum=%s...' % seasonNum)
    aSeriesItems = parseSerieEpisodes(sHtmlContent, seasonNum)
    log('[KINOX] STEP 9: parseSerieEpisodes Ergebnis: %d Episoden gefunden' % len(aSeriesItems))
    
    if not aSeriesItems: 
        log('[KINOX] FEHLER: Keine Episoden gefunden!')
        setEndOfDirectory()
        return
    
    items = []
    for item_data in aSeriesItems:
        log('[KINOX]   -> Erstelle Episode: %s' % item_data['title'])
        item = {}
        sShowTitle = sMovieTitle.split('(')[0].split('*')[0]
        item.setdefault('title', item_data['title'])
        item.setdefault('infoTitle', sShowTitle)
        item.setdefault('sUrl', item_data['url']) 
        item.setdefault('entryUrl', sUrl) 
        item.setdefault('poster', thumbnail)
        item.setdefault('season', item_data['season'])
        item.setdefault('episode', item_data['episode'])
        item.setdefault('isTvshow', False)
        item.setdefault('sFunction', 'showHosters') 
        
        items.append(item)
    
    log('[KINOX] STEP 10: %d Episoden-Items erstellt' % len(items))
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()
    log('[KINOX] ==================== showEpisodes ENDE ====================')


def __createMovieTitle(sHtmlContent):
    log('[KINOX] --- __createMovieTitle START ---')
    
    # Versuche zuerst das h1-span Pattern
    pattern = '<h1><span style="display: inline-block">(.*?)</span></h1>'
    log('[KINOX] TITLE STEP 1: Versuche h1-span Pattern')
    aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        title = str(aResult[1][0])
        log('[KINOX] TITLE ERFOLG: h1-span Pattern gefunden: %s' % title)
        log('[KINOX] --- __createMovieTitle ENDE ---')
        return title
    log('[KINOX] TITLE STEP 1: h1-span Pattern nicht gefunden')
    
    # Fallback: Extrahiere aus dem title-Tag bis "Stream"
    pattern = '<title>([^<]+?)\s+Stream\s+.*?</title>'
    log('[KINOX] TITLE STEP 2: Versuche title-Tag Pattern mit "Stream"')
    aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        title = str(aResult[1][0]).strip()
        log('[KINOX] TITLE ERFOLG: title-Tag Pattern gefunden: %s' % title)
        log('[KINOX] --- __createMovieTitle ENDE ---')
        return title
    log('[KINOX] TITLE STEP 2: title-Tag Pattern mit "Stream" nicht gefunden')
    
    # Fallback 2: Extrahiere aus title-Tag bis "auf Kinox"
    pattern = '<title>(.+?)\s+(?:online anschauen|Stream).*?(?:auf Kinox|Kinox)'
    log('[KINOX] TITLE STEP 3: Versuche title-Tag Pattern mit "Kinox"')
    aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        title = str(aResult[1][0]).strip()
        log('[KINOX] TITLE ERFOLG: title-Tag Pattern mit Kinox gefunden: %s' % title)
        log('[KINOX] --- __createMovieTitle ENDE ---')
        return title
    log('[KINOX] TITLE STEP 3: title-Tag Pattern mit "Kinox" nicht gefunden')
    
    # Fallback 3: Nimm alles vor " - "
    pattern = '<title>([^<]+?)\s+-\s+.*?</title>'
    log('[KINOX] TITLE STEP 4: Versuche title-Tag Pattern mit " - "')
    aResult = cParser.parse(sHtmlContent, pattern)
    if aResult[0]:
        title = str(aResult[1][0]).strip()
        log('[KINOX] TITLE ERFOLG: title-Tag Pattern mit " - " gefunden: %s' % title)
        log('[KINOX] --- __createMovieTitle ENDE ---')
        return title
    log('[KINOX] TITLE STEP 4: title-Tag Pattern mit " - " nicht gefunden')
    
    log('[KINOX] TITLE FEHLER: Kein Pattern hat einen Titel gefunden!')
    log('[KINOX] --- __createMovieTitle ENDE ---')
    return False


def parseSerieSite(sHtmlContent):
    pattern = '<option[^>]+value="(\d+)"[^>]+>Staffel.+?</option>'
    return cParser.parse(sHtmlContent, pattern)

def parseSerieEpisodes(sHtmlContent, seasonNum):
    log('[KINOX] ---------- parseSerieEpisodes START ----------')
    log('[KINOX] PARSE STEP 1: seasonNum Input: %s (Typ: %s)' % (seasonNum, type(seasonNum).__name__))
    
    aSeriesItems = []
    
    # Überprüfung ob seasonNum gültig ist
    if seasonNum is None:
        log('[KINOX] PARSE FEHLER: seasonNum ist None!')
        return aSeriesItems
    
    try:
        seasonNum = int(seasonNum)
        log('[KINOX] PARSE STEP 2: seasonNum erfolgreich zu int konvertiert: %d' % seasonNum)
    except (ValueError, TypeError) as e:
        log('[KINOX] PARSE FEHLER: Konvertierung zu int fehlgeschlagen: %s' % str(e))
        return aSeriesItems
    
    # Ersten Pattern parsen
    pattern = 'id="SeasonSelection" rel="([^"]+)"'
    log('[KINOX] PARSE STEP 3: Suche nach SeasonSelection Pattern...')
    aResult = cParser.parse(sHtmlContent, pattern)
    log('[KINOX] PARSE STEP 4: SeasonSelection gefunden: %s' % aResult[0])
    
    if aResult[0]:
        aSeriesUrls = aResult[1][0].split("&")
        sSeriesUrl = '&' + str(aSeriesUrls[0]) + '&' + str(aSeriesUrls[1])
        log('[KINOX] PARSE STEP 5: Series URL erstellt: %s' % sSeriesUrl)
    else:
        log('[KINOX] PARSE FEHLER: Keine SeasonSelection gefunden!')
        return aSeriesItems
    
    # Zweiten Pattern für die spezifische Staffel parsen
    pattern = '<option.*?value="%d" rel="([^"]+)".*?>Staffel.*?</option>' % seasonNum
    log('[KINOX] PARSE STEP 6: Pattern für Staffel %d: %s' % (seasonNum, pattern))
    aResult = cParser.parse(sHtmlContent, pattern)
    log('[KINOX] PARSE STEP 7: Staffel Pattern gefunden: %s' % aResult[0])
    
    if aResult[0]:
        log('[KINOX] PARSE STEP 8: Episoden-IDs: %s' % str(aResult[1]))
        aSeriesIds = aResult[1][0].split(',')
        log('[KINOX] PARSE STEP 9: Anzahl Episoden: %d' % len(aSeriesIds))
        
        for iSeriesIds in aSeriesIds:
            log('[KINOX]   -> Verarbeite Episode-ID: %s' % iSeriesIds)
            aSeries = {}
            iEpisodeNum = iSeriesIds
            sTitel = 'Folge ' + str(iEpisodeNum)
            sUrl = URL_EPISODE_URL + sSeriesUrl + '&Season=' + str(seasonNum) + '&Episode=' + str(iEpisodeNum)
            log('[KINOX]      Episode URL: %s' % sUrl)
            
            aSeries['title'] = sTitel
            aSeries['url'] = sUrl
            aSeries['season'] = seasonNum
            aSeries['episode'] = iEpisodeNum
            aSeriesItems.append(aSeries)
    else:
        log('[KINOX] PARSE FEHLER: Keine Episoden für Staffel %d gefunden!' % seasonNum)
    
    log('[KINOX] PARSE STEP 10: %d Episoden erfolgreich geparst' % len(aSeriesItems))
    log('[KINOX] ---------- parseSerieEpisodes ENDE ----------')
    return aSeriesItems

def __isSerie(sHtmlContent):
    pattern = 'id="SeasonSelection" rel="([^"]+)"'
    aResult = cParser.parse(sHtmlContent, pattern)
    return aResult[0] == True


def ajaxCall():
    parms = ParameterHandler()
    iPage = parms.getValue('page')
    sMediaType = parms.getValue('mediaType')
    iMediaTypePageId = parms.getValue('mediaTypePageId')
    sCharacter = parms.getValue('character')
        
    logger.info('MediaType: ' + sMediaType + ' , Page: ' + str(iPage) + ' , iMediaTypePageId: ' + str(
        iMediaTypePageId) + ' , sCharacter: ' + str(sCharacter))
        
    sHtmlContent = __getAjaxContent(sMediaType, iPage, iMediaTypePageId, False, sCharacter)
    
    if not sHtmlContent:
        setEndOfDirectory()
        return
        
    aData = loads(sHtmlContent)
    items = []

    pattern = '<div class="Opt leftOpt Headlne"><a title="(.*?)" href="(.*?)">.*?src="(.*?)".*?class="Descriptor">(.*?)</div.*?lng/(.*?).png'
    aResult = cParser.parse(aData['Content'], pattern)
    
    if aResult[0]:
        iTotalCount = int(aData['Total'])
        
        for aEntry in aResult[1]:
            item = {}
            sMovieTitle, subLang = __checkSubLanguage(aEntry[0])
            lang = __createLanguage(aEntry[4])
            sUrl = URL_MAIN + str(aEntry[1])
            thumbnail = URL_MAIN + str(aEntry[2])
            
            sFullTitle = "%s [%s]" % (sMovieTitle, lang)
            
            item.setdefault('title', sFullTitle)
            item.setdefault('infoTitle', sMovieTitle)
            item.setdefault('sUrl', sUrl)
            item.setdefault('entryUrl', sUrl)
            item.setdefault('poster', thumbnail)
            item.setdefault('plot', aEntry[3])
            item.setdefault('sFunction', 'parseMovieEntrySite')

            if sMediaType == 'series':
                item.setdefault('isTvshow', True)
            else:
                item.setdefault('isTvshow', False)
                
            items.append(item)
            
        xsDirectory(items, SITE_NAME)

        iNextPage = int(iPage) + 1
        if __createDisplayStart(iNextPage) < iTotalCount:
            parms = ParameterHandler()
            dNextParams = {'page': iNextPage, 'character': sCharacter, 'mediaType': sMediaType}
            if iMediaTypePageId:
                dNextParams['mediaTypePageId'] = iMediaTypePageId
            
            sPluginUrl = 'runPlugin&site=%s&function=ajaxCall' % SITE_NAME
            for k, v in dNextParams.items():
                sPluginUrl += '&%s=%s' % (k, quote(str(v)))
            
            addDirectoryItem('[B]>>> Nächste Seite (%s) [/B]' % iNextPage, sPluginUrl, 'next.png', 'next.png')
            
    setEndOfDirectory()


def __createDisplayStart(iPage):
    return (30 * int(iPage)) - 30


def __getAjaxContent(sMediaType, iPage, iMediaTypePageId, metaOn, sCharacter=''):
    iDisplayStart = __createDisplayStart(iPage)
    sPrefLang = __getPreferredLanguage()
    oRequest = cRequestHandler(URL_AJAX)
    
    if not iMediaTypePageId:
        oRequest.addParameters('additional', '{"fType":"' + str(sMediaType) + '","Length":60,"fLetter":"' + str(sCharacter) + '"}')
    else:
        oRequest.addParameters('additional', '{"foo":"bar","' + str(
            sMediaType) + '":"' + iMediaTypePageId + '","fType":"movie","fLetter":"' + str(sCharacter) + '"}')
            
    oRequest.addParameters('iDisplayLength', '30')
    oRequest.addParameters('iDisplayStart', iDisplayStart)
    
    oRequest.addParameters('ListMode', 'cover')
    oRequest.addParameters('Page', str(iPage))
    oRequest.addParameters('Per_Page', '30')
    oRequest.addParameters('per_page', '30')
    oRequest.addParameters('dir', 'desc')
    oRequest.addParameters('sort', 'title')
    
    sUrl = oRequest.getRequestUri()
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Cookie', sPrefLang + 'ListDisplayYears=Always;')
    return oRequest.request()


def showHosters():
    log('[KINOX] ==================== showHosters START ====================')
    isProgressDialog=True
    params = ParameterHandler()
    log('[KINOX] HOSTER STEP 1: ParameterHandler erstellt')
    
    sUrl = ''
    try:
        meta = json.loads(params.getValue('meta'))
        log('[KINOX] HOSTER STEP 2: Meta-Parameter geladen: %s' % str(meta))
    except Exception as e:
        log('[KINOX] HOSTER FEHLER: Meta konnte nicht geladen werden: %s' % str(e))
        meta = {}
    
    sUrl = meta.get('sUrl')
    log('[KINOX] HOSTER STEP 3: URL aus meta: %s' % sUrl)
    
    if not sUrl: 
        sUrl = params.getValue('sUrl')
        log('[KINOX] HOSTER STEP 3b: URL aus params (Fallback): %s' % sUrl)
    
    if not sUrl:
        log('[KINOX] HOSTER FEHLER: Keine URL gefunden!')
        return
    
    log('[KINOX] HOSTER STEP 4: Rufe URL ab: %s' % sUrl)
    sHtmlContent = cRequestHandler(sUrl).request()
    log('[KINOX] HOSTER STEP 5: HTML-Content erhalten (Länge: %d Zeichen)' % len(sHtmlContent) if sHtmlContent else 'FEHLER: Kein Content!')
    
    pattern = 'class="MirBtn.*?rel="([^"]+)".*?class="Named">([^<]+)</div>(.*?)</div>'
    log('[KINOX] HOSTER STEP 6: Parse Hoster mit Pattern...')
    aResult = cParser.parse(sHtmlContent, pattern)
    log('[KINOX] HOSTER STEP 7: Hoster gefunden: %s (Anzahl: %d)' % (aResult[0], len(aResult[1]) if aResult[0] else 0))
    
    items_for_container = []
    
    sThumbnail = meta.get('poster', SITE_ICON)
    sTitle = meta.get('infoTitle', 'Unbekannter Titel')
    log('[KINOX] HOSTER STEP 8: Thumbnail: %s, Titel: %s' % (sThumbnail, sTitle))
    
    if aResult[0]:
        log('[KINOX] HOSTER STEP 9: Verarbeite %d Hoster...' % len(aResult[1]))
        for idx, aEntry in enumerate(aResult[1]):
            sHoster = aEntry[1]
            log('[KINOX]   -> Hoster %d: %s' % (idx + 1, sHoster))
            
            if isBlockedHoster(sHoster,isResolve=False)[0]:
                log('[KINOX]      ÜBERSPRUNGEN: Hoster ist blockiert')
                continue
            
            pattern_mirror = '<b>Mirror</b>: [0-9]+/([0-9]+)'
            aResultMirror = cParser.parse(aEntry[2], pattern_mirror)
            mirrors = 1
            
            if aResultMirror[0] and aResultMirror[1] and len(aResultMirror[1][0]) > 0:
                try:
                    mirrors = int(aResultMirror[1][0])
                    log('[KINOX]      Mirrors gefunden: %d' % mirrors)
                except ValueError:
                    mirrors = 1
                    log('[KINOX]      Mirror-Parsing fehlgeschlagen, verwende 1')
            
            if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
            t = 0
            if isProgressDialog: progressDialog.update(t)
            
            
            for i in range(1, mirrors + 1):
                sHosterUrl = URL_MIRROR + cParser.unquotePlus(aEntry[0])
                sMirrorName = ''
                if mirrors > 1:
                    sMirrorName = ' Mirror ' + str(i)
                    sHosterUrl = cParser.replace(r'Mirror=[0-9]+', 'Mirror=' + str(i), sHosterUrl)
                
                log('[KINOX]      -> Mirror %d URL: %s' % (i, sHosterUrl))
                t += 100/ int(mirrors)
                if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sMirrorName)
                
                hoster_url = getHosterUrl(sHosterUrl)
                log('[KINOX]      -> Hoster URL abgerufen: %s' % hoster_url)
                
                items_for_container.append((
                    sHoster + sMirrorName,    
                    sTitle,                   
                    meta,                     
                    False,                    
                    hoster_url,               
                    sThumbnail                
                ))
                t += 100 / int(mirrors)
                if isProgressDialog:  progressDialog.close()
    else:
        log('[KINOX] HOSTER FEHLER: Keine Hoster im HTML gefunden!')

    log('[KINOX] HOSTER STEP 10: Insgesamt %d Items für Container erstellt' % len(items_for_container))
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items_for_container)))
    log('[KINOX] HOSTER STEP 11: Container-Update URL: %s' % url)
    logger.info("KINX_DBG: ERZWINGE CONTAINER-UPDATE mit %d Hostern" % len(items_for_container))
    execute('Container.Update(%s)' % url)
    log('[KINOX] ==================== showHosters ENDE ====================')



def getHosterUrl(sUrl=False):
    sHtmlContent = cRequestHandler(sUrl).request()
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    sHtmlContent = oRequest.request()
    isMatch, sStreamUrl = cParser.parseSingleResult(sHtmlContent, 'a\shref=\\\\".*?(https?:.*?)\\\\"')
    if not isMatch:
        isMatch, sStreamUrl = cParser.parseSingleResult(sHtmlContent, '<iframe src=[^"]*"([^"]+)')
    if isMatch:
        if sStreamUrl.startswith('//'):
            sStreamUrl = 'https:' + sStreamUrl
        if 'streamcrypt.net' in sStreamUrl:
            oRequest = cRequestHandler(sStreamUrl, caching=False)
            oRequest.request()
            sStreamUrl = oRequest.getRealUrl()
        if 'thevideo' in sStreamUrl:
            sStreamUrl = sStreamUrl.replace('embed-', 'stream').replace('html', 'mp4')
            sUrl = _redirectHoster(sStreamUrl)
            return sUrl
        return sStreamUrl


def _redirectHoster(url):
    try:
        from urllib.error import HTTPError
        from urllib.request import build_opener
    except ImportError:
        from urllib2 import build_opener, HTTPError
        
    opener = build_opener()
    opener.addheaders = [('Referer', url)]
    try:
        resp = opener.open(url)
        if url != resp.geturl():
            return resp.geturl()
        else:
            return url
    except HTTPError as e:
        if e.code == 403:
            if url != e.geturl():
                return e.geturl()
        raise


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    _search(sSearchText)
    setEndOfDirectory()


def _search(sSearchText):
    sHtmlContent = __getHtmlContent(URL_SEARCH % cParser.quotePlus(sSearchText), ignoreErrors=True)
    __displayItems(False, sHtmlContent)
    setEndOfDirectory()
