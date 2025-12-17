# -*- coding: UTF-8 -*-
import re, requests, time, resolveurl as resolver
from scrapers.modules.tools import cParser
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting
SITE_IDENTIFIER = 'megakino'
SITE_DOMAIN = 'megakino.one'
SITE_NAME = SITE_IDENTIFIER.upper()
class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = self.base_link + '/index.php?do=search&subaction=search&story=%s'
        self.checkHoster = False if getSetting('provider.megakino.checkHoster') == 'false' else True
        self.sources = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Referer': self.base_link,
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'}
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            links = []
            for sSearchText in titles:
                try:
                    search_url = self.search_link % sSearchText
                    sHtmlContent = self.get_html(search_url)
                    if not sHtmlContent:
                        continue
                    r = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'id': 'dle-content'})[0].content
                    if season != 0:
                        pattern = '<a\\s+class="poster[^>]*href="([^"]+).*?alt="([^"]+)'
                    else:
                        pattern = '<a\\s+class="poster[^>]*href="([^"]+).*?alt="([^"]+)">.*?<li>.*?(\\d{4}).*?</a>'
                    isMatch, aResult = cParser.parse(r, pattern)
                    if not isMatch:
                        continue
                    if season == 0:
                        for sUrl, sName, sYear in aResult:
                            try:
                                if not int(sYear) == year:
                                    continue
                            except:
                                continue
                            if cleantitle.get(sName) in t:
                                links.append({'url': sUrl, 'name': sName, 'quality': 'HD', 'year': sYear})
                    elif season > 0:
                        for sUrl, sName in aResult:
                            sYear = ''
                            if cleantitle.get(sName.split('-')[0].strip()) in t and str(season) in sName.split('-')[1]:
                                links.append({'url': sUrl, 'name': sName.split('-')[0].strip(), 'quality': 'HD', 'year': sYear})
                    if len(links) > 0:
                        break
                except:
                    continue
            if len(links) == 0:
                return sources
            for link in links:
                sHtmlContent = self.get_html(link['url'])
                if not sHtmlContent:
                    continue
                pattern = 'poster__label">([^/|<]+)'
                isMatch, sQuality = cParser.parseSingleResult(sHtmlContent, pattern)
                if isMatch and '1080' in sQuality:
                    sQuality = '1080p'
                self.quality = sQuality if isMatch else link['quality']
                if season > 0:
                    pattern = '<select\\s+name="pmovie__select-items"[^>]+id="ep%s">\\s*(.*?)\\s*</select>' % str(episode)
                    isMatch, sHtmlContent = cParser.parseSingleResult(sHtmlContent, pattern)
                    isMatch, aResult = cParser().parse(sHtmlContent, 'value="([^"]+)')
                    if not isMatch:
                        continue
                else:
                    pattern = '<iframe.*?src=(?:"|)([^"\\s]+)'
                    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
                    if not isMatch:
                        continue
                if self.checkHoster:
                    from resources.lib import workers
                    threads = []
                    for sUrl in aResult:
                        threads.append(workers.Thread(self.chk_link, sUrl, hostDict, season, episode))
                    [i.start() for i in threads]
                    [i.join() for i in threads]
                else:
                    for sUrl in aResult:
                        if sUrl.startswith('/'):
                            sUrl = re.sub('//', 'https://', sUrl)
                        if sUrl.startswith('/'):
                            sUrl = 'https:/' + sUrl
                        valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
                        if not valid or 'youtube' in hoster:
                            continue
                        self.sources.append({'source': hoster, 'quality': link['quality'], 'language': 'de', 'url': sUrl, 'direct': False})
            return self.sources
        except:
            return self.sources

    def get_html(self, url):
        try:
            session = requests.Session()
            headers = self.headers.copy()
            r1 = session.get(url, headers=headers, timeout=10)
            html = r1.text
            if 'yg=token' in html or '?y=token' in html:
                token_url = self.base_link.rstrip('/') + '/index.php?yg=token'
                token_headers = headers.copy()
                token_headers.update({'Accept': '*/*', 'X-Requested-With': 'XMLHttpRequest', 'Referer': url})
                r2 = session.get(token_url, headers=token_headers, timeout=10)
                time.sleep(0.5)
                r3 = session.get(url, headers=headers, timeout=10)
                html = r3.text
            if html and len(html) > 500:
                return html
            else:
                return html or ""
        except:
            return ""

    def chk_link(self, sUrl, hostDict, season, episode):
        try:
            if sUrl.startswith('/'):
                sUrl = re.sub('//', 'https://', sUrl)
            if sUrl.startswith('/'):
                sUrl = 'https:/' + sUrl
            valid, hoster = source_utils.is_host_valid(sUrl, hostDict)
            if not valid or 'youtube' in hoster:
                return
            hmf = resolver.HostedMediaFile(url=sUrl, include_disabled=True, include_universal=False)
            if hmf.valid_url():
                url = hmf.resolve()
                if url:
                    self.sources.append({'source': hoster, 'quality': self.quality, 'language': 'de', 'url': url, 'direct': True})
        except:
            return

    def resolve(self, url):
        try:
            return url
        except:
            return
