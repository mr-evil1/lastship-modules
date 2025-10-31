# -*- coding: UTF-8 -*-

# 2023-01-28
# edit 2024-11-19

import re
import resolveurl as resolver
from scrapers.modules.tools import cParser  # re - alternative
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting, setSetting, urljoin
import xbmcgui
SITE_IDENTIFIER = 'fhdfilme'
SITE_DOMAIN = 'hdfilme.my'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = urljoin(self.base_link, '?story=%s&do=search&subaction=search')
        self.checkHoster = False 
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            if season == 0:
                ## https://meinecloud.click/movie/tt1477834
                oRequest = cRequestHandler('https://meinecloud.click/movie/%s' % imdb, caching=True)
                sHtmlContent = oRequest.request()
                isMatch, aResult = cParser.parse(sHtmlContent, 'data-link="([^"]+)')
                for sUrl in aResult:
                    if sUrl.startswith('/'): sUrl = 'https:' + sUrl
                    valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
                    if not valid: continue
                    self.sources.append({'source': hoster, 'quality': '720p', 'language': 'de', 'url': sUrl, 'direct': False})

            else:
                oRequest = cRequestHandler(self.search_link % imdb, caching=True)
                sHtmlContent = oRequest.request()
                pattern = 'class="thumb".*?title="([^"]+).*?href="([^"]+).*?_year">([^<]+)'
                isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                if not isMatch: return self.sources

                sName, sUrl, sYear = aResult[0]
                oRequest = cRequestHandler(sUrl, caching=True)
                sHtmlContent = oRequest.request()
                pattern = '%sx%s\s.*?/>' % (str(season), str(episode))
                isMatch, sLinkContainer = cParser.parseSingleResult(sHtmlContent, pattern)
                pattern = 'href="([^"]+)'
                isMatch, aResult = cParser.parse(sLinkContainer, pattern)
                if not isMatch: return self.sources
                for sUrl in aResult:
                    if sUrl.startswith('/'): sUrl = 'https:' + sUrl
                    valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
                    if not valid: continue
                    self.sources.append({'source': hoster, 'quality': '720p', 'language': 'de', 'url': sUrl, 'direct': False})
            return self.sources
        except:
            return self.sources

    def resolve(self, url):
        return url