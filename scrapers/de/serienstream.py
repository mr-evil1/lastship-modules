# -*- coding: utf-8 -*-
import re
import sys

try:
    from resources.lib.control import getSetting, urljoin, setSetting
except:
    pass

try:
    from resources.lib.requestHandler import cRequestHandler
except:
    cRequestHandler = None

try:
    from scrapers.modules import cleantitle, dom_parser
except:
    pass

try:
    from resources.lib.utils import isBlockedHoster
except:
    isBlockedHoster = None

try:
    from resources.lib import log_utils
except:
    log_utils = None


SITE_IDENTIFIER = 'serienstream'
SITE_DOMAIN = 's.to'
SITE_NAME = 'SerienStream'


class source:
    def __init__(self):
        self.priority = 2
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = '/serien'
        self.sources = []
        
        if log_utils:
            log_utils.log('SerienStream - Initialized with domain: %s' % self.domain, log_utils.LOGDEBUG)

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        aLinks = []
        
        if season == 0:
            if log_utils:
                log_utils.log('SerienStream - Skipping - season is 0', log_utils.LOGDEBUG)
            return self.sources
        
        try:
            t = [cleantitle.get(i) for i in titles if i]
            if log_utils:
                log_utils.log('SerienStream - Searching for titles: %s (S%02dE%02d)' % (titles, season, episode), log_utils.LOGDEBUG)
            
            url = urljoin(self.base_link, self.search_link)
            
            if cRequestHandler:
                oRequest = cRequestHandler(url)
                oRequest.cacheTime = 60*60*24*7
                sHtmlContent = oRequest.request()
            else:
                import requests
                requests.packages.urllib3.disable_warnings()
                r = requests.get(url, timeout=15, verify=False)
                sHtmlContent = r.text
            
            links = dom_parser.parse_dom(sHtmlContent, "div", attrs={"class": "genre"})
            links = dom_parser.parse_dom(links, "a")
            links = [(i.attrs["href"], i.content) for i in links]
            
            if log_utils:
                log_utils.log('SerienStream - Found %d series in list' % len(links), log_utils.LOGDEBUG)
            for i in links:
                for a in t:
                    try:
                        if any([a in cleantitle.get(i[1])]):
                            aLinks.append({'source': i[0]})
                            if log_utils:
                                log_utils.log('SerienStream - Matched series: %s' % i[1], log_utils.LOGDEBUG)
                            break
                    except:
                        pass
            
            if len(aLinks) == 0:
                if log_utils:
                    log_utils.log('SerienStream - No matching series found', log_utils.LOGWARNING)
                return self.sources
            
            for i in aLinks:
                url = i['source']
                self.run2(url, year, season=season, episode=episode, hostDict=hostDict, imdb=imdb)
        
        except Exception as e:
            if log_utils:
                log_utils.log('SerienStream - ERROR in run: %s' % str(e), log_utils.LOGERROR)
                import traceback
                log_utils.log('SerienStream - %s' % traceback.format_exc(), log_utils.LOGERROR)
            return self.sources
        
        return self.sources

    def run2(self, url, year, season=0, episode=0, hostDict=None, imdb=None):

        try:
            url = url[:-1] if url.endswith('/') else url
            if "staffel" in url:
                url = re.findall("(.*?)staffel", url)[0]
            url += '/staffel-%d/episode-%d' % (int(season), int(episode))
            url = urljoin(self.base_link, url)
            
            if log_utils:
                log_utils.log('SerienStream - Episode URL: %s' % url, log_utils.LOGDEBUG)
            
            if cRequestHandler:
                sHtmlContent = cRequestHandler(url).request()
            else:
                import requests
                requests.packages.urllib3.disable_warnings()
                r = requests.get(url, timeout=15, verify=False)
                sHtmlContent = r.text
            
            a = dom_parser.parse_dom(sHtmlContent, 'a', attrs={'class': 'imdb-link'}, req='href')
            if a and imdb:
                foundImdb = a[0].attrs.get("data-imdb", '')
                if foundImdb and not foundImdb == imdb:
                    if log_utils:
                        log_utils.log('SerienStream - IMDB mismatch: %s != %s' % (foundImdb, imdb), log_utils.LOGWARNING)
                    return
            
            lr = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'class': 'hosterSiteVideo'})
            
            r = dom_parser.parse_dom(lr, 'li', attrs={'data-lang-key': re.compile('[1]')})
            
            if not r:
                r = dom_parser.parse_dom(lr, 'li', attrs={'data-lang-key': re.compile('[1|2|3]')})
            
            if not r:
                if log_utils:
                    log_utils.log('SerienStream - No hosters found', log_utils.LOGWARNING)
                return self.sources
            
            r = [(i.attrs['data-link-target'], 
                  dom_parser.parse_dom(i, 'h4'),
                  'subbed' if i.attrs.get('data-lang-key') == '3' else '' if i.attrs.get('data-lang-key') == '1' else 'English/OV') 
                 for i in r]
            
            r = [(i[0], 
                  re.sub('\s(.*)', '', i[1][0].content) if i[1] else 'Unknown',
                  'HD' if i[1] and 'hd' in i[1][0].content.lower() else 'SD',
                  i[2]) 
                 for i in r if i[1]]
            
            if log_utils:
                log_utils.log('SerienStream - Found %d hosters' % len(r), log_utils.LOGDEBUG)
            
            login, password = self._getLogin()
            if not login or not password:
                if log_utils:
                    log_utils.log('SerienStream - No login credentials', log_utils.LOGERROR)
                return self.sources
            
            import requests
            requests.packages.urllib3.disable_warnings()
            s = requests.Session()
            
            URL_LOGIN = self.base_link + '/login'
            payload = {'email': login, 'password': password}
            
            try:
                res = s.get(URL_LOGIN, verify=False, timeout=10)
                s.post(URL_LOGIN, data=payload, cookies=res.cookies, verify=False, timeout=10)
                if log_utils:
                    log_utils.log('SerienStream - Login successful', log_utils.LOGDEBUG)
            except Exception as e:
                if log_utils:
                    log_utils.log('SerienStream - Login failed: %s' % str(e), log_utils.LOGERROR)
                return self.sources
            
            for link_target, host, quality, info in r:
                try:
                    redirect_url = self.base_link + link_target
                    sUrl = s.get(redirect_url, verify=False, timeout=10).url
                    
                    if log_utils:
                        log_utils.log('SerienStream - Source: %s | %s | %s' % (host, quality, sUrl), log_utils.LOGDEBUG)
                    if isBlockedHoster:
                        isBlocked, hoster, resolved_url, prioHoster = isBlockedHoster(sUrl, isResolve=True)
                        if isBlocked:
                            continue
                    else:
                        resolved_url = sUrl
                        prioHoster = 0
                    
                    self.sources.append({
                        'source': host,
                        'quality': quality,
                        'language': 'de',
                        'url': resolved_url,
                        'info': info,
                        'direct': False,
                        'debridonly': False,
                        'priority': self.priority,
                        'prioHoster': prioHoster
                    })
                    
                except Exception as e:
                    if log_utils:
                        log_utils.log('SerienStream - Redirect failed for %s: %s' % (host, str(e)), log_utils.LOGERROR)
                    continue
            
            if log_utils:
                log_utils.log('SerienStream - Returning %d sources' % len(self.sources), log_utils.LOGDEBUG)
            return self.sources
            
        except Exception as e:
            if log_utils:
                log_utils.log('SerienStream - ERROR in run2: %s' % str(e), log_utils.LOGERROR)
                import traceback
                log_utils.log('SerienStream - %s' % traceback.format_exc(), log_utils.LOGERROR)
            return self.sources
    
    def resolve(self, url):
        return url
    
    @staticmethod
    def _getLogin():
        login = ''
        password = ''
        
        try:
            from scrapers.modules.jsnprotect import cHelper
            login = cHelper.UserName
            password = cHelper.PassWord
            setSetting('serienstream.user', login)
            setSetting('serienstream.pass', password)
        except:
            login = getSetting(SITE_IDENTIFIER + '.user')
            password = getSetting(SITE_IDENTIFIER + '.pass')
        
        if not login or not password:
            try:
                import xbmcgui, xbmcaddon
                AddonName = xbmcaddon.Addon().getAddonInfo('name')
                xbmcgui.Dialog().ok(AddonName,
                                    "In den Einstellungen die Kontodaten (Login) für %s eintragen / überprüfen\nBis dahin wird %s von der Suche ausgeschlossen." % (
                                    SITE_NAME, SITE_NAME))
                setSetting('provider.' + SITE_IDENTIFIER, 'false')
            except:
                pass
            return '', ''
        
        return login, password
