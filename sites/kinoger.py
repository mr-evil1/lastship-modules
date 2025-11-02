# -*- coding: utf-8 -*-
import json, sys
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
import base64
import binascii
import hashlib
import re,xbmcgui
import json
from resources.lib import pyaes
from itertools import zip_longest as ziplist

SITE_IDENTIFIER = 'kinoger'
SITE_NAME = 'KinoGer'
SITE_ICON = 'kinoger.png'

DOMAIN = getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'kinoger.com')
URL_MAIN = 'https://kinoger.com'
URL_SERIES = URL_MAIN + '/stream/serie/'


def extract_supervideo_url(embed_url):
    try:
        from resources.lib import jsunpacker
        
        logger.info('Supervideo: Starte URL-Extraktion für: %s' % embed_url)
        
        oRequest = cRequestHandler(embed_url, caching=False, ignoreErrors=True)
        oRequest.addHeaderEntry('Referer', 'https://kinoger.com/')
        oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        oRequest.addHeaderEntry('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8')
        oRequest.addHeaderEntry('Accept-Language', 'de,en-US;q=0.7,en;q=0.3')
        
        sHtmlContent = oRequest.request()
        
        if not sHtmlContent or len(sHtmlContent) < 100:
            logger.info('Supervideo: Keine oder unzureichende HTML-Daten empfangen')
            return None
        isMatch, packed = cParser.parseSingleResult(sHtmlContent, r'(eval\s*\(function\(p,a,c,k,e,d\).*?)</script>')
        
        if not isMatch:
            logger.info('Supervideo: Kein gepacktes JavaScript gefunden')
            return None
        
        try:
            unpacked = jsunpacker.unpack(packed)
            logger.info('Supervideo: JavaScript erfolgreich entpackt')
        except Exception as e:
            logger.info('Supervideo: Fehler beim JavaScript-Unpacking: %s' % str(e))
            return None
        patterns = [
            r'file\s*:\s*"([^"]+\.m3u8[^"]*)"',
            r"file\s*:\s*'([^']+\.m3u8[^']*)'",
            r'sources\s*:\s*\[\s*{\s*file\s*:\s*"([^"]+)"',
            r'(https?://[a-zA-Z0-9\-\.]+/[^"\s]+\.m3u8[^\s"]*)',
            r'src\s*:\s*"([^"]+\.m3u8[^"]*)"',
        ]
        
        video_url = None
        for pattern in patterns:
            isMatch, result = cParser.parseSingleResult(unpacked, pattern)
            if isMatch:
                video_url = result.replace('\\', '').strip()
                logger.info('Supervideo: Video-URL gefunden mit Pattern: %s' % pattern)
                break
        
        if not video_url:
            logger.info('Supervideo: Keine Video-URL im entpackten JavaScript gefunden')
            return None
        
        if not video_url.startswith('http'):
            logger.info('Supervideo: URL ist nicht vollständig: %s' % video_url)
            return None
        
        logger.info('Supervideo: Extrahierte Video-URL: %s' % video_url)
        
        headers = '|Referer=https://supervideo.cc/&Origin=https://supervideo.cc&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        return video_url + headers
        
    except Exception as e:
        logger.info('Supervideo: Unerwarteter Fehler bei der URL-Extraktion: %s' % str(e))
        import traceback
        logger.info('Supervideo: Traceback: %s' % traceback.format_exc())
        return None


def load():
    addDirectoryItem("Neu", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MAIN), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Serien", 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Genre", 'runPlugin&site=%s&function=showGenre' % (SITE_NAME), SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()


