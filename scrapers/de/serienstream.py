# -*- coding: utf-8 -*-
import re
import sys
from resources.lib.control import getSetting, urljoin, setSetting
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser
from resources.lib.utils import isBlockedHoster
from resources.lib.tools import logger, cParser


SITE_IDENTIFIER = 'serienstream'
SITE_DOMAIN = 's.to'
SITE_NAME = 'SerienStream'
log_utils=True

class source:
    def __init__(self):
        self.priority = 4
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        
        if getSetting('bypassDNSlock') != 'true':
            self.base_link = 'https://' + self.domain
        else:
            self.base_link ='http://186.2.175.5'
        self.search_link = '/suche?term='
        
        self.sources = []
        self.logged_in = False
        self.credentials_checked = False
        
        if log_utils:
            logger.info('SerienStream - Init: %s' % self.base_link)

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        if season == 0:
            return self.sources
        
        try:
            t = [cleantitle.get(i) for i in titles if i]
            
            if log_utils:
                logger.info('SerienStream - Search: S%02dE%02d' % (season, episode))
            
            login, password = self._getLogin()
            
            if not login or not password:
                if log_utils:
                    logger.info('SerienStream - No credentials, skipping scraper')
                
                if not self.credentials_checked:
                    self.credentials_checked = True
                    try:
                        import xbmcgui
                        xbmcgui.Dialog().ok(
                            'SerienStream',
                            'Keine Login-Daten in den Einstellungen eingetragen.\n\nBitte Email und Passwort für SerienStream eintragen.\nBis dahin wird SerienStream übersprungen.'
                        )
                    except Exception as e:
                        if log_utils:
                            logger.info('SerienStream - Dialog error: %s' % str(e))
                
                return self.sources
            
            if log_utils:
                logger.info('SerienStream - Credentials found, attempting login')
            
            login_success = self._do_login(login, password)
            if not login_success:
                if log_utils:
                    logger.info('SerienStream - Login failed, but continuing anyway')
            
            aLinks = []
            for title in titles:
                if not title:
                    continue
                
                try:
                    try:
                        from urllib import quote
                    except:
                        from urllib.parse import quote
                    
                    if isinstance(title, str):
                        try:
                            search_term = quote(title)
                        except:
                            search_term = quote(title.encode('utf-8'))
                    else:
                        search_term = quote(title)
                    
                    search_url = urljoin(self.base_link, self.search_link + search_term)
                    
                    if log_utils:
                        logger.info('SerienStream - Search URL: %s' % search_url)
                    
                    oRequest = cRequestHandler(search_url)
                    oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0')
                    sHtmlContent = oRequest.request()
                    
                    links = self._parse_search_results(sHtmlContent)
                    
                    if links:
                        if log_utils:
                            logger.info('SerienStream - Found %d results' % len(links))
                        
                        for href, series_title in links:
                            for clean_title in t:
                                try:
                                    if clean_title in cleantitle.get(series_title):
                                        aLinks.append({'source': href})
                                        if log_utils:
                                            logger.info('SerienStream - Match: %s' % href)
                                        break
                                except:
                                    pass
                            if aLinks:
                                break
                    
                    if aLinks:
                        break
                        
                except Exception as e:
                    if log_utils:
                        logger.info('SerienStream - Search error: %s' % str(e))
                    continue
            
            if len(aLinks) == 0:
                return self.sources
            
            for i in aLinks:
                url = i['source']
                self.run2(url, year, season=season, episode=episode, hostDict=hostDict, imdb=imdb)
        
        except Exception as e:
            if log_utils:
                logger.info('SerienStream - Error: %s' % str(e))
            return self.sources
        
        return self.sources

    def _do_login(self, login, password):
        try:
            if log_utils:
                logger.info('SerienStream - Performing login...')
            
            URL_LOGIN = self.base_link + '/login'
            
            oRequest = cRequestHandler(URL_LOGIN)
            oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0')
            login_page = oRequest.request()
            
            form_fields = {}
            input_pattern = r'<input[^>]*name=["\']([^"\']+)["\'][^>]*(?:value=["\']([^"\']*)["\'])?[^>]*>'
            for match in re.finditer(input_pattern, login_page, re.IGNORECASE):
                name = match.group(1)
                value = match.group(2) if match.group(2) else ''
                if name.lower() not in ['email', 'password']:
                    form_fields[name] = value
            
            oRequest = cRequestHandler(URL_LOGIN)
            oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0')
            oRequest.addHeaderEntry('Content-Type', 'application/x-www-form-urlencoded')
            oRequest.addHeaderEntry('Referer', URL_LOGIN)
            oRequest.addHeaderEntry('Origin', self.base_link)
            
            for field_name, field_value in form_fields.items():
                oRequest.addParameters(field_name, field_value)
            
            oRequest.addParameters('email', login)
            oRequest.addParameters('password', password)
            
            login_response = oRequest.request()
            
            if len(login_response) != len(login_page):
                if log_utils:
                    logger.info('SerienStream - Login successful')
                self.logged_in = True
                return True
            elif 'logout' in login_response.lower() or 'abmelden' in login_response.lower():
                if log_utils:
                    logger.info('SerienStream - Login successful')
                self.logged_in = True
                return True
            else:
                self.logged_in = False
                return False
                
        except Exception as e:
            if log_utils:
                logger.info('SerienStream - Login error: %s' % str(e))
            self.logged_in = False
            return False

    def _parse_search_results(self, html):
        links = []
        
        try:
            patterns = [
                r'href="https?://[^/]+(/serie/[^"]+)"',
                r'href="(/serie/[^"]+)"',
            ]
            
            all_serie_hrefs = []
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                all_serie_hrefs.extend(matches)
            
            all_serie_hrefs = list(set(all_serie_hrefs))
            
            for href in all_serie_hrefs:
                try:
                    title_pattern = r'href="[^"]*' + re.escape(href) + r'"[^>]*title="([^"]+)"'
                    title_match = re.search(title_pattern, html, re.IGNORECASE)
                    
                    if title_match:
                        title = title_match.group(1)
                    else:
                        title = href.split('/')[-1].replace('-', ' ').title()
                    
                    if title:
                        title = re.sub(r'<[^>]+>', '', title).strip()
                        links.append((href, title))
                        
                except:
                    pass
                
        except Exception as e:
            if log_utils:
                logger.info('SerienStream - Parse error: %s' % str(e))
        
        return links

    def run2(self, url, year, season=0, episode=0, hostDict=None, imdb=None):
        try:
            url = url[:-1] if url.endswith('/') else url
            if "staffel" in url:
                url = re.findall("(.*?)staffel", url)[0]
            
            episode_url = '%s/staffel-%d/episode-%d' % (url, int(season), int(episode))
            full_url = urljoin(self.base_link, episode_url)
            
            if log_utils:
                logger.info('SerienStream - Episode: %s' % full_url)
            
            oRequest = cRequestHandler(full_url)
            oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0')
            sHtmlContent = oRequest.request()
            
            if len(sHtmlContent) == 0:
                return self.sources
            
            if imdb:
                a = dom_parser.parse_dom(sHtmlContent, 'a', attrs={'class': 'imdb-link'}, req='href')
                if a:
                    foundImdb = a[0].attrs.get("data-imdb", '')
                    if foundImdb and not foundImdb == imdb:
                        return
            
            pattern = r'data-link-id="([^"]+)"[^>]*data-play-url="([^"]+)"[^>]*data-provider-name="([^"]+)"[^>]*data-language-id="([^"]+)"'
            matches = re.findall(pattern, sHtmlContent, re.DOTALL | re.IGNORECASE)
            
            if not matches:
                return self.sources
            
            if log_utils:
                logger.info('SerienStream - Found %d links' % len(matches))
            
            self.episode_referer = full_url
            
            for link_id, play_url, provider_name, language_id in matches:
                try:
                    if language_id != '1':
                        continue
                    
                    redirect_url = urljoin(self.base_link, play_url)
                    
                    quality = 'SD'
                    try:
                        quality_pattern = r'data-provider-name="' + re.escape(provider_name) + r'"[^>]*>(.*?)</button>'
                        quality_match = re.search(quality_pattern, sHtmlContent, re.DOTALL | re.IGNORECASE)
                        if quality_match and 'hd' in quality_match.group(1).lower():
                            quality = 'HD'
                    except:
                        pass
                    
                    self.sources.append({
                        'source': provider_name,
                        'quality': quality,
                        'language': 'de',
                        'url': redirect_url,
                        'info': '',
                        'direct': False,
                        'debridonly': False,
                        'priority': self.priority,
                        'prioHoster': 0
                    })
                    
                    if log_utils:
                        logger.info('SerienStream - Added: %s' % provider_name)
                    
                except Exception as e:
                    if log_utils:
                        logger.info('SerienStream - Error: %s' % str(e))
                    continue
            
            if log_utils:
                logger.info('SerienStream - Total: %d sources' % len(self.sources))
            
            return self.sources
            
        except Exception as e:
            if log_utils:
                logger.info('SerienStream - Fatal: %s' % str(e))
            return self.sources
    
    def resolve(self, url):
        try:
            if log_utils:
                logger.info('SerienStream - Resolving: %s' % url[:80])
            
            try:
                import requests
                requests.packages.urllib3.disable_warnings()
                
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': getattr(self, 'episode_referer', self.base_link),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                })
                
                response = session.get(url, allow_redirects=True, verify=False, timeout=10)
                final_url = response.url
                
                if log_utils:
                    logger.info('SerienStream - Resolved to: %s' % final_url[:80])
                
                if final_url and final_url != url and len(final_url) > 20:
                    return final_url
                    
            except:
                pass
            
            try:
                oRequest = cRequestHandler(url, ignoreErrors=True)
                oRequest.addHeaderEntry('User-Agent', 'Mozilla/5.0')
                oRequest.addHeaderEntry('Referer', getattr(self, 'episode_referer', self.base_link))
                oRequest.request()
                final_url = oRequest.getRealUrl()
                
                if final_url and final_url != url:
                    if log_utils:
                        logger.info('SerienStream - Resolved via cRequestHandler: %s' % final_url[:80])
                    return final_url
            except:
                pass
            
            if log_utils:
                logger.info('SerienStream - Could not resolve, returning original URL')
            return url
            
        except Exception as e:
            if log_utils:
                logger.info('SerienStream - Resolve error: %s' % str(e))
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
            return '', ''
        
        return login, password
