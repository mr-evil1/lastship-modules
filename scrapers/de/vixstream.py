# -*- coding: UTF-8 -*-
import re
import json
import urllib.parse
from scrapers.modules.tools import cParser
from resources.lib.requestHandler import cRequestHandler
from resources.lib.control import getSetting
from resources.lib.tools import logger

SITE_IDENTIFIER = 'vixstream'
SITE_DOMAIN = 'vixsrc.to'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.tak = getSetting('api.tmdb')
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/29.0 Chrome/136.0.0.0 Mobile Safari/537.36"
        self.sources = []

    def _get_tmdb_id(self, imdb_id):
        try:
            url = 'https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb_id, self.tak)
            oRequest = cRequestHandler(url, caching=True)
            sHtmlContent = oRequest.request()
            data = json.loads(sHtmlContent)
            if data.get('movie_results'):
                return str(data['movie_results'][0]['id'])
            elif data.get('tv_results'):
                return str(data['tv_results'][0]['id'])
        except:
            pass
        return None

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            tmdb_id = self._get_tmdb_id(imdb)
            if not tmdb_id:
                return self.sources
            if int(season) == 0:
                movie_url = 'https://%s/movie/%s/' % (self.domain, tmdb_id)
            else:
                movie_url = 'https://%s/tv/%s/%s/%s/' % (self.domain, tmdb_id, str(season), str(episode))
            oRequest = cRequestHandler(movie_url)
            oRequest.addHeaderEntry('User-Agent', self.ua)
            oRequest.addHeaderEntry('Referer', self.base_link + '/')
            html = oRequest.request()
            p_match = re.search(r"url:\s*'([^']+)'", html)
            t_match = re.search(r"'token':\s*'([^']+)'", html)
            e_match = re.search(r"'expires':\s*'([^']+)'", html)

            if p_match and t_match:
                playlist_base = p_match.group(1)
                token = t_match.group(1)
                expires = e_match.group(1)
                sep = '&' if '?' in playlist_base else '?'
                final_url = '%s%stoken=%s&expires=%s&h=1&lang=de' % (playlist_base, sep, token, expires)
                self.sources.append({
                    'source': 'VixCloud',
                    'quality': '1080p',
                    'language': 'de',
                    'url': final_url + '|' + movie_url,
                    'direct': False 
                })
                logger.info('[%s] Quelle gefunden: %s' % (SITE_NAME, tmdb_id))

            return self.sources
        except Exception as e:
            logger.error('[%s] Fehler: %s' % (SITE_NAME, str(e)))
            return self.sources

    def resolve(self, url_data):
        try:
            url, movie_referer = url_data.split('|')
            headers = {
                'User-Agent': self.ua,
                'Referer': movie_referer,
                'Origin': 'https://' + self.domain,
                'Accept': '*/*',
                'Accept-Language': 'de-AT,de-DE;q=0.9,de;q=0.8,en-US;q=0.7,en;q=0.6',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty'
            }
            
            header_string = urllib.parse.urlencode(headers)
            resolved_link = '%s|%s' % (url, header_string)
            
            return resolved_link
        except:
            return url_data.split('|')[0] if '|' in url_data else url_data
