# -*- coding: UTF-8 -*-
import re
import gzip
import http.cookiejar
import urllib.request
import urllib.parse
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting
from resources.lib.tools import logger
from scrapers.modules import cleantitle

SITE_IDENTIFIER = 'movie2k2'
SITE_DOMAIN = 'movie2k.cx'
SITE_NAME = 'Movie2k2'

_STOP_WORDS = {'der', 'die', 'das', 'ein', 'eine', 'the', 'a', 'an', 'les', 'le', 'la', 'de', 'di', 'und', 'and'}

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = self.base_link + '/search?q=%s'
        self.ua = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/30.0 Chrome/143.0.0.0 Mobile Safari/537.36'
        self._opener = None

    def _get_opener(self):
        if self._opener is not None:
            return self._opener
        try:
            cj = http.cookiejar.CookieJar()
            self._opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(cj),
                urllib.request.HTTPSHandler()
            )
            self._opener.addheaders = [
                ('User-Agent', self.ua),
                ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'),
                ('Accept-Language', 'de-AT,de-DE;q=0.9,de;q=0.8,en-US;q=0.7,en;q=0.6'),
                ('Accept-Encoding', 'gzip, deflate'),
                ('sec-ch-ua', '"Samsung Internet";v="30.0", "Chromium";v="143", "Not A(Brand";v="24"'),
                ('sec-ch-ua-mobile', '?1'),
                ('sec-ch-ua-platform', '"Android"'),
                ('sec-fetch-dest', 'document'),
                ('sec-fetch-mode', 'navigate'),
                ('sec-fetch-site', 'same-origin'),
                ('sec-fetch-user', '?1'),
                ('upgrade-insecure-requests', '1'),
            ]
            self._opener.open(self.base_link, timeout=10)
            logger.info('Load %s - Session initialisiert (%d Cookies)' % (SITE_NAME, len(list(cj))))
        except Exception as ex:
            logger.info('Load %s - Session-Init fehlgeschlagen: %s' % (SITE_NAME, str(ex)))
            self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
            self._opener.addheaders = [
                ('User-Agent', self.ua),
                ('Accept-Encoding', 'gzip, deflate'),
            ]
        return self._opener

    def _fetch(self, url, referer=None):
        """HTTP-GET mit Session-Cookies und automatischer gzip-Dekomprimierung."""
        try:
            opener = self._get_opener()
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.ua)
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Referer', referer or self.base_link)
            req.add_header('sec-fetch-dest', 'document')
            req.add_header('sec-fetch-mode', 'navigate')
            req.add_header('sec-fetch-site', 'same-origin')
            with opener.open(req, timeout=15) as resp:
                raw = resp.read()
                encoding = resp.headers.get('Content-Encoding', '')
            if encoding == 'gzip':
                raw = gzip.decompress(raw)
            elif encoding == 'deflate':
                import zlib
                raw = zlib.decompress(raw)
            try:
                html = raw.decode('utf-8')
            except UnicodeDecodeError:
                html = raw.decode('latin-1', errors='replace')
            return html
        except Exception as ex:
            logger.info('Load %s - Fetch-Fehler %s: %s' % (SITE_NAME, url, str(ex)))
            return None

    @staticmethod
    def _titles_match(target_clean, name_clean):
        if target_clean in name_clean or name_clean in target_clean:
            return True
        def strip(s):
            s = re.sub(r'^(the|der|die|das|ein|eine|le|la|les|de|il)\s*', '', s)
            s = re.sub(r'\s*(film|movie|serie|serien|special|show)$', '', s)
            return s.strip()
        t = strip(target_clean)
        n = strip(name_clean)
        if t and n and (t in n or n in t):
            return True
        t_words = set(t.split())
        n_words = set(n.split())
        if t_words and n_words:
            overlap = len(t_words & n_words)
            ratio = overlap / min(len(t_words), len(n_words))
            if ratio >= 0.6:
                return True
        return False

    def run(self, titles, year, season=0, episode=0, imdb=''):
        sources = []
        links = self.search(titles, year, season, episode, imdb)
        if not links:
            logger.info('Load %s - No links found' % SITE_NAME)
            return []

        for url in links:
            try:
                html = self._fetch(url, referer=self.base_link)
                if not html:
                    continue

                aResult = re.findall(
                    r'<option\s+value\s*=\s*"([^"]+)"[^>]*data-quality\s*=\s*"([^"]*)"[^>]*>\s*([^<]+?)\s*</option>',
                    html, re.IGNORECASE
                )
                if not aResult:
                    raw2 = re.findall(
                        r'<option\s+value\s*=\s*"(https?://[^"]+)"[^>]*>\s*([^<(]+?)\s*</option>',
                        html, re.IGNORECASE
                    )
                    aResult = [(u, '', n) for u, n in raw2]

                for sUrl, sQuality, sName in aResult:
                    if not sUrl:
                        continue
                    q = sQuality.lower()
                    sNameLow = sName.lower()
                    if '2160' in q or '4k' in q:
                        quality = '4K'
                    elif '1080' in q or '1080' in sNameLow:
                        quality = '1080p'
                    elif '720' in q or '720' in sNameLow:
                        quality = '720p'
                    elif q == 'hd' or '(hd)' in sNameLow:
                        quality = 'HD'
                    elif '480' in q or '480' in sNameLow:
                        quality = '480p'
                    else:
                        quality = 'SD'

                    isBlocked, hoster, sFinalUrl, prioHoster = isBlockedHoster(sUrl)
                    if isBlocked:
                        continue

                    hoster_name = hoster or re.sub(r'\s*\(.*?\)', '', sName).strip()
                    sources.append({
                        'source': hoster_name,
                        'quality': quality,
                        'language': 'de',
                        'url': sFinalUrl,
                        'direct': False,
                        'prioHoster': prioHoster
                    })
            except Exception as ex:
                logger.info('Load %s - Fehler beim Parsen %s: %s' % (SITE_NAME, url, str(ex)))

        return sources

    def search(self, titles, year, season, episode, imdb=''):
        for title in titles:
            try:
                stream_url = self._find_stream_url(title, imdb)
                if not stream_url:
                    continue
                if season > 0:
                    stream_url = '%s?type=series&season=%s&episode=%s' % (stream_url, season, episode)
                logger.info('Load %s - Stream page: %s' % (SITE_NAME, stream_url))
                return [stream_url]
            except Exception as ex:
                logger.info('Load %s - Search error: %s' % (SITE_NAME, str(ex)))
        return []

    def _find_stream_url(self, title, imdb=''):
        keywords = self._build_keywords(title)
        for kw in keywords:
            html = self._fetch_search(kw)
            if not html:
                continue
            if '(0 gefunden)' in html:
                logger.info('Load %s - 0 Treffer: %s' % (SITE_NAME, kw))
                continue

            links = re.findall(
                r'href\s*=\s*"(/stream/[^"]+)"[^>]*>\s*([^\n<]+?)\s*<',
                html, re.IGNORECASE
            )
            if not links:
                logger.info('Load %s - Kein /stream/-Link im HTML für: %s (HTML-Länge=%d, Snippet=%s)' % (
                    SITE_NAME, kw, len(html), repr(html[2000:2200]) if len(html) > 2000 else repr(html[:200])))
                continue

            target_clean = cleantitle.get(title)
            for sPath, sName in links:
                sName = sName.strip()
                if not sName:
                    continue
                name_clean = cleantitle.get(sName)
                if not name_clean:
                    continue
                if self._titles_match(target_clean, name_clean):
                    full_url = self.base_link + sPath
                    if imdb and not self._verify_imdb(full_url, imdb):
                        logger.info('Load %s - IMDB-Mismatch: %s' % (SITE_NAME, sName))
                        continue
                    logger.info('Load %s - Match: "%s" → "%s"' % (SITE_NAME, title, sName))
                    return full_url
            found_names = [n.strip() for _, n in links[:5]]
            logger.info('Load %s - Kein Titel-Match für "%s". Gefunden: %s' % (SITE_NAME, title, found_names))
        return None

    def _build_keywords(self, title):
        words = [w for w in title.split() if w.lower() not in _STOP_WORDS and len(w) > 2]
        keywords = []
        if len(words) >= 3:
            keywords.append(' '.join(words[:3]))
        if len(words) >= 2:
            keywords.append(' '.join(words[:2]))
        if words:
            keywords.append(words[0])
        if not keywords:
            keywords.append(title)
        seen = []
        for k in keywords:
            if k not in seen:
                seen.append(k)
        return seen

    def _fetch_search(self, keyword):
        url = self.search_link % urllib.parse.quote(keyword)
        logger.info('Load %s - Search: %s' % (SITE_NAME, url))
        return self._fetch(url, referer=self.base_link)

    def _verify_imdb(self, stream_url, imdb):
        try:
            html = self._fetch(stream_url)
            if not html:
                return True
            found = re.search(r'imdb\.com/title/(tt\d+)', html)
            if found:
                return found.group(1) == imdb
            return True
        except Exception:
            return True

    def resolve(self, url):
        return url
