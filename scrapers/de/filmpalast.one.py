# -*- coding: UTF-8 -*-
import re
import urllib.parse
import resolveurl as resolver
from resources.lib.requestHandler import cRequestHandler
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting
from resources.lib.tools import logger
from scrapers.modules import cleantitle
try:
    from html import unescape as html_unescape
except ImportError:
    from HTMLParser import HTMLParser as _hp
    html_unescape = _hp().unescape

SITE_IDENTIFIER = 'filmpalast.one'
SITE_DOMAIN = 'filmpalast.one'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = '/index.php?do=search&subaction=search&story=%s'

    def _request(self, url, referer=None):
        h = cRequestHandler(url, bypass_dns=True)
        h.addHeaderEntry('User-Agent', UA)
        if referer:
            h.addHeaderEntry('Referer', referer)
        return h.request()

    def _parse_results(self, html):
        matches = re.findall(
            r'<a\s+href="(https?://(?:www\.)?filmpalast\.\w+/stream/[^"]+)"[^>]*>\s*'
            r'(?:<[^>]+>\s*)*<h3[^>]*class="Title"[^>]*>([^<]+)</h3>',
            html, re.S | re.I
        )
        if matches:
            return matches
        results = []
        for m_url in re.findall(
            r'href="(https?://(?:www\.)?filmpalast\.\w+/stream/[^"]+)"', html, re.I
        ):
            slug = re.search(r'/stream/\d+-(.+?)(?:-deutsch)?\.html', m_url, re.I)
            if slug:
                results.append((m_url, slug.group(1).replace('-', ' ')))
        return results

    def _find_url_by_id(self, imdb):
        search_url = self.base_link + (self.search_link % urllib.parse.quote(imdb))
        data = self._request(search_url, self.base_link)
        if not data:
            return None
        results = self._parse_results(data)
        if results:
            return results[0][0]
        return None

    def _find_url_by_title(self, query, titles, year):
        search_url = self.base_link + (self.search_link % urllib.parse.quote(query))
        data = self._request(search_url, self.base_link)
        if not data:
            return None
        clean_titles = [cleantitle.get(t) for t in titles]
        for m_url, m_title in self._parse_results(data):
            clean_match = cleantitle.get(html_unescape(m_title))
            if not any(ct in clean_match or clean_match in ct for ct in clean_titles):
                continue
            page_data = self._request(m_url, self.base_link)
            if not page_data:
                continue
            if year:
                y = re.search(r'Erscheinungsdatum:\s*</strong>\s*\d{2}-\d{2}-(\d{4})', page_data, re.I)
                if y and str(year) not in y.group(1):
                    continue
            return m_url
        return None

    def _short_query(self, title):
        words = title.strip().split()
        for i in range(1, len(words) + 1):
            if len(' '.join(words[:i])) >= 4:
                return ' '.join(words[:min(i + 2, len(words))])
        return title[:20]

    def _resolve_meinecloud(self, imdb, referer, quality):
        sources = []
        seen_urls = set()

        movie_url = 'https://meinecloud.click/movie/' + imdb
        movie_data = self._request(movie_url, referer)
        embed_urls = []
        if movie_data:
            raw_links = re.findall(r'data-link="(//[^"]+)"', movie_data, re.I)
            for link in raw_links:
                embed_urls.append('https:' + link)
            logger.info('[Filmpalast] meinecloud /movie/ data-links: %s' % embed_urls)

        ddl_url = 'https://meinecloud.click/ddl/' + imdb
        ddl_data = self._request(ddl_url, referer)
        ddl_urls = []
        if ddl_data:
            ddl_urls = re.findall(r"window\.open\(\s*\\'(https?://[^\\']+)\\'", ddl_data)
            logger.info('[Filmpalast] meinecloud /ddl/ Hoster: %s' % ddl_urls)

        all_urls = embed_urls + [u for u in ddl_urls if u not in embed_urls]

        for s_url in all_urls:
            norm = s_url.rstrip('/')
            if norm in seen_urls:
                continue
            seen_urls.add(norm)
            if not s_url or s_url.startswith('javascript'):
                continue
            hoster = re.sub(r'^https?://(?:www\.)?([^/]+).*$', r'\1', s_url)
            is_blocked, res_host, res_url, prio = isBlockedHoster(s_url)
            if is_blocked and prio >= 100:
                continue
            sources.append({
                'source': res_host if res_host else hoster,
                'quality': quality,
                'language': 'de',
                'url': res_url if res_url else s_url,
                'direct': False,
                'debridonly': False
            })
        logger.info('[Filmpalast] meinecloud gesamt %d Quellen' % len(sources))
        return sources

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        url = ''
        try:
            titles = [t for t in titles if t and str(t).lower() != 'none']
            logger.info('[Filmpalast] Suche: %s  imdb=%s  year=%s' % (titles, imdb, year))
            if imdb:
                url = self._find_url_by_id(imdb)
                if url:
                    logger.info('[Filmpalast] Treffer via IMDb: %s' % url)
            if not url:
                seen_queries = set()
                for title in titles:
                    query = self._short_query(title)
                    if not query or query in seen_queries:
                        continue
                    seen_queries.add(query)
                    logger.info('[Filmpalast] Query: %s' % query)
                    url = self._find_url_by_title(query, titles, year)
                    if url:
                        logger.info('[Filmpalast] Treffer via Titel: %s' % url)
                        break
            if not url:
                logger.info('[Filmpalast] Kein Treffer.')
                return sources
            moviecontent = self._request(url, self.base_link)
            logger.info('[Filmpalast] Seitengroesse: %d bytes' % len(moviecontent or ''))
            quality = 'HD'
            q = re.search(r'<span[^>]*class="Qlty"[^>]*>([^<]+)', moviecontent, re.I)
            if q:
                t = q.group(1).strip()
                if '2160' in t or '4K' in t.upper():
                    quality = '4K'
                elif '1080' in t:
                    quality = '1080p'
                elif '720' in t:
                    quality = '720p'
            streams = re.findall(
                r'class="[^"]*TPlayerTb[^"]*"[^>]*>\s*<iframe[^>]+src="([^"]+)"',
                moviecontent, re.S | re.I
            )
            if not streams:
                streams = re.findall(r'<iframe[^>]+src="(https?://[^"]+)"', moviecontent, re.I)
                logger.info('[Filmpalast] Fallback iframe-Suche: %d gefunden' % len(streams))
            for s_url in streams:
                if not s_url or s_url.startswith('javascript'):
                    continue
                if 'meinecloud.click' in s_url and imdb:
                    logger.info('[Filmpalast] meinecloud erkannt, lese /movie/ + /ddl/ fuer %s' % imdb)
                    mc_sources = self._resolve_meinecloud(imdb, url, quality)
                    sources.extend(mc_sources)
                    continue
                hoster = re.sub(r'^https?://(?:www\.)?([^/]+).*$', r'\1', s_url)
                is_blocked, res_host, res_url, prio = isBlockedHoster(s_url)
                if is_blocked and prio >= 100:
                    continue
                sources.append({
                    'source': res_host if res_host else hoster,
                    'quality': quality,
                    'language': 'de',
                    'url': res_url if res_url else s_url,
                    'direct': False,
                    'debridonly': False
                })
            logger.info('[Filmpalast] %d Quellen gefunden' % len(sources))
            return sources
        except Exception as e:
            logger.error('[Filmpalast] Fehler: %s' % e)
            return sources

    def resolve(self, url):
        return url
