# -*- coding: UTF-8 -*-
import json
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting, quote
import xbmcgui
SITE_IDENTIFIER = 'moflix'
SITE_DOMAIN = 'moflix-stream.xyz'
SITE_NAME = SITE_IDENTIFIER.upper()
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = self.base_link + '/api/v1/search/%s?query=%s&limit=8'
        self.sources = []
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            links = []
            for title in titles:
                title = quote(title)
                oRequest = cRequestHandler(self.search_link % (title, title))
                oRequest.addHeaderEntry('Referer', self.base_link + '/')
                jSearch = json.loads(oRequest.request())
                aResults = jSearch['results']
                for i in aResults:
                    if 'imdb_id' in i and i['imdb_id'] == imdb:
                        links.append({'id': i['id'], 'name': i['name']})
                        break
                    elif season == 0:
                        if 'is_series' in i and i['is_series']: continue
                        if 'year' in i and year != i['year']: continue
                        if cleantitle.get(i['name']) in t:
                            links.append({'id': i['id'], 'name': i['name']})
                    else:
                        if 'is_series' in i and not i['is_series']: continue
                        if cleantitle.get(i['name']) in t:
                            links.append({'id': i['id'], 'name': i['name']})
                if len(links) > 0: break
            if len(links) == 0: return self.sources
            for link in links:
                id = link['id']
                if season == 0:
                    url = self.base_link + '/api/v1/titles/%s?load=images,genres,productionCountries,keywords,videos,primaryVideo,seasons,compactCredits' % id
                else:
                    url = self.base_link + '/api/v1/titles/%s/seasons/%s/episodes/%s?load=videos,compactCredits,primaryVideo' % (id, season, episode)
                oRequest = cRequestHandler(url)
                oRequest.addHeaderEntry('Referer', url)
                jSearch = json.loads(oRequest.request())
                if not jSearch: continue
                if season == 0:
                    jVideos = jSearch['title']['videos']
                else:
                    jVideos = jSearch['episode']['videos']
                for j in jVideos:
                    try:
                        quality = j['quality'] if j['quality'] else 'SD'
                        valid, hoster = source_utils.is_host_valid(j['src'], hostDict)
                        if not valid: continue
                        self.sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': j['src'], 'info': j['language'], 'direct': False})
                    except:
                        pass
            return self.sources
        except:
            return self.sources
    def resolve(self, url):
        try:
            return url
        except:
            return