# -*- coding: UTF-8 -*-
import re
import urllib.parse
import resolveurl as resolver
from resources.lib.requestHandler import cRequestHandler
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting
from resources.lib.tools import logger
from scrapers.modules import cleantitle

SITE_IDENTIFIER = 'filmpalast'
SITE_DOMAIN = 'filmpalast.to'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain

    def _request(self, url, referer=None):
        h = cRequestHandler(url, bypass_dns=True)
        h.addHeaderEntry('User-Agent', UA)
        if referer:
            h.addHeaderEntry('Referer', referer)
        data = h.request()
        logger.debug('[Filmpalast] GET %s -> %d bytes' % (url, len(data) if data else 0))
        return data

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        url = ''

        try:
            titles = [t for t in titles if t and str(t).lower() != 'none']
            logger.info('[Filmpalast] Starte Suche | Titel: %s | Jahr: %s | IMDb: %s' % (titles, year, imdb))

            for title in titles:
                search_url = self.base_link + '/search/title/' + urllib.parse.quote(title)
                data = self._request(search_url, self.base_link)
                if not data:
                    logger.warning('[Filmpalast] Keine Antwort fuer Suche: %s' % title)
                    continue

                content_match = re.search(r'id="content"[^>]*>(.+?)<div id="paging"', data, re.S | re.I)
                if not content_match:
                    logger.debug('[Filmpalast] Kein Content-Block gefunden fuer: %s' % title)
                    continue

                content = content_match.group(1)
                matches = re.findall(r'href="//filmpalast\.to(/stream/[^"]+)"[^>]*title="([^"]+)"', content, re.S | re.I)
                logger.debug('[Filmpalast] %d Treffer im Content fuer: %s' % (len(matches), title))

                clean_search = cleantitle.get(title)

                for m_url, m_title in matches:
                    clean_match = cleantitle.get(m_title)
                    logger.debug('[Filmpalast] Vergleiche: "%s" <-> "%s"' % (clean_search, clean_match))

                    if clean_search not in clean_match and clean_match not in clean_search:
                        continue

                    page_url = self.base_link + m_url
                    logger.debug('[Filmpalast] Lade Detailseite: %s' % page_url)
                    page_data = self._request(page_url, self.base_link)

                    if year:
                        y = re.search(r'>Ver&ouml;ffentlicht:\s*([^<]+)', page_data, re.I)
                        if y:
                            logger.debug('[Filmpalast] Jahr auf Seite: %s | Gesucht: %s' % (y.group(1).strip(), year))
                            if str(year) not in y.group(1):
                                logger.debug('[Filmpalast] Jahr passt nicht, ueberspringe')
                                continue
                        else:
                            logger.debug('[Filmpalast] Kein Jahr auf Seite gefunden')

                    url = page_url
                    logger.info('[Filmpalast] Treffer: %s' % url)
                    break

                if url:
                    break

            if not url:
                logger.info('[Filmpalast] Kein Treffer gefunden')
                return sources

            logger.debug('[Filmpalast] Lade Streamseite: %s' % url)
            moviecontent = self._request(url, self.base_link)

            quality = 'HD'
            q = re.search(r'<span id="release_text"[^>]*>([^<&]+)', moviecontent, re.I)
            if q:
                t = q.group(1)
                logger.debug('[Filmpalast] Release-Text: %s' % t.strip())
                if '2160' in t or '4K' in t:
                    quality = '4K'
                elif '1080' in t:
                    quality = '1080p'
                elif '720' in t:
                    quality = '720p'
            else:
                logger.debug('[Filmpalast] Kein Release-Text gefunden, verwende Standard: %s' % quality)

            streams = re.findall(
                r'<li class="hostBg[^"]*">\s*<p class="hostName">([^<]+)</p>\s*</li>\s*<li[^>]*class="streamPlayBtn[^"]*"[^>]*>\s*<!--sse--><a[^>]+(?:href|data-player-url)="(https?://[^"]+)"',
                moviecontent, re.S | re.I
            )
            logger.debug('[Filmpalast] %d Stream-Eintraege gefunden' % len(streams))

            for hoster, s_url in streams:
                if not s_url or s_url.startswith('javascript'):
                    logger.debug('[Filmpalast] Ueberspringe ungueltige URL: %s' % s_url)
                    continue

                is_blocked, res_host, res_url, prio = isBlockedHoster(s_url)
                if is_blocked and prio >= 100:
                    logger.debug('[Filmpalast] Hoster blockiert: %s (prio=%s)' % (hoster.strip(), prio))
                    continue

                source_entry = {
                    'source': res_host if res_host else hoster.strip(),
                    'quality': quality,
                    'language': 'de',
                    'url': res_url if res_url else s_url,
                    'direct': False,
                    'debridonly': False
                }
                logger.debug('[Filmpalast] Quelle hinzugefuegt: %s | %s | %s' % (source_entry['source'], quality, source_entry['url']))
                sources.append(source_entry)

            logger.info('[Filmpalast] Fertig | %d Quellen gefunden | Qualitaet: %s' % (len(sources), quality))
            return sources

        except Exception as e:
            logger.error('[Filmpalast] Unerwarteter Fehler: %s' % e)
            return sources

    def resolve(self, url):
        return url