def showGenre():
    oRequest = cRequestHandler(URL_MAIN)
    oRequest.cacheTime = 60 * 60 * 48
    sHtmlContent = oRequest.request()
    pattern = '<li[^>]class="links"><a href="([^"]+).*?/>([^<]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        return

    for sUrl, sName in aResult:
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MAIN + sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showEntries(entryUrl=False, sSearchText=False, bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=True)
    oRequest.cacheTime = 60 * 60 * 6
    if sSearchText:
        oRequest.addParameters('story', sSearchText)
        oRequest.addParameters('do', 'search')
        oRequest.addParameters('subaction', 'search')
        oRequest.addParameters('x', '0')
        oRequest.addParameters('y', '0')
        oRequest.addParameters('titleonly', '3')
        oRequest.addParameters('submit', 'submit')
    else:
        oRequest.addParameters('dlenewssortby', 'date')
        oRequest.addParameters('dledirection', 'desc')
        oRequest.addParameters('set_new_sort', 'dle_sort_main')
        oRequest.addParameters('set_direction_sort', 'dle_direction_main')
    sHtmlContent = oRequest.request()
    pattern = 'class="title".*?href="([^"]+)">([^<]+).*?src="([^"]+)(.*?)</a> </span>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        return
    items=[]
    total = len(aResult)
    for sUrl, sName, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        item={}
        isTvshow = True if 'staffel' in sName.lower() or 'serie' in entryUrl or ';">S0' in sDummy else False
        isYear, sYear = cParser.parse(sName, '(.*?)\s+\((\d+)\)')
        if isYear:
            for name, year in sYear:
                sName = name
                sYear = year
                break
        isDesc, sDesc = cParser.parseSingleResult(sDummy, '(?:</b></div>|</div></b>|</b>)([^<]+)')
        isDuration, sDuration = cParser.parseSingleResult(sDummy, '(?:Laufzeit|Spielzeit).*?([\d]+)')
        value='showSeasons' if isTvshow else 'getHosters'
        if not isYear:
            sYear=None
        if not isDesc:
            sDesc=''
        if not isDuration:
            sDuration=None
        
        item.setdefault('TVShowTitle',sName)
        item.setdefault('infoTitle', sName)
        item.setdefault('title', sName)
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', isTvshow)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', sDesc)        
        item.setdefault('duration',sDuration)
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sUrl', entryUrl)
        item.setdefault('sFunction',value)
        items.append(item)
    xsDirectory(items, SITE_NAME)

    if not bGlobal:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<a[^>]href="([^"]+)">vorw')
        if isMatchNextPage:
            addDirectoryItem('[B]>>>[/B]',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
    setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    entryUrl = meta.get('entryUrl')
    sThumbnail = meta.get('sThumbnail')
    sTVShowTitle = str(meta.get('TVShowTitle'))
    oRequest = cRequestHandler(entryUrl)
    oRequest.cacheTime = 60 * 60 * 6
    sHtmlContent = oRequest.request()
    items=[]
    L11 = []
    isMatchsst, sstsContainer = cParser.parseSingleResult(sHtmlContent, 'sst.show.*?</script>')
    if isMatchsst:
        sstsContainer = sstsContainer.replace('[', '<').replace(']', '>')
        isMatchsst, L11 = cParser.parse(sstsContainer, "<'([^>]+)")
        if isMatchsst:
            total = len(L11)
    L22 = []
    isMatchollhd, ollhdsContainer = cParser.parseSingleResult(sHtmlContent, 'ollhd.show.*?</script>')
    if isMatchollhd:
        ollhdsContainer = ollhdsContainer.replace('[', '<').replace(']', '>')
        isMatchollhd, L22 = cParser.parse(ollhdsContainer, "<'([^>]+)")
        if isMatchollhd:
            total = len(L22)
    L33 = []
    isMatchpw, pwsContainer = cParser.parseSingleResult(sHtmlContent, 'pw.show.*?</script>')
    if isMatchpw:
        pwsContainer = pwsContainer.replace('[', '<').replace(']', '>')
        isMatchpw, L33 = cParser.parse(pwsContainer, "<'([^>]+)")
        if isMatchpw:
            total = len(L33)

    L44 = []
    isMatchgo, gosContainer = cParser.parseSingleResult(sHtmlContent, 'go.show.*?</script>')
    if isMatchgo:
        gosContainer = gosContainer.replace('[', '<').replace(']', '>')
        isMatchgo, L44 = cParser.parse(gosContainer, "<'([^>]+)")
        if isMatchgo:
            total = len(L44)

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '</b>([^"]+)<br><br>')
    for i in range(0, total):
        item={}
        
        try:
            item.setdefault('L11', L11[i])
        except Exception:
            pass
        try:
            item.setdefault('L22', L22[i])
        except Exception:
            pass
        try:
            item.setdefault('L33', L33[i])
        except Exception:
            pass
        try:
            item.setdefault('L44', L44[i])
        except Exception:
            pass
        i = i + 1
        
        item.setdefault('sTVShowTitle',sTVShowTitle)
        item.setdefault('infoTitle', sTVShowTitle) 
        item.setdefault('title', 'Staffel ' + str(i))
        item.setdefault('entryUrl', entryUrl)
        item.setdefault('isTvshow', True)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', sDesc)        
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sUrl', entryUrl)
        item.setdefault('sSeasonNr',i)
        item.setdefault('sDesc',sDesc)
        item.setdefault('sFunction','showEpisodes')
        
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    sSeasonNr = meta.get('sSeasonNr')
    sThumbnail = meta.get('sThumbnail')
    sTVShowTitle = str(meta.get('TVShowTitle'))
    sDesc = meta.get('sDesc')
    items=[]
    L11 = []
    if meta.get('L11'):
        L11 = meta.get('L11')
        isMatch1, L11 = cParser.parse(L11, "(http[^']+)")
    L22 = []
    if meta.get('L22'):
        L22 = meta.get('L22')
        isMatch, L22 = cParser.parse(L22, "(http[^']+)")
    L33 = []
    if meta.get('L33'):
        L33 = meta.get('L33')
        isMatch3, L33 = cParser.parse(L33, "(http[^']+)")
    L44 = []
    if meta.get('L44'):
        L44 = meta.get('L44')
        isMatch4, L44 = cParser.parse(L44, "(http[^']+)")
    liste = ziplist(L11, L22, L33, L44)
    i = 0
    for sUrl in liste:
        i = i + 1
        item={}
        item.setdefault('TVShowTitle',sTVShowTitle)
        item.setdefault('infoTitle', sTVShowTitle) 
        item.setdefault('title', 'Episode ' + str(i))
        item.setdefault('entryUrl', sUrl)
        item.setdefault('isTvshow', False)
        item.setdefault('poster', sThumbnail)
        item.setdefault('plot', sDesc)        
        item.setdefault('sThumbnail',sThumbnail)
        item.setdefault('sUrl', sUrl)
        item.setdefault('sSeasonNr',sSeasonNr)
        item.setdefault('sEpisode',i)
        item.setdefault('sDesc','')
        item.setdefault('sLinks',sUrl)
        items.append(item)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters():
    params = ParameterHandler()
    meta = json.loads(params.getValue('meta'))
    isResolve = True
    isTvshow=False
    sThumbnail=meta.get('poster')
    isProgressDialog=True
    sUrl = meta.get('sUrl')
    hosters = []
    headers = '&Accept-Language=de%2Cde-DE%3Bq%3D0.9%2Cen%3Bq%3D0.8%2Cen-GB%3Bq%3D0.7%2Cen-US%3Bq%3D0.6&Accept=%2A%2F%2A&User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%3B+rv%3A99.0%29+Gecko%2F20100101+Firefox%2F99.0'
    params = ParameterHandler()
    
    if meta.get('sLinks'):
        for sUrl in meta.get('sLinks'):
            isMatch, aResult = cParser.parse(sUrl, "(http[^']+)")
            if isMatch:
                for sUrl in aResult:
                    try:
                        

                        if 'kinoger.be' in sUrl:
                            oRequest = cRequestHandler(sUrl, caching=False, ignoreErrors=True)
                            oRequest.addHeaderEntry('Referer', 'https://kinoger.com/')
                            sHtmlContent = oRequest.request()
                            isMatch, packed = cParser.parseSingleResult(sHtmlContent, '(eval\s*\(function.*?)</script>')
                            if isMatch:
                                from resources.lib import jsunpacker
                                sHtmlContent = jsunpacker.unpack(packed)
                            isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, 'sources.*?file.*?(http[^"]+)')
                            if isMatch:
                                hUrl = hUrl.replace('\\', '')
                                oRequest = cRequestHandler(hUrl, caching=False, ignoreErrors=True)
                                oRequest.addHeaderEntry('Referer', 'https://kinoger.be/')
                                oRequest.addHeaderEntry('Origin', 'https://kinoger.be')
                                oRequest.removeNewLines(False)
                                sHtmlContent = oRequest.request()
                                if 'CF-DDOS-GUARD aktiv' in sHtmlContent:
                                    continue
                                else:
                                    pattern = 'RESOLUTION=.*?x(\d+).*?\n(index[^\n]+)'
                                    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                            if isMatch:
                                for sQuality, sUrl in aResult:
                                    sUrl = (hUrl.split('video')[0].strip() + sUrl.strip())
                                    sUrl = sUrl + '|Origin=https%3A%2F%2Fkinoger.be&Referer=https%3A%2F%2Fkinoger.be%2F' + headers
                                    hoster = {'link': sUrl, 'name': 'KinoGer.be [I][%sp][/I]' % sQuality, 'quality': sQuality, 'resolveable': True}
                                    hosters.append(hoster)

                        elif 'kinoger.pw' in sUrl:
                            sQuality = '720'
                            hoster = {'link': sUrl + 'DIREKT', 'name': 'Veev.to [I][%sp][/I]'% sQuality, 'quality': sQuality, 'resolveable': True}
                            hosters.append(hoster)

                        elif 'kinoger.re' in sUrl:
                            sQuality = '1080'
                            hoster = {'link': sUrl + 'DIREKT', 'name': 'Kinoger.re [I][%sp][/I]'% sQuality, 'quality': sQuality, 'resolveable': True}
                            hosters.append(hoster)

                        else:
                            sQuality = '720'
                            sName = cParser.urlparse(sUrl)
                            
                            if isBlockedHoster(sName)[0]: 
                                continue
                            
                            if 'supervideo' in sUrl.lower():
                                logger.info('Supervideo-Hoster erkannt: %s' % sUrl)
                                
                                extracted_url = extract_supervideo_url(sUrl)
                                
                                if extracted_url:
                                    logger.info('Supervideo: URL erfolgreich extrahiert und wird als resolvierbarer Stream hinzugefügt')
                                    hoster = {
                                        'link': extracted_url, 
                                        'name': 'Supervideo [I][%sp][/I]' % sQuality, 
                                        'quality': sQuality, 
                                        'resolveable': True
                                    }
                                    hosters.append(hoster)
                                else:
                                    logger.info('Supervideo: URL-Extraktion fehlgeschlagen, versuche Fallback mit resolveUrl')
                                    hoster = {
                                        'link': sUrl, 
                                        'name': 'Supervideo [I][%sp][/I]' % sQuality, 
                                        'displayedName': 'Supervideo [I][%sp][/I]' % sQuality,
                                        'quality': sQuality, 
                                        'resolveable': False
                                    }
                                    hosters.append(hoster)
                            else:
                                hoster = {
                                    'link': sUrl + 'DIREKT', 
                                    'name': sName, 
                                    'displayedName': '%s [I][%sp][/I]' % (sName, sQuality), 
                                    'quality': sQuality, 
                                    'resolveable': True
                                }
                                hosters.append(hoster)

                    except Exception as e:
                        logger.info('Fehler beim Verarbeiten des Hosters: %s' % str(e))
                        pass

    else:
        sUrl = meta.get('entryUrl')
        sHtmlContent = cRequestHandler(sUrl, ignoreErrors=True).request()
        pattern = "show[^>]\d,[^>][^>]'([^']+)"
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for sUrl in aResult:
                try:
                    if 'kinoger.be' in sUrl:
                        oRequest = cRequestHandler(sUrl, caching=False, ignoreErrors=True)
                        oRequest.addHeaderEntry('Referer', 'https://kinoger.com/')
                        sHtmlContent = oRequest.request()
                        isMatch, packed = cParser.parseSingleResult(sHtmlContent, '(eval\s*\(function.*?)</script>')
                        if isMatch:
                            from resources.lib import jsunpacker
                            sHtmlContent = jsunpacker.unpack(packed)
                        isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, 'sources.*?file.*?(http[^"]+)')
                        if isMatch:
                            hUrl = hUrl.replace('\\', '')
                            oRequest = cRequestHandler(hUrl, caching=False, ignoreErrors=True)
                            oRequest.addHeaderEntry('Referer', 'https://kinoger.be/')
                            oRequest.addHeaderEntry('Origin', 'https://kinoger.be')
                            oRequest.removeNewLines(False)
                            sHtmlContent = oRequest.request()
                            if 'CF-DDOS-GUARD aktiv' in sHtmlContent:
                                continue
                            else:
                                pattern = 'RESOLUTION=.*?x(\d+).*?\n(index[^\n]+)'
                                isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                        if isMatch:
                            for sQuality, sUrl in aResult:
                                sUrl = (hUrl.split('video')[0].strip() + sUrl.strip())
                                sUrl = sUrl + '|Origin=https%3A%2F%2Fkinoger.be&Referer=https%3A%2F%2Fkinoger.be%2F' + headers
                                hoster = {'link': sUrl, 'name': 'KinoGer.be [I][%sp][/I]' % sQuality, 'quality': sQuality, 'resolveable': True}
                                hosters.append(hoster)

                    elif 'kinoger.pw' in sUrl:
                        sQuality = '720'
                        hoster = {'link': sUrl + 'DIREKT', 'name': 'Veev.to [I][%sp][/I]'% sQuality, 'quality': sQuality, 'resolveable': True}
                        hosters.append(hoster)

                    elif 'kinoger.re' in sUrl:
                        sQuality = '1080'
                        hoster = {'link': sUrl + 'DIREKT', 'name': 'Kinoger.re [I][%sp][/I]'% sQuality, 'quality': sQuality, 'resolveable': True}
                        hosters.append(hoster)

                    else:
                        sQuality = '720'
                        sName = cParser.urlparse(sUrl)
                        
                        if 'supervideo' in sUrl.lower():
                            logger.info('Supervideo-Hoster erkannt: %s' % sUrl)
                            
                            extracted_url = extract_supervideo_url(sUrl)
                            
                            if extracted_url:
                                logger.info('Supervideo: URL erfolgreich extrahiert')
                                hoster = {
                                    'link': extracted_url, 
                                    'name': 'Supervideo [I][%sp][/I]' % sQuality, 
                                    'quality': sQuality, 
                                    'resolveable': True
                                }
                                hosters.append(hoster)
                            else:
                                logger.info('Supervideo: URL-Extraktion fehlgeschlagen, verwende Fallback')
                                hoster = {
                                    'link': sUrl, 
                                    'name': 'Supervideo [I][%sp][/I]' % sQuality, 
                                    'displayedName': 'Supervideo [I][%sp][/I]' % sQuality,
                                    'quality': sQuality, 
                                    'resolveable': False
                                }
                                hosters.append(hoster)
                        else:
                            hoster = {
                                'link': sUrl + 'DIREKT', 
                                'name': sName, 
                                'displayedName': '%s [I][%sp][/I]' % (sName, sQuality), 
                                'quality': sQuality, 
                                'resolveable': True
                            }
                            hosters.append(hoster)

                except Exception as e:
                    logger.info('Fehler beim Verarbeiten des Hosters: %s' % str(e))
                    pass

    if not isMatch:
        return

    if hosters:
        items=[]
        for shoster in hosters:
            item={}
            infoTitle=shoster['name']
            hurl=getHosterUrl(shoster['link'])
            streamUrl=hurl[0]['streamUrl']
            isResolve=hurl[0]['resolved']
            sUrl=shoster['link']
            
            if isProgressDialog: progressDialog.create('xStream V2', 'Erstelle Hosterliste ...')
            t = 0
            if isProgressDialog: progressDialog.update(t)
            
            sHoster=cParser.urlparse(streamUrl)
            t += 100 / len(hosters)
            if isProgressDialog: progressDialog.update(int(t), '[CR]Überprüfe Stream von ' + sHoster)
            if 'ayer' in sHoster: continue
            
            if 'outube' in sHoster:
                sHoster=sHoster.split('.')[0]+' Trailer'
            
            items.append((infoTitle, infoTitle, meta, isResolve, streamUrl, sThumbnail))
        if isProgressDialog:  progressDialog.close()
    
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)


