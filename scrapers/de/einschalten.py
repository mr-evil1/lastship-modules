# -*- coding: UTF-8 -*-
import re
import resolveurl as resolver
import json
from scrapers.modules.tools import cParser
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting, setSetting, urljoin
from resources.lib.utils import isBlockedHoster
import xbmc
import xbmcgui

SITE_IDENTIFIER = 'einschalten'
import sys, os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..")); from resources.lib import log_utils
SITE_DOMAIN = 'einschalten.in'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = urljoin(self.base_link, 'search?query=%s')
        self.checkHoster = False
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        t = [cleantitle.get(i) for i in set(titles) if i]
        links = []
        try:
            for sSearchText in set(titles):
                URL_SEARCH = self.search_link % sSearchText
                oRequest = cRequestHandler(URL_SEARCH, caching=True)
                sHtmlContent = oRequest.request()
                pattern = 'class="group.*?title="([^"]+).*?href="([^"]+).*?span>(\d+)'
                isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                if not isMatch: continue
                for sName, sUrl, sYear in aResult:
                    sYear = int(sYear) if sYear.isdigit() else 0

                    if season == 0:
                        if cleantitle.get(sName.split('-')[0].strip()) in t and sYear == int(year):
                            links.append(sUrl)
                            break
                    else:
                        if cleantitle.get(sName.split('-')[0].strip()) in t and f'staffel {str(season)}' in sName.lower():
                            links.append(sUrl)
                            break
                if len(links) > 0: break
            if len(links) == 0:
                return self.sources
            for link in links:
                try:
                    sUrl = self.base_link + '/api' + link + '/watch'
                    sHtmlContent = cRequestHandler(sUrl).request()
                    if 'streamUrl' not in sHtmlContent:
                        log_utils.log(f'[EINSCHALTEN DEBUG] API-Antwort enthält kein "streamUrl": {sHtmlContent[:100]}...', xbmc.LOGWARNING)
                        continue
                    jResult = json.loads(sHtmlContent)
                    releaseName = jResult.get('releaseName', '')
                    streamUrl = jResult.get('streamUrl')
                    if not streamUrl:
                        continue
                    if '720p' in releaseName: quality = '720p'
                    elif '1080p' in releaseName: quality = '1080p'
                    else: quality = 'SD'
                    isBlocked, hoster, url, prioHoster = isBlockedHoster(streamUrl)
                    if isBlocked:
                        continue
                    if url:
                        self.sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url, 'direct': True, 'prioHoster': prioHoster})
                except Exception as e:
                    continue
            return self.sources
        except Exception as e:
            return self.sources
    def resolve(self, url):
        try:
            import resolveurl as resolver
            resolved_url = resolver.resolve(url)
            return resolved_url
        except Exception as e:
            return