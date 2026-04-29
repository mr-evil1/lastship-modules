# -*- coding: UTF-8 -*-
import re
import json
import base64
import urllib.parse
from resources.lib.requestHandler import cRequestHandler
from resources.lib.control import getSetting
from resources.lib.tools import logger

SITE_IDENTIFIER = 'vixstream'
SITE_DOMAIN = 'vixsrc.to'
SITE_NAME = SITE_IDENTIFIER.upper()
VIXCLOUD = 'vixcloud.co'
_K = base64.b64decode('ZWRkZTZiNWU0MTI0NmFiNzlhMjY5N2NkMTI1ZTE3ODE=').decode()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.tak = getSetting('api.tmdb') or _K
        self.ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/29.0 Chrome/136.0.0.0 Mobile Safari/537.36"
        self.sources = []

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

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            tmdb_id = self._get_tmdb_id(imdb)
            if not tmdb_id:
                return self.sources

            if int(season) == 0:
                api_url = 'https://%s/api/movie/%s' % (self.domain, tmdb_id)
            else:
                api_url = 'https://%s/api/tv/%s/%s/%s' % (self.domain, tmdb_id, str(season), str(episode))

            oRequest = cRequestHandler(api_url)
            oRequest.addHeaderEntry('User-Agent', self.ua)
            oRequest.addHeaderEntry('Referer', self.base_link + '/')
            oRequest.addHeaderEntry('Accept', 'application/json')
            data = json.loads(oRequest.request())

            src = data.get('src', '')
            if not src:
                return self.sources

            src = re.sub(r'lang=[a-z]+', 'lang=de', src)
            embed_url = 'https://%s%s' % (VIXCLOUD, src)

            self.sources.append({
                'source': 'VixCloud',
                'quality': '1080p',
                'language': 'de',
                'url': embed_url + '|' + self.base_link,
                'direct': False
            })
            logger.info('[%s] Quelle gefunden: tmdb=%s' % (SITE_NAME, tmdb_id))

        except Exception as e:
            logger.error('[%s] Fehler: %s' % (SITE_NAME, str(e)))

        return self.sources

    def resolve(self, url_data):
        try:
            embed_url, referer = url_data.split('|', 1)

            oRequest = cRequestHandler(embed_url)
            oRequest.addHeaderEntry('User-Agent', self.ua)
            oRequest.addHeaderEntry('Referer', referer)
            oRequest.addHeaderEntry('Origin', 'https://' + self.domain)
            html = oRequest.request()

            m = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', html)
            if not m:
                m = re.search(r'(?:url|file)\s*[=:]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html)
            if not m:
                m = re.search(r'["\'](https?://[^"\']*playlist[^"\']*)["\']', html)
            if not m:
                logger.error('[%s] resolve: kein m3u8 gefunden' % SITE_NAME)
                return None

            headers = {
                'User-Agent': self.ua,
                'Referer': embed_url,
                'Origin': 'https://' + VIXCLOUD,
            }
            return '%s|%s' % (m.group(1), urllib.parse.urlencode(headers))

        except Exception as e:
            logger.error('[%s] resolve Fehler: %s' % (SITE_NAME, str(e)))
            return None
