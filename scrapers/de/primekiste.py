# -*- coding: utf-8 -*-
import re, json
from resources.lib.control import getSetting
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle
from resources.lib.tools import logger, cParser
from resources.lib.utils import isBlockedHoster
import xbmc

SITE_IDENTIFIER = 'primekiste'
SITE_DOMAIN = 'primekiste.com'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = '/data/browse/?lang=2&keyword=%s&year=%s&type=%s&page=1&limit=20'
        self.watch_link = '/data/watch/?_id=%s'
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        self.sources = []
        try:
            jSearch = self.search(titles, year, season, episode)
            if not jSearch or len(jSearch) == 0:
                return []
            for item in jSearch:
                movie_id = item.get('id')
                if not movie_id:
                    continue
                watch_url = self.base_link + self.watch_link % movie_id
                oRequest = cRequestHandler(watch_url, caching=False)
                response = oRequest.request()
                if not response:
                    continue
                try:
                    jWatch = json.loads(response)
                except Exception:
                    continue
                streams = jWatch.get('streams', [])
                if not streams:
                    continue

                def get_quality_score(stream):
                    release = stream.get('release', '').lower()
                    if '2160p' in release or '4k' in release:
                        return 4
                    if '1080p' in release:
                        return 3
                    if '720p' in release:
                        return 2
                    return 1

                streams = sorted(streams, key=lambda k: (get_quality_score(k), k.get('added', '')), reverse=True)

                total = 0
                processed_count = 0
                for stream in streams:
                    processed_count += 1
                    if processed_count > 50:
                        break

                    if season > 0 and episode > 0:
                        stream_episode = stream.get('e')
                        if stream_episode and int(stream_episode) != episode:
                            continue

                    stream_url = stream.get('stream')
                    if not stream_url:
                        continue

                    quality = 'HD'
                    release = stream.get('release', '')
                    if release:
                        if '2160p' in release or '4k' in release.lower():
                            quality = '4K'
                        elif '1080p' in release:
                            quality = '1080p'
                        elif '720p' in release:
                            quality = '720p'

                    isBlocked, hoster, url, prioHoster = isBlockedHoster(stream_url)
                    if isBlocked or not url:
                        continue

                    is_duplicate = False
                    for s in self.sources:
                        if s['source'] == hoster and s['quality'] == quality:
                            is_duplicate = True
                            break

                    if is_duplicate:
                        continue

                    self.sources.append({
                        'source': hoster,
                        'quality': quality,
                        'language': 'de',
                        'url': url,
                        'direct': True,
                        'prioHoster': prioHoster
                    })

                    total += 1
                    if total >= 15:
                        break

            return self.sources
        except Exception as e:
            logger.error('Primekiste run error: %s' % e)
            return []

    def search(self, titles, year, season, episode):
        results = []
        mtype = 'tvseries' if season > 0 else 'movies'
        year_str = str(year) if year else ''
        clean_titles = [cleantitle.get(t) for t in titles if t]
        found_perfect = False

        for title in titles:
            try:
                search_url = self.base_link + self.search_link % (title, year_str, mtype)
                oRequest = cRequestHandler(search_url, caching=False)
                response = oRequest.request()
                if not response:
                    continue
                try:
                    jSearch = json.loads(response)
                except Exception:
                    continue
                movies = jSearch.get('movies', [])
                if not movies:
                    continue

                for item in movies:
                    movie_id = item.get('_id')
                    if not movie_id:
                        continue

                    movie_title = item.get('title', '')
                    movie_year = item.get('year')
                    clean_title = cleantitle.get(movie_title)

                    if season > 0:
                        season_match = False
                        if 'staffel' in clean_title.lower():
                            match = re.search(r'staffel\s*(\d+)', clean_title.lower())
                            if match and int(match.group(1)) == season:
                                season_match = True

                        title_match = any(t in clean_title for t in clean_titles)

                        if title_match and season_match:
                            results.append({
                                'id': movie_id,
                                'title': movie_title,
                                'year': movie_year
                            })
                            found_perfect = True
                            break
                    else:
                        title_match = clean_title in clean_titles
                        year_match = True

                        if year and movie_year:
                            try:
                                if abs(int(movie_year) - int(year)) > 1:
                                    year_match = False
                            except:
                                pass

                        if title_match and year_match:
                            results.append({
                                'id': movie_id,
                                'title': movie_title,
                                'year': movie_year
                            })
                            found_perfect = True
                            break

                if found_perfect:
                    break

            except Exception as e:
                logger.error('Primekiste search error: %s' % e)
                continue

        return results

    def resolve(self, url):
        return url



















