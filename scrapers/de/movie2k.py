# -*- coding: UTF-8 -*-
from resources.lib.utils import isBlockedHoster
import re, json
from resources.lib.control import getSetting
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules.tools import cParser
import sys, os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..")); from resources.lib import log_utils

SITE_IDENTIFIER = 'movie2k'
SITE_DOMAIN = 'movie2k.ch'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = self.base_link + '/data/search/?lang=2&keyword=%s'
        self.watch_link = self.base_link + '/data/watch/?_id=%s'
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb=''):
        jSearch = self.search(titles, year, season, episode, imdb)
        if not jSearch:
            return []
        jSearch = sorted(jSearch, key=lambda k: k.get('added', ''), reverse=True)
        total = 0
        loop = 0
        for i in range(len(jSearch)):
            if jSearch[i].get('deleted', 0):
                continue
            sUrl = jSearch[i].get('stream', '')
            if not sUrl:
                continue
            if sUrl.startswith('//'):
                sUrl = 'https:' + sUrl
            loop += 1
            if loop == 50:
                break
            release = jSearch[i].get('release', '')
            if '2160' in release or '4K' in release:
                quality = '4K'
            elif '1440' in release or '2K' in release:
                quality = '1440p'
            elif '1080' in release:
                quality = '1080p'
            elif '720' in release:
                quality = '720p'
            elif '480' in release:
                quality = '480p'
            elif '360' in release:
                quality = '360p'
            else:
                quality = 'HD'
            isBlocked, hoster, url, prioHoster = isBlockedHoster(sUrl)
            if isBlocked:
                continue
            if url:
                self.sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url, 'direct': True, 'prioHoster': prioHoster})
                total += 1
                if total == 10:
                    break
        return self.sources

    def resolve(self, url):
        return url

    def _get_imdb_from_entry(self, entry):
        try:
            tmdb = entry.get('tmdb', {})
            if isinstance(tmdb, str):
                tmdb = json.loads(tmdb)
            details = tmdb.get('movie', {})
            if isinstance(details, list):
                details = details[0] if details else {}
            return details.get('movie_details', {}).get('imdb_id', '')
        except Exception:
            return ''

    def search(self, titles, year, season, episode, imdb=''):
        for title in titles:
            try:
                from urllib.parse import quote
                query = self.search_link % quote(title)
                oRequest = cRequestHandler(query)
                raw = oRequest.request()
                if not raw:
                    continue
                results = json.loads(raw)
                if not isinstance(results, list) or not results:
                    continue

                _id = False

                if imdb:
                    for i in results:
                        if i.get('imdb_id', '') == imdb or self._get_imdb_from_entry(i) == imdb:
                            if season > 0 and str(i.get('s', '')) != str(season):
                                continue
                            _id = i.get('_id', False)
                            if _id:
                                break

                if not _id:
                    if season > 0:
                        for i in results:
                            if not i.get('tv', 0):
                                continue
                            isMatch, sSeason = cParser.parseSingleResult(i.get('title', ''), r'Staffel.*?(\d+)')
                            if sSeason == str(season):
                                _id = i.get('_id', False)
                                if _id:
                                    break
                        if not _id:
                            for i in results:
                                if i.get('tv', 0):
                                    _id = i.get('_id', False)
                                    if _id:
                                        break
                    else:
                        for i in results:
                            if i.get('tv', 0):
                                continue
                            if i.get('year') and str(i.get('year')) != str(year):
                                continue
                            _id = i.get('_id', False)
                            if _id:
                                break

                if not _id:
                    continue

                oRequest = cRequestHandler(self.watch_link % _id)
                watch = json.loads(oRequest.request())
                streams = watch.get('streams', [])
                if not streams:
                    continue
                if season > 0:
                    return [s for s in streams if str(s.get('e', '')) == str(episode)]
                return streams
            except Exception:
                continue
        return []
