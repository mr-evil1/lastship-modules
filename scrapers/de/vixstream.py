# -*- coding: UTF-8 -*-
#evl
import re
import json
import base64
import urllib.parse
try:
    import cloudscraper
except:
    try:
        import cloudscraper2 as cloudscraper
    except:
        import cloudrequest as cloudscraper
from resources.lib.requestHandler import cRequestHandler
from resources.lib.control import getSetting
from resources.lib.tools import logger

SITE_IDENTIFIER = 'vixstream'
SITE_DOMAIN = 'vixsrc.to'
SITE_NAME = SITE_IDENTIFIER.upper()
_K = base64.b64decode('ZWRkZTZiNWU0MTI0NmFiNzlhMjY5N2NkMTI1ZTE3ODE=').decode()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de', 'en']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.tak = getSetting('api.tmdb') or _K
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/30.0 Chrome/143.0.0.0 Mobile Safari/537.36"
        self.sources = []
        self._session = None
        self._scraper = None

    def _get_session(self):
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                self._session.headers.update({
                    'User-Agent': self.ua,
                    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'
                })
            except ImportError:
                logger.error('[%s] requests module nicht verfügbar!' % SITE_NAME)
        return self._session

    def _get_scraper(self):
        if self._scraper is None:
            self._scraper = cloudscraper.create_scraper()
            self._scraper.headers.update({
                'User-Agent': self.ua,
                'sec-ch-ua': '"Samsung Internet";v="30.0", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-platform': '"Android"',
                'sec-ch-ua-mobile': '?1',
                'Accept': '*/*',
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': self.base_link,
                'Referer': self.base_link + '/',
            })
        return self._scraper

    def _get_tmdb_id(self, imdb_id):
        try:
            url = 'https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb_id, self.tak)
            oRequest = cRequestHandler(url, caching=True)
            data = json.loads(oRequest.request())
            if data.get('movie_results'):
                return str(data['movie_results'][0]['id'])
            elif data.get('tv_results'):
                return str(data['tv_results'][0]['id'])
        except Exception as e:
            logger.error('[%s] TMDB Fehler: %s' % (SITE_NAME, str(e)))
        return None

    def _stream_languages(self):
        setting = getSetting('hosts.language') or '0'
        if setting == '1':
            return [('de', 'Deutsch')]
        if setting == '2':
            return [('en', 'Englisch')]
        return [('de', 'Deutsch'), ('en', 'Englisch')]

    def _src_with_language(self, src, language):
        if re.search(r'([?&])lang=[a-z]+', src):
            return re.sub(r'([?&])lang=[a-z]+', r'\1lang=%s' % language, src)
        separator = '&' if '?' in src else '?'
        return '%s%slang=%s' % (src, separator, language)

    def _visit_page_for_cookies(self, page_url):
        try:
            scraper = self._get_scraper()
            if not scraper:
                logger.error('[%s] Keine Scraper verfügbar' % SITE_NAME)
                return False
            response = scraper.get(page_url, headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }, timeout=10)
            logger.info('[%s] Seite besucht: %s - Status: %s' % (SITE_NAME, page_url, response.status_code))
            return response.status_code == 200
        except Exception as e:
            logger.error('[%s] Fehler beim Seitenbesuch: %s' % (SITE_NAME, str(e)))
            return False

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            tmdb_id = self._get_tmdb_id(imdb)
            if not tmdb_id:
                logger.warning('[%s] Keine TMDB-ID gefunden für IMDB: %s' % (SITE_NAME, imdb))
                return self.sources

            if int(season) == 0:
                page_url = 'https://%s/movie/%s' % (self.domain, tmdb_id)
                api_url = 'https://%s/api/movie/%s' % (self.domain, tmdb_id)
            else:
                page_url = 'https://%s/tv/%s' % (self.domain, tmdb_id)
                api_url = 'https://%s/api/tv/%s/%s/%s' % (self.domain, tmdb_id, str(season), str(episode))

            logger.info('[%s] ========== RUN START ==========' % SITE_NAME)
            logger.info('[%s] TMDB-ID: %s' % (SITE_NAME, tmdb_id))
            logger.info('[%s] Page URL: %s' % (SITE_NAME, page_url))
            logger.info('[%s] API URL: %s' % (SITE_NAME, api_url))
            logger.info('[%s] [1/4] Besuche Seite für Cookies...' % SITE_NAME)
            self._visit_page_for_cookies(page_url)

            scraper = self._get_scraper()
            if not scraper:
                logger.error('[%s] Keine Scraper für API-Aufruf verfügbar' % SITE_NAME)
                return self.sources

            logger.info('[%s] [2/4] API-Aufruf...' % SITE_NAME)
            
            response = scraper.get(api_url, headers={
                'Referer': page_url,
                'Accept': 'application/json, */*',
                'Origin': 'https://' + self.domain,
                'Connection': 'keep-alive',
                'X-Requested-With': 'XMLHttpRequest'
            }, timeout=10)

            logger.info('[%s] API Response Status: %s' % (SITE_NAME, response.status_code))

            if response.status_code != 200:
                logger.error('[%s] API-Status nicht 200! Status: %s' % (SITE_NAME, response.status_code))
                logger.debug('[%s] Response: %s' % (SITE_NAME, response.text[:500]))
                return self.sources

            try:
                data = response.json()
                logger.debug('[%s] API JSON erfolgreich geparst' % SITE_NAME)
            except json.JSONDecodeError as e:
                logger.error('[%s] JSON-Parse Fehler: %s' % (SITE_NAME, str(e)))
                logger.debug('[%s] Response Text: %s' % (SITE_NAME, response.text[:500]))
                return self.sources

            src = data.get('src', '')
            logger.info('[%s] API returned src: %s' % (SITE_NAME, src[:150] if src else 'LEER!'))

            if not src:
                logger.warning('[%s] Kein src in API-Response gefunden' % SITE_NAME)
                logger.debug('[%s] API Response: %s' % (SITE_NAME, json.dumps(data, indent=2)[:1000]))
                return self.sources

            logger.info('[%s] [3/4] Teste embed URLs...' % SITE_NAME)
            
            seen_urls = set()
            for language, language_label in self._stream_languages():
                lang_src = self._src_with_language(src, language)
                embed_url = 'https://%s%s' % (self.domain, lang_src)
                
                if embed_url in seen_urls:
                    logger.debug('[%s] Embed URL bereits gesehen, überspringe' % SITE_NAME)
                    continue
                
                seen_urls.add(embed_url)
                logger.info('[%s] Teste embed URL sofort nach API-Aufruf...' % SITE_NAME)
                test_response = scraper.get(embed_url, headers={
                    'Referer': page_url,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }, timeout=10)
                
                logger.info('[%s] Embed URL Test Status: %s' % (SITE_NAME, test_response.status_code))
                
                if test_response.status_code != 200:
                    logger.warning('[%s] ⚠ Embed URL gibt Status %s zurück!' % (SITE_NAME, test_response.status_code))
                    if test_response.status_code == 410:
                        logger.warning('[%s] Token ist UNGÜLTIG oder SESSION ABGELAUFEN' % SITE_NAME)
                token_match = re.search(r'token=([^&]+)', embed_url)
                token_value = token_match.group(1) if token_match else 'NICHT GEFUNDEN'
                
                logger.info('[%s] Quelle %s: Token=%s..., URL=%s' % (
                    SITE_NAME, language, token_value[:20], embed_url[:100]
                ))
                
                self.sources.append({
                    'source': 'VixCloud',
                    'quality': '1080p',
                    'language': language,
                    'url': embed_url + '|' + page_url,
                    'direct': False,
                    'info': language_label
                })

            logger.info('[%s] [4/4] %d Quellen hinzugefügt' % (SITE_NAME, len(self.sources)))
            logger.info('[%s] ========== RUN END ==========' % SITE_NAME)

        except Exception as e:
            logger.error('[%s] run() Fehler: %s' % (SITE_NAME, str(e)))
            import traceback
            logger.debug('[%s] Traceback: %s' % (SITE_NAME, traceback.format_exc()))

        return self.sources

    def _extract_token_from_html(self, html):
        patterns = [
            r'["\']token["\']\s*:\s*["\']([a-f0-9\-_]{32,})["\']',
            r'token["\']?\s*:\s*["\']([a-zA-Z0-9\-_]{32,})["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return None

    def _extract_expires_from_html(self, html):
        patterns = [
            r'["\']expires["\']\s*:\s*["\']?(\d{10})["\']?',
            r'expires["\']?\s*:\s*["\']?(\d{10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return None

    def _extract_url_from_html(self, html):
        patterns = [
            r'["\']?url["\']?\s*:\s*["\']([^"\']*?/playlist/\d+)["\']',
            r'["\']?url["\']?\s*[=:]\s*["\']([^"\']*?/playlist/\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return None

    def _extract_playlist_token_from_html(self, html):
        patterns = [
            r'token["\']?\s*:\s*["\']([a-f0-9]{32})["\']',
            r'["\']token["\']?\s*:\s*["\']([a-f0-9]{32})["\']',
            r'const\s+token\s*=\s*["\']([a-f0-9]{32})["\']',
            r'["\']token["\']?\s*[=:]\s*["\']?([a-f0-9]{32})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                token = match.group(1)
                if len(token) == 32 and all(c in '0123456789abcdef' for c in token):
                    logger.debug('[%s] Playlist-Token mit Pattern %s gefunden' % (SITE_NAME, pattern))
                    return token
        
        return None

    def resolve(self, url_data):
        try:
            embed_url, referer = url_data.split('|', 1)
            
            logger.info('[%s] ========== RESOLVE START ==========' % SITE_NAME)
            logger.info('[%s] embed_url: %s' % (SITE_NAME, embed_url[:150]))

            scraper = self._get_scraper()
            if not scraper:
                logger.error('[%s] Keine Scraper für resolve verfügbar' % SITE_NAME)
                return None

            parsed_embed = urllib.parse.urlparse(embed_url)
            query_params = urllib.parse.parse_qs(parsed_embed.query)
            
            logger.debug('[%s] URL Parameters:' % SITE_NAME)
            for key, val in query_params.items():
                logger.debug('[%s]   %s: %s' % (SITE_NAME, key, val[0][:50] if val else 'N/A'))
            
            video_id_match = re.search(r'/embed/(\d+)', embed_url)
            if not video_id_match:
                logger.error('[%s] Konnte Video-ID nicht extrahieren: %s' % (SITE_NAME, embed_url))
                return None
            
            video_id = video_id_match.group(1)
            stream_language = query_params.get('lang', ['de'])[0]
            if stream_language not in ['de', 'en']:
                stream_language = 'de'

            logger.info('[%s] Video-ID: %s, Language: %s' % (SITE_NAME, video_id, stream_language))

            logger.info('[%s] [1/3] Lade embed-Seite...' % SITE_NAME)
            
            response = scraper.get(embed_url, headers={
                'Referer': 'https://%s/' % self.domain,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8' if stream_language == 'de' else 'en-US,en;q=0.9,de;q=0.7',
            }, timeout=15)

            logger.info('[%s] Embed-Seite Status: %s' % (SITE_NAME, response.status_code))
            
            if response.status_code != 200:
                logger.error('[%s] FEHLER: Embed-Seite Status nicht 200!' % SITE_NAME)
                logger.error('[%s] Status: %s - %s' % (SITE_NAME, response.status_code, response.reason))
                
                if response.status_code == 410:
                    logger.error('[%s] Status 410 = Token ist UNGÜLTIG oder SESSION ABGELAUFEN!' % SITE_NAME)
                
                logger.debug('[%s] Response Preview: %s...' % (SITE_NAME, response.text[:300]))
                return None

            html = response.text
            logger.info('[%s] Embed-HTML erhalten (%d Zeichen)' % (SITE_NAME, len(html)))

            logger.info('[%s] [2/3] Extrahiere Playlist-Token...' % SITE_NAME)
            playlist_token = self._extract_playlist_token_from_html(html)
            
            if not playlist_token:
                logger.error('[%s]  Playlist-Token nicht gefunden!' % SITE_NAME)
                logger.debug('[%s] HTML Preview: %s...' % (SITE_NAME, html[:2000]))
                return None

            logger.info('[%s] Token gefunden: %s...' % (SITE_NAME, playlist_token[:16]))

            expires = self._extract_expires_from_html(html)
            if not expires:
                logger.error('[%s]  Expires nicht gefunden!' % SITE_NAME)
                return None

            logger.info('[%s]  Expires gefunden: %s' % (SITE_NAME, expires))

            logger.info('[%s] [3/3] Konstruiere Playlist-URL...' % SITE_NAME)
            
            playlist_url = 'https://%s/playlist/%s?token=%s&expires=%s&h=1&lang=%s' % (
                self.domain, video_id, playlist_token, expires, stream_language
            )
            logger.info('[%s] Playlist-URL: %s' % (SITE_NAME, playlist_url[:150]))

            final_url = '%s|%s' % (playlist_url, urllib.parse.urlencode({
                'User-Agent': self.ua,
                'Referer': 'https://%s/embed/%s' % (self.domain, video_id),
                'Origin': 'https://' + self.domain,
            }))
            
            logger.info('[%s]  Finale URL generiert' % SITE_NAME)
            logger.info('[%s] ========== RESOLVE END ==========' % SITE_NAME)
            return final_url

        except Exception as e:
            logger.error('[%s]  resolve() Fehler: %s' % (SITE_NAME, str(e)))
            import traceback
            logger.debug('[%s] Traceback: %s' % (SITE_NAME, traceback.format_exc()))
            return None

    def get_source(self, url, host, data):
        try:
            scraper = self._get_scraper()
            response = scraper.get(url)
            if response.status_code != 200:
                logger.error('[%s] Fehler: %s' % (SITE_NAME, response.status_code))
                return None
            return response.text
        except Exception as e:
            logger.error('[%s] Exception: %s' % (SITE_NAME, e))
            return None
