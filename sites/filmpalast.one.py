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

try:
    from resolveurl.plugins.dropload import DropLoadResolver
    DropLoadResolver.domains = ['dropload.io', 'dropload.tv', 'dropload.co']
    DropLoadResolver.pattern = r'(?://|\.)(dropload\.(?:io|tv|co))/(?:embed-|e/|d/)?([0-9a-zA-Z]+)'
except Exception:
    pass

SITE_IDENTIFIER = 'filmpalast.one'
SITE_DOMAIN = 'filmpalast.one'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = '/?story=%s&do=search&subaction=search'

    def _request(self, url, referer=None):
        h = cRequestHandler(url, bypass_dns=True)
        h.addHeaderEntry('User-Agent', UA)
        if referer:
            h.addHeaderEntry('Referer', referer)
        return h.request()

    def _parse_results(self, html):
        results = []
        for block in re.findall(r'<(?:li|article)[^>]*class="[^"]*TPost[^"]*"[^>]*>(.*?)</(?:li|article)>', html, re.S | re.I):
            m_url = re.search(r'href="(https?://[^"]*filmpalast\.[^"]+/stream/[^"]+)"', block, re.I)
            m_title = re.search(r'<h3[^>]*class="[^"]*Title[^"]*"[^>]*>([^<]+)</h3>', block, re.I)
            if m_url and m_title:
                results.append((m_url.group(1), html_unescape(m_title.group(1).strip())))
        if not results:
            urls = re.findall(r'href="(https?://[^"]*filmpalast\.[^"]+/stream/[^"]+)"', html, re.I)
            titles = re.findall(r'<h3[^>]*class="[^"]*Title[^"]*"[^>]*>([^<]+)</h3>', html, re.I)
            for i, m_url in enumerate(urls):
                title = html_unescape(titles[i].strip()) if i < len(titles) else re.sub(r'/stream/\d+-(.+?)(?:-deutsch)?\.html', lambda m: m.group(1).replace('-', ' '), m_url)
                results.append((m_url, title))
        return results

    def _find_url_by_id(self, imdb):
        search_url = self.base_link + (self.search_link % urllib.parse.quote(imdb))
        data = self._request(search_url, self.base_link)
        if not data:
            return None
        results = self._parse_results(data)
        if results:
            logger.info('[Filmpalast] ID-Suche Treffer: %d' % len(results))
            return results[0][0]
        logger.info('[Filmpalast] ID-Suche kein Treffer fuer %s' % imdb)
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
                y = re.search(r'(?:Erscheinungsdatum|Jahr)[^:]*:\s*(?:</strong>)?\s*(?:\d{2}[.\-]\d{2}[.\-])?(\d{4})', page_data, re.I)
                if not y:
                    y = re.search(r'<span[^>]*class="[^"]*Date[^"]*"[^>]*>[^<]*(\d{4})', page_data, re.I)
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
            logger.info('[Filmpalast] isBlockedHoster %s -> blocked=%s res_url=%s prio=%s' % (hoster, is_blocked, res_url, prio))
            if is_blocked and not res_url:
                continue
            final_url = s_url
            can_resolve = False
            for check_url in ([s_url, res_url] if res_url and res_url != s_url else [s_url]):
                try:
                    if resolver.HostedMediaFile(url=check_url):
                        final_url = check_url
                        can_resolve = True
                        break
                except Exception:
                    pass
            if not can_resolve and is_blocked:
                logger.info('[Filmpalast] kein Resolver + blocked, skip: %s' % hoster)
                continue
            sources.append({
                'source': res_host if res_host else hoster,
                'quality': quality,
                'language': 'de',
                'url': final_url,
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
            ddl_scripts = re.findall(r'<script[^>]+src="(https://meinecloud\.click/ddl/[^"]+)"', moviecontent, re.I)
            mc_ids_done = set()
            for s_url in streams:
                if not s_url or s_url.startswith('javascript'):
                    continue
                if 'meinecloud.click' in s_url:
                    mc_match = re.search(r'meinecloud\.click/movie/(tt\d+|\d+)', s_url, re.I)
                    mc_id = mc_match.group(1) if mc_match else imdb
                    if mc_id and mc_id not in mc_ids_done:
                        mc_ids_done.add(mc_id)
                        logger.info('[Filmpalast] meinecloud ID: %s' % mc_id)
                        mc_sources = self._resolve_meinecloud(mc_id, url, quality)
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
            for ddl_src in ddl_scripts:
                mc_match = re.search(r'meinecloud\.click/ddl/(tt\d+|\d+)', ddl_src, re.I)
                if mc_match:
                    mc_id = mc_match.group(1)
                    if mc_id not in mc_ids_done:
                        mc_ids_done.add(mc_id)
                        logger.info('[Filmpalast] meinecloud DDL-Script ID: %s' % mc_id)
                        mc_sources = self._resolve_meinecloud(mc_id, url, quality)
                        sources.extend(mc_sources)
            logger.info('[Filmpalast] %d Quellen gefunden' % len(sources))
            return sources
        except Exception as e:
            logger.error('[Filmpalast] Fehler: %s' % e)
            return sources

    def resolve(self, url):
        return url
