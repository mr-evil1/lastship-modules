# -*- coding: UTF-8 -*-import re
import resolveurl as resolver
from resources.lib.control import urljoin
from resources.lib import workers
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser, source_utils
from resources.lib.control import getSetting

SITE_IDENTIFIER = 'filmpalast'
SITE_DOMAIN = 'filmpalast.to'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain

        self.search_link = '/search/title/%s'


    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        try:
            url = ''
            t = [cleantitle.get(i) for i in titles if i]
            for title in titles:
                try:
                    query = self.search_link % title
                    query = urljoin(self.base_link, query)
                    oRequest  = cRequestHandler(query)
                    sHtmlContent = oRequest.request()
                    r = dom_parser.parse_dom(sHtmlContent, 'article')
                    if r:
                        r = dom_parser.parse_dom(r, 'a', attrs={'class': 'rb'}, req='href')
                        r = [(i.attrs['href'], i.content) for i in r]
                        if len(r) == 0: continue
                        elif len(r) >= 1 and season == 0:
                            self.list = []
                            threads = []
                            for i in r:
                                threads.append(workers.Thread(self.chk_year, i, year))
                            [i.start() for i in threads]
                            [i.join() for i in threads]
                            r = self.list

                        if len(r) > 0:
                            if season > 0:
                                for i in r:
                                    link = re.findall('(.*?)S\d', i[1])
                                    if link:
                                        if cleantitle.get(link[0]) in t:
                                            url = source_utils.strip_domain(i[0])
                            else:
                                r = [i[0] for i in r if cleantitle.get(i[1]) in t]
                                if len(r) > 0:
                                    url = r[0]
                    if url:
                        break
                except:
                    pass

            if url == '': return sources
            if season > 0:
                e = '0' + str(episode) if int(episode) < 10 else str(episode)
                s = '0' + str(season) if int(season) < 10 else str(season)
                url = re.findall('(.*?)s\d', url)[0] + 's%se%s' % (s, e)


            query = urljoin(self.base_link, url)
            oRequest = cRequestHandler(query)
            moviecontent = oRequest.request()

            quality = dom_parser.parse_dom(moviecontent, 'span', attrs={'id': 'release_text'})[0].content.split('&nbsp;')[0]
            quality, info = source_utils.get_release_quality(quality)
            info = ', '.join(info)
            # keine Info
            info = ''
            r = dom_parser.parse_dom(moviecontent, 'ul', attrs={'class': 'currentStreamLinks'})
            r = [(dom_parser.parse_dom(i, 'p', attrs={'class': 'hostName'}), dom_parser.parse_dom(i, 'a')) for i in r]
            r = [(re.sub(' hd$', '', i[0][0].content.lower()), i[1][0].attrs['data-player-url'] if 'data-player-url' in i[1][0].attrs else i[1][0].attrs['href']) for i in r if i[0] and i[1]]

            for hoster, link in r:
                try:
                    valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                    if not valid: continue
                    #sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': link, 'info': info, 'direct': False, 'debridonly': False})
                    hmf = resolver.HostedMediaFile(url=link, include_disabled=True, include_universal=False)
                    if hmf.valid_url():
                        url = hmf.resolve()
                        if url: sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url, 'direct': True})
                except:
                    continue


            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            return sources

    def resolve(self, url):
        try:
            # userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'
            # if 'filmpalast.to' in url:  # 'https://filmpalast.to/vivo.php?hash=vwlyQ6rGAHHrozgDl9AWDBGyN5tybSHDnwVlMVBkPLY%3D'
            #     headers_dict = {
            #         'User-Agent': userAgent,
            #         'Origin': 'filmpalast.to',
            #         'Host': 'filmpalast.to',
            #         'Referer': url}
            # url = source_utils.check_302(url)
            return url
        except:
            return

    def chk_year(self, i, year):
        try:
            years = ('%s' % str(year), '%s' % str(int(year) + 1), '%s' % str(int(year) - 1), '0')
            #url = source_utils.strip_domain(i[0])
            query = urljoin(self.base_link, i[0])
            oRequest = cRequestHandler(query)
            sHtmlContent = oRequest.request()
            found_year = re.search('licht:.*?(\d{4})', sHtmlContent).group(1)
            if found_year in years:
                self.list.append((query,i[1]))
        except:
            pass