def getHosterUrl(sUrl=False):
    if sUrl.endswith('DIREKT'):
        sUrl1 = sUrl[:-6]
        Request = cRequestHandler(sUrl1, caching=False)
        Request.request()
        sUrl2 = Request.getRealUrl()
        if sUrl2:
            return [{'streamUrl': sUrl2, 'resolved': False}]
        else:
            return [{'streamUrl': sUrl1, 'resolved': True}]
    else:
        return [{'streamUrl': sUrl, 'resolved': True}]


def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    showEntries(URL_MAIN, sSearchText, bGlobal=False)


def _search(sSearchText):
    showEntries(URL_MAIN, sSearchText, bGlobal=True)


def content_decryptor(html_content,passphrase):
    match = re.compile(r'''JScripts = '(.+?)';''', re.DOTALL).search(html_content)
    if match:
        json_obj = json.loads(match.group(1))
        salt = binascii.unhexlify(json_obj["s"])
        iv = binascii.unhexlify(json_obj["iv"])
        ct = base64.b64decode(json_obj["ct"])
        concated_passphrase = passphrase.encode() + salt
        md5 = [hashlib.md5(concated_passphrase).digest()]
        result = md5[0]
        i = 1
        while len(result) < 32:
            md5.append(hashlib.md5(md5[i - 1] + concated_passphrase).digest())
            result += md5[i]
            i += 1
        key = result[:32]
        aes = pyaes.AESModeOfOperationCBC(key, iv)
        decrypter = pyaes.Decrypter(aes)
        plain_text = decrypter.feed(ct)
        plain_text += decrypter.feed()
        return json.loads(plain_text.decode())
    else:
        return None
