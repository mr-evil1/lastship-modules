# -*- coding: utf-8 -*-
import json, sys, re
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute, getSetting, setSetting
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib import log_utils
import json
oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()
import xbmcgui
try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

SITE_IDENTIFIER = 'internetarchive'
SITE_NAME = 'Internet Archive'
SITE_ICON = 'internetarchive.png'

DOMAIN = getSetting('provider.' + SITE_IDENTIFIER + '.domain', 'archive.org')
URL_MAIN = 'https://' + DOMAIN
URL_MOVIE = URL_MAIN + '/details/'
URL_SEARCH = URL_MAIN + '/advancedsearch.php?q=%s&fl[]=description&fl[]=identifier&fl[]=language&fl[]=title&fl[]=year&rows=50&page=1&output=json'
URL_SEARCH_MOVIES = URL_MAIN + '/advancedsearch.php?q=%s%%20AND%%20mediatype:movies&fl[]=description&fl[]=identifier&fl[]=language&fl[]=title&fl[]=year&rows=50&page=1&output=json'
URL_COLL = URL_MAIN + '/advancedsearch.php?q=collection:%22'
URL_COLL1 = '%22&fl%5B%5D=collection&fl%5B%5D=description&fl%5B%5D=genre&fl%5B%5D=identifier&fl%5B%5D=language&fl%5B%5D=title&fl%5B%5D=year&rows=80000&page=1&output=json'


URL_COLLECTIONS_LIST = {
    'Film Noir': 'Film_Noir',
    'Feature Films': 'feature_films',
    'Movie Trailers': 'movie_trailers',
    'Short Films': 'short_films',
    'SciFi Horror': 'scifi_horror',
    'Cinemocracy': 'cinemocracy',
    'Classic Cinema': 'classic_cinema',
    'Silent Films': 'silent_films',
    'Comedy Films': 'Comedy_Films',
    'Color Films': 'colorized-movies'
}


def load():
    """Menu structure of the site plugin"""
    log_utils.log('Load %s' % SITE_NAME)
    addDirectoryItem("Collectionen", 'runPlugin&site=%s&function=showMovieBrowse' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Filme durchsuchen", 'runPlugin&site=%s&function=menuCollections' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def menuCollections():
    """Zeige verfügbare Collectionen"""
    log_utils.log('menuCollections - Start')
    
    for key in sorted(URL_COLLECTIONS_LIST):
        archive_url = URL_COLL + str(URL_COLLECTIONS_LIST[key] )+ URL_COLL1
        encoded_archive_url = quote(archive_url, safe='') 
        addDirectoryItem(key, 'runPlugin&site=%s&function=showCollections&sUrl=%s' % (SITE_NAME, encoded_archive_url), SITE_ICON, 'DefaultMovies.png')
        
        log_utils.log('menuCollections - Adding: %s -> %s' % (key, encoded_archive_url))

    setEndOfDirectory()



def showMovieBrowse():
    log_utils.log('showMovieBrowse - Start')
    addDirectoryItem("Alle Feature Films", 'runPlugin&site=%s&function=showCollections&sUrl=%s' % (SITE_NAME, quote(URL_COLL + 'feature_films' + URL_COLL1, safe='')), SITE_ICON, 'DefaultMovies.png')

    addDirectoryItem("Film Collectief", 'runPlugin&site=%s&function=showCollections&sUrl=%s' % (SITE_NAME, quote(URL_COLL + 'collectie_filmcollectief' + URL_COLL1,safe='')), SITE_ICON, 'DefaultMovies.png')
    
    addDirectoryItem("Pic Fixer Films", 'runPlugin&site=%s&function=showCollections&sUrl=%s' % (SITE_NAME, quote(URL_COLL + 'feature_films_picfixer' + URL_COLL1,safe='')), SITE_ICON, 'DefaultMovies.png')
    
    
    addDirectoryItem("Hall of Fame", 'runPlugin&site=%s&function=showCollections&sUrl=%s' % (SITE_NAME, quote(URL_COLL + 'silenthalloffame' + URL_COLL1,safe='')), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory() 



def showCollections(entryUrl=False, sSearchText=False, bGlobal=False):
    """Zeige Einträge einer Collection"""
    log_utils.log('showCollections - Start')
    
    params = ParameterHandler()
    if not entryUrl: 
        entryUrl = params.getValue('sUrl')
    
    log_utils.log('showCollections - URL: %s' % entryUrl)
    
    try:
        
        oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
        oRequest.cacheTime = 60 * 60 * 6
        sContent = oRequest.request()
        
        if not sContent:
            log_utils.log('showCollections - ERROR: Keine Antwort erhalten')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        log_utils.log('showCollections - Response Length: %d' % len(sContent))
        log_utils.log('showCollections - Parsing JSON...')
        
        jSearch = json.loads(sContent)
        
        if 'response' not in jSearch:
            log_utils.log('showCollections - ERROR: Keine response in JSON')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        if 'docs' not in jSearch['response']:
            log_utils.log('showCollections - ERROR: Keine docs in response')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        aResults = jSearch['response']['docs']
        total = len(aResults)
        
        log_utils.log('showCollections - Found %d results' % total)
        
        if total == 0:
            log_utils.log('showCollections - No results found')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        items = []
        

        sLanguage = getSetting('prefLanguage', '0')
        log_utils.log('showCollections - Language Filter: %s' % sLanguage)
        
        for idx, i in enumerate(aResults):
            try:
                log_utils.log('showCollections - Processing item %d/%d' % (idx + 1, total))
                
                if 'identifier' not in i or 'title' not in i:
                    log_utils.log('showCollections - Item %d: Missing identifier or title' % (idx + 1))
                    continue
                
                sId = i['identifier']
                sName = i['title']
                
                log_utils.log('showCollections - Item %d: %s (ID: %s)' % (idx + 1, sName, sId))
                
                if sSearchText and not cParser.search(sSearchText, sName):
                    log_utils.log('showCollections - Item %d: Filtered by search text' % (idx + 1))
                    continue
                

                if 'language' in i and i['language']:
                    sLang = str(i['language']).lower()
                    log_utils.log('showCollections - Item %d: Language: %s' % (idx + 1, sLang))
                    
                    if sLanguage == '1':  # Deutsch
                        if not any(x in sLang for x in ['ger', 'deu', 'de']):
                            log_utils.log('showCollections - Item %d: Filtered by language (not German)' % (idx + 1))
                            continue
                    elif sLanguage == '2':  # Englisch
                        if not any(x in sLang for x in ['eng', 'en']):
                            log_utils.log('showCollections - Item %d: Filtered by language (not English)' % (idx + 1))
                            continue
                
                item = {}
                
                if bGlobal:
                    sName = SITE_NAME + ' - ' + sName
                
                item['infoTitle'] = sName
                item['title'] = sName
                item['entryUrl'] = URL_MOVIE + sId
                item['isTvshow'] = False
                item['poster'] = ''
                item['sFunction'] = 'getHosters'
                
                # Jahr
                if 'year' in i and i['year']:
                    try:
                        year = str(i['year'])
                        if len(year) == 4:
                            item['year'] = year
                            log_utils.log('showCollections - Item %d: Year: %s' % (idx + 1, year))
                    except:
                        pass
                
                # Beschreibung
                if 'description' in i and i['description']:
                    try:
                        desc = i['description']
                        if isinstance(desc, list):
                            desc = ' '.join(desc)
                        item['plot'] = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]{2}'.format(SITE_NAME, sName, desc[:500])
                    except:
                        item['plot'] = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
                else:
                    item['plot'] = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
                
                items.append(item)
                log_utils.log('showCollections - Item %d: Added to items list' % (idx + 1))
                
            except Exception as e:
                log_utils.log('showCollections - ERROR processing item %d: %s' % (idx + 1, str(e)))
                continue
        
        log_utils.log('showCollections - Total items to display: %d' % len(items))
        
        if items:
            log_utils.log('showCollections - Calling xsDirectory with %d items' % len(items))
            xsDirectory(items, SITE_NAME)
        else:
            log_utils.log('showCollections - No items to display')
        
        if not bGlobal:
            setEndOfDirectory()
        
        log_utils.log('showCollections - End')
        
    except Exception as e:
        log_utils.log('showCollections - FATAL ERROR: %s' % str(e))
        if not bGlobal:
            setEndOfDirectory()


def showEntries(entryUrl=False, sSearchText=False, bGlobal=False):
    """Zeige Einträge (Filme/Serien)"""
    log_utils.log('showEntries - Start')
    
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    
    log_utils.log('showEntries - URL: %s' % entryUrl)
    
    try:
        log_utils.log('showEntries - Requesting URL...')
        oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
        oRequest.cacheTime = 60 * 60 * 6
        sContent = oRequest.request()
        
        if not sContent:
            log_utils.log('showEntries - ERROR: Keine Antwort')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        log_utils.log('showEntries - Response Length: %d' % len(sContent))
        jSearch = json.loads(sContent)
        
        if 'response' not in jSearch or 'docs' not in jSearch['response']:
            log_utils.log('showEntries - ERROR: Invalid JSON structure')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        aResults = jSearch['response']['docs']
        total = len(aResults)
        
        log_utils.log('showEntries - Found %d results' % total)
        
        if total == 0:
            log_utils.log('showEntries - No results')
            if not bGlobal:
                setEndOfDirectory()
            return
        
        items = []
        
        for idx, i in enumerate(aResults):
            try:
                if 'identifier' not in i or 'title' not in i:
                    continue
                
                sId = i['identifier']
                sName = i['title']
                
                log_utils.log('showEntries - Item %d/%d: %s' % (idx + 1, total, sName))
                
                if sSearchText and not cParser.search(sSearchText, sName):
                    continue
                
                item = {}
                
                if bGlobal:
                    sName = SITE_NAME + ' - ' + sName
                
                item['infoTitle'] = sName
                item['title'] = sName
                item['entryUrl'] = URL_MOVIE + sId
                item['isTvshow'] = False
                item['poster'] = ''
                item['sFunction'] = 'getHosters'
                
                if 'year' in i and i['year']:
                    try:
                        year = str(i['year'])
                        if len(year) == 4:
                            item['year'] = year
                    except:
                        pass
                
                if 'description' in i and i['description']:
                    try:
                        desc = i['description']
                        if isinstance(desc, list):
                            desc = ' '.join(desc)
                        item['plot'] = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]{2}'.format(SITE_NAME, sName, desc[:500])
                    except:
                        item['plot'] = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
                else:
                    item['plot'] = '[B][COLOR blue]{0}[/B][CR]{1}[/COLOR][CR]'.format(SITE_NAME, sName)
                
                items.append(item)
                
            except Exception as e:
                log_utils.log('showEntries - ERROR processing item %d: %s' % (idx + 1, str(e)))
                continue
        
        log_utils.log('showEntries - Total items: %d' % len(items))
        
        if items:
            xsDirectory(items, SITE_NAME)
        
        if not bGlobal:
            setEndOfDirectory()
        
        log_utils.log('showEntries - End')
        
    except Exception as e:
        log_utils.log('showEntries - FATAL ERROR: %s' % str(e))
        if not bGlobal:
            setEndOfDirectory()


def getHosters():
    """Extrahiere Video-Links von der Detail-Seite"""
    log_utils.log('getHosters - Start')
    
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sUrl = meta.get('entryUrl', params.getValue('entryUrl'))
    
    log_utils.log('getHosters - URL: %s' % sUrl)
    
    items = []
    isProgressDialog = True
    isResolve = False
    
    try:
        if sUrl.startswith('//'):
            sUrl = 'https:' + sUrl
            log_utils.log('getHosters - Fixed URL: %s' % sUrl)
        
        log_utils.log('getHosters - Requesting page...')
        sHtmlContent = cRequestHandler(sUrl).request()
        
        if not sHtmlContent:
            log_utils.log('getHosters - ERROR: No HTML response')
            url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
            execute('Container.Update(%s)' % url)
            return
        
        log_utils.log('getHosters - HTML Length: %d' % len(sHtmlContent))
        

        log_utils.log('getHosters - Trying pattern 1 (embedUrl)...')
        pattern1 = 'itemprop="embedUrl".*?href="([^"]+)"'
        isMatch1, aResult1 = cParser.parse(sHtmlContent, pattern1)
        log_utils.log('getHosters - Pattern 1 found %d matches' % (len(aResult1) if isMatch1 else 0))
        

        log_utils.log('getHosters - Trying pattern 2 (direct video links)...')
        pattern2 = 'href="([^"]*\.(?:mp4|mkv|avi|ogv)[^"]*)"'
        isMatch2, aResult2 = cParser.parse(sHtmlContent, pattern2)
        log_utils.log('getHosters - Pattern 2 found %d matches' % (len(aResult2) if isMatch2 else 0))
        
        
        log_utils.log('getHosters - Trying pattern 3 (format-source)...')
        pattern3 = '"format":\s*"([^"]*(?:MPEG4|h\.264|Ogg Video)[^"]*)"[^}]*"source":\s*"([^"]+)"'
        isMatch3, aResult3 = cParser.parse(sHtmlContent, pattern3)
        log_utils.log('getHosters - Pattern 3 found %d matches' % (len(aResult3) if isMatch3 else 0))
        

        allLinks = []
        
        if isMatch1:
            for link in aResult1:
                allLinks.append(link)
                log_utils.log('getHosters - Added from pattern 1: %s' % link)
        
        if isMatch2:
            for link in aResult2:
                if link.startswith('/'):
                    link = URL_MAIN + link
                allLinks.append(link)
                log_utils.log('getHosters - Added from pattern 2: %s' % link)
        
        if isMatch3:
            for fmt, link in aResult3:
                if link.startswith('/'):
                    link = URL_MAIN + link
                allLinks.append(link)
                log_utils.log('getHosters - Added from pattern 3: %s (format: %s)' % (link, fmt))
        
        log_utils.log('getHosters - Total links found: %d' % len(allLinks))
        
        if not allLinks:
            log_utils.log('getHosters - ERROR: No links found')
            url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
            execute('Container.Update(%s)' % url)
            return
        
        sThumbnail = meta.get('poster', '')
        sTitle = meta.get('infoTitle', '')
        
        if meta.get('isTvshow', False):
            meta.setdefault('mediatype', 'tvshow')
        else:
            meta.setdefault('mediatype', 'movie')
        
        if isProgressDialog:
            progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
        
        t = 0
        processed_links = set()
        
        for idx, sUrl in enumerate(allLinks):
            try:
                log_utils.log('getHosters - Processing link %d/%d' % (idx + 1, len(allLinks)))
                

                if sUrl in processed_links:
                    log_utils.log('getHosters - Link %d: Duplicate, skipping' % (idx + 1))
                    continue
                processed_links.add(sUrl)
                
                if sUrl.startswith('//'):
                    sUrl = 'https:' + sUrl
                elif sUrl.startswith('/'):
                    sUrl = URL_MAIN + sUrl
                
            
                quality = 'SD'
                if '1080' in sUrl or '1920' in sUrl:
                    quality = '1080p'
                elif '720' in sUrl or '1280' in sUrl:
                    quality = '720p'
                elif '480' in sUrl:
                    quality = '480p'
                
                log_utils.log('getHosters - Link %d: Quality: %s' % (idx + 1, quality))
                
                sHoster = 'Archive.org [%s]' % quality
                
                if isProgressDialog:
                    progressDialog.update(int(t), '[CR]Stream gefunden: ' + quality)
                
                items.append((sHoster, sTitle, meta, isResolve, sUrl, sThumbnail))
                log_utils.log('getHosters - Link %d: Added to items' % (idx + 1))
                
                t += 100 / len(allLinks) if len(allLinks) > 0 else 100
                
            except Exception as e:
                log_utils.log('getHosters - ERROR processing link %d: %s' % (idx + 1, str(e)))
                continue
        
        if isProgressDialog:
            progressDialog.close()
        
        log_utils.log('getHosters - Total streams: %d' % len(items))
        
    except Exception as e:
        log_utils.log('getHosters - FATAL ERROR: %s' % str(e))
        if isProgressDialog:
            try:
                progressDialog.close()
            except:
                pass
    
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)
    log_utils.log('getHosters - End')


def showSearch():
    """Zeige Suchfeld"""
    log_utils.log('showSearch - Start')
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        log_utils.log('showSearch - No search text entered')
        return
    log_utils.log('showSearch - Search text: %s' % sSearchText)
    showEntries(URL_SEARCH_MOVIES % quote_plus(sSearchText), sSearchText, bGlobal=False)


def _search(sSearchText):
    """Globale Suche"""
    log_utils.log('_search - Search text: %s' % sSearchText)
    showEntries(URL_SEARCH_MOVIES % quote_plus(sSearchText), sSearchText, bGlobal=True)
