# -*- coding: UTF-8 -*-
import re
import json

from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import source_utils
from resources.lib.control import getSetting

SITE_IDENTIFIER = 'gezkino'
SITE_DOMAIN     = 'mediathekviewweb.de'
SITE_NAME       = 'GEZ Kino'

API_URL         = 'https://mediathekviewweb.de/api/query'
MIN_DURATION    = 4680
SKIP_WORDS      = ['audiodeskription', 'audio description', 'hörfilm', 'deskription', 'barrierefrei', 'ad version']
QUERY_TERMS     = ['Spielfilm', 'Spielfilme', 'Filme']
STRIP_MARKERS   = [
    ' - Spielfilm', u' \u2013 Spielfilm', ', Spielfilm',
    u' \xd6sterreich', ', Deutschland', ', Schweiz', ', Belgien',
    ', Frankreich', ', Spanien', ', Niederlande', ', Irland',
    ', Luxemburg', ', Italien', ', USA', ', Kosovo',
    u', Gro\xdfbritannien', ', Norwegen', ', BRD', u', D\xe4nemark',
    ', Australien', ', Schweden', ' Fernsehfilm', ' Heimatfilm',
    ' - Thriller', ' - Drama', u'\xab', u'\xbb',
]


class source:
    def __init__(self):
        self.priority  = 2
        self.language  = ['de']
        self.domain    = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.checkHoster = False
        self.sources   = []

    def _clean(self, title):
        s = title
        for m in STRIP_MARKERS:
            s = re.split(re.escape(m), s, flags=re.I)[0]
        s = re.sub(r'^(Spielfilm|Spiellfilm):\s*', '', s, flags=re.I)
        s = re.sub(r'\(.*?\)', '', s)
        return re.sub(r'[^a-z0-9]', '', s.lower())

    def _matches(self, candidate, titles):
        c = self._clean(candidate)
        for t in titles:
            n = re.sub(r'[^a-z0-9]', '', t.lower())
            if n and (n in c or c in n):
                return True
        return False

    def _query(self, query_term):
        try:
            payload = json.dumps({
                'queries': [{'fields': ['topic'], 'query': query_term}],
                'size': 2000,
                'sortBy': 'timestamp',
                'sortOrder': 'desc',
            })
            oRequest = cRequestHandler(API_URL, caching=True, method='POST', data=payload)
            oRequest.addHeaderEntry('Content-Type', 'application/json')
            sHtml = oRequest.request()
            if not sHtml:
                return []
            results = []
            for m in json.loads(sHtml).get('result', {}).get('results', []):
                url   = m.get('url_video', '')
                title = m.get('title', '')
                if not url or not title:
                    continue
                if m.get('duration', 0) < MIN_DURATION:
                    continue
                if any(x in title.lower() for x in SKIP_WORDS):
                    continue
                results.append({'url': url, 'title': title})
            return results
        except Exception:
            return []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            if season != 0:
                return self.sources

            seen = set()
            for term in QUERY_TERMS:
                for entry in self._query(term):
                    url = entry['url']
                    if url in seen:
                        continue
                    if not self._matches(entry['title'], titles):
                        continue
                    seen.add(url)
                    valid, hoster = source_utils.is_host_valid(url, hostDict)
                    self.sources.append({
                        'source':   hoster if valid else 'Mediathek',
                        'quality':  'HD',
                        'language': 'de',
                        'url':      url,
                        'direct':   not valid,
                    })
        except Exception:
            pass
        return self.sources

    def resolve(self, url):
        return url
