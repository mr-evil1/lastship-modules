# -*- coding: UTF-8 -*-
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger
from resources.lib.control import getSetting, urlparse

SITE_IDENTIFIER = 'kinokiste'
SITE_DOMAIN = 'kinokiste.club'
SITE_NAME = SITE_IDENTIFIER.upper()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

DIRECT_EXTENSIONS = ('.m3u8', '.mp4', '.mkv', '.avi', '.ts')
BROKEN_HOSTERS    = ['veev.to', 'veev.cc', 'voe.sx', 'voe.to',
                     'vinovo.to', 'vinovo.si']

QUALITY_MAP = [
    ('4K',    ['4k', 'uhd', '2160']),
    ('1080p', ['1080']),
    ('720p',  ['720']),
    ('HD',    ['hd', 'web', 'webrip', 'bluray', 'bdrip', 'brrip']),
    ('HDCAM', ['hdcam']),
    ('SD',    ['sd', 'dvd', 'dvdrip']),
    ('TS',    ['ts', 'telesync', 'tc']),
    ('CAM',   ['cam']),
]
QUALITY_ORDER = ['4K', '1080p', '720p', 'HD', 'HDCAM', 'SD', 'TS', 'CAM']

def _parseQuality(raw):
    s = raw.lower()
    for label, keys in QUALITY_MAP:
        if any(k in s for k in keys):
            return label
    return raw[:20] if raw else 'SD'

def _qualityRank(q):
    try:
        return QUALITY_ORDER.index(q)
    except:
        return 99

def _isDirect(url):
    path = urlparse(url).path.lower().split('?')[0]
    return any(path.endswith(ext) for ext in DIRECT_EXTENSIONS)

def _buildKeywords(titles):
    """
    Baut alle sinnvollen Keyword-Varianten aus den übergebenen Titeln:
      - Vollständiger Titel
      - Jeder Teilbereich nach ' - ' / ' – ' (z.B. "Superman Returns" aus "Superman 5 - Superman Returns")
      - Jeder Teilbereich nach ': '
    Reihenfolge: kürzere/spezifischere Teile zuerst (landen am Ende der Liste),
    damit der erste API-Treffer der beste ist.
    Duplikate und Fragmente < 3 Zeichen werden entfernt.
    """
    seen = set()
    result = []

    def _add(kw):
        k = kw.strip()
        if len(k) < 3:
            return
        key = k.lower()
        if key not in seen:
            seen.add(key)
            result.append(k)

    for t in titles:
        if not t:
            continue
        base = re.sub(r'\s*\(\d{4}\)\s*$', '', t).strip()

        # Vollständiger Titel zuerst
        _add(base)

        # Split bei " - " und " – "
        for part in re.split(r'\s*[-–]\s*', base):
            _add(part)

        # Split bei ": "
        for part in base.split(': '):
            _add(part)

    return result


def _buildSearchTerms(titles):
    """Normalisierte Suchbegriffe für das lokale Titel-Matching."""
    seen = set()
    terms = []
    for kw in _buildKeywords(titles):
        for v in (kw.replace(' ', '').lower(), kw.lower()):
            if v not in seen:
                seen.add(v)
                terms.append(v)
    return terms


class source:
    def __init__(self):
        self.priority = 1
        self.language  = ['de']
        self.domain    = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link  = 'https://' + self.domain
        self.search_link = self.base_link + '/data/browse/?lang=2&keyword=%s&year=&order_by=&page=1&limit=20'
        self.watch_link  = self.base_link + '/data/watch/?_id=%s'
        self.sources    = []

    # ------------------------------------------------------------------ #
    def _request(self, url, cache=0):
        try:
            oRequest = cRequestHandler(url)
            oRequest.addHeaderEntry('User-Agent', UA)
            oRequest.addHeaderEntry('Referer', self.base_link + '/')
            oRequest.addHeaderEntry('Origin', self.base_link)
            oRequest.cacheTime = cache
            sResponse = oRequest.request()
            if not sResponse:
                logger.error('[%s] Leere Antwort: %s' % (SITE_NAME, url))
                return None
            return json.loads(sResponse)
        except Exception as e:
            logger.error('[%s] Request-Fehler: %s' % (SITE_NAME, str(e)))
            return None

    # ------------------------------------------------------------------ #
    def _searchOne(self, keyword, cache):
        """Führt einen einzelnen Keyword-Request durch und gibt (keyword, movies) zurück."""
        url   = self.search_link % keyword.replace(' ', '+')
        aJson = self._request(url, cache=cache)
        movies = []
        if aJson and isinstance(aJson.get('movies'), list):
            movies = aJson['movies']
        logger.debug('[%s] Keyword "%s" → %d Treffer' % (SITE_NAME, keyword, len(movies)))
        return keyword, movies

    # ------------------------------------------------------------------ #
    def _parallelSearch(self, keywords, cache=3600, max_workers=4):
        """
        Führt alle Keyword-Requests parallel aus (ThreadPoolExecutor).
        Gibt die kombinierte, deduplizierte Filmliste zurück.
        """
        all_movies = {}   # _id → movie-dict  (dedupliziert)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._searchOne, kw, cache): kw for kw in keywords}
            for future in as_completed(futures):
                try:
                    kw, movies = future.result()
                    for m in movies:
                        mid = str(m.get('_id', ''))
                        if mid and mid not in all_movies:
                            all_movies[mid] = m
                except Exception as e:
                    logger.error('[%s] Thread-Fehler: %s' % (SITE_NAME, str(e)))

        logger.info('[%s] Parallel-Suche: %d unique Eintraege aus %d Keywords' % (
            SITE_NAME, len(all_movies), len(keywords)))
        return list(all_movies.values())

    # ------------------------------------------------------------------ #
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sMainTitle = ''
        for t in titles:
            if not t:
                continue
            sMainTitle = re.sub(r'\s*\(\d{4}\)\s*$', '', t).strip()
            break

        if not sMainTitle:
            return self.sources

        keywords     = _buildKeywords(titles)
        search_terms = _buildSearchTerms(titles)

        logger.info('[%s] Suche: "%s" imdb=%s year=%s season=%s episode=%s' % (
            SITE_NAME, sMainTitle, imdb, year, season, episode))
        logger.info('[%s] Keywords (%d): %s' % (SITE_NAME, len(keywords), ' | '.join(keywords)))

        # Alle Keywords parallel anfragen
        movies = self._parallelSearch(keywords, cache=3600, max_workers=4)

        if not movies:
            logger.error('[%s] Keine API-Ergebnisse fuer "%s"' % (SITE_NAME, sMainTitle))
            return self.sources

        # ---- Matching ------------------------------------------------- #
        matches  = []
        seen_ids = set()

        for movie in movies:
            if '_id' not in movie:
                continue
            mid    = str(movie['_id'])
            if mid in seen_ids:
                continue

            sTitle   = str(movie.get('title', ''))
            isTvshow = 'Staffel' in sTitle or 'Season' in sTitle

            if season == 0 and isTvshow:
                continue
            if season != 0 and not isTvshow:
                continue

            sYear    = str(movie.get('year', ''))
            sQuality = str(movie.get('quality') or '')

            if season == 0:
                sApiBase  = re.sub(r'\s*\(\d{4}\)\s*$', '', sTitle).strip()
                sApiNsp   = sApiBase.replace(' ', '').lower()
                sApiLower = sApiBase.lower()
                # Vorwärts- UND Rückwärts-Match
                matched = any(
                    st in sApiNsp or st in sApiLower or
                    sApiNsp in st  or sApiLower in st
                    for st in search_terms
                )
                if not matched:
                    continue
                if sYear and len(sYear) == 4 and abs(int(sYear) - int(year)) > 1:
                    continue
                logger.info('[%s] Treffer: "%s" (%s)' % (SITE_NAME, sTitle, sYear))
                seen_ids.add(mid)
                matches.append((mid, sQuality))

            else:
                mSeason = re.search(r'Staffel\s+(\d+)|Season\s+(\d+)', sTitle, re.IGNORECASE)
                sSeason = (mSeason.group(1) or mSeason.group(2)) if mSeason else '1'
                sBase   = re.sub(r'\s*[-–]\s*(Staffel|Season)\s*\d+.*', '', sTitle, flags=re.IGNORECASE).strip()
                sBase   = re.sub(r'\s*\(\d{4}\)\s*$', '', sBase).strip()
                sBaseNsp   = sBase.replace(' ', '').lower()
                sBaseLower = sBase.lower()
                matched = any(
                    st in sBaseNsp or st in sBaseLower or
                    sBaseNsp in st  or sBaseLower in st
                    for st in search_terms
                )
                if matched and int(sSeason) == int(season):
                    logger.info('[%s] Serien-Treffer: "%s" S%s' % (SITE_NAME, sTitle, sSeason))
                    seen_ids.add(mid)
                    matches.append((mid, sQuality, int(sSeason)))

        logger.info('[%s] %d Match(es) gefunden' % (SITE_NAME, len(matches)))

        # ---- Streams parallel laden ------------------------------------ #
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._getStreams, m, episode, hostDict) for m in matches]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    logger.error('[%s] Stream-Thread-Fehler: %s' % (SITE_NAME, str(e)))

        return self.sources

    # ------------------------------------------------------------------ #
    def _getStreams(self, data, episode, hostDict):
        aJson = self._request(self.watch_link % data[0], cache=60 * 10)
        if not aJson or not isinstance(aJson.get('streams'), list):
            logger.error('[%s] Keine Streams fuer ID %s' % (SITE_NAME, data[0]))
            return

        sQuality = _parseQuality(data[1])
        isTvshow = len(data) > 2
        logger.info('[%s] %d Streams fuer ID %s' % (SITE_NAME, len(aJson['streams']), data[0]))

        best_per_domain = {}

        for stream in aJson['streams']:
            if isTvshow and 'e' in stream and str(stream['e']) != str(episode):
                continue
            if 'stream' not in stream:
                continue
            sUrl = stream['stream']
            if sUrl.startswith('//'):
                sUrl = 'https:' + sUrl

            sDomain = urlparse(sUrl).hostname or ''
            if not sDomain:
                continue

            if any(b in sDomain for b in BROKEN_HOSTERS):
                continue

            bDirect = _isDirect(sUrl)

            if not bDirect and hostDict:
                sDomainShort = '.'.join(sDomain.split('.')[-2:])
                if not any(sDomainShort in h or sDomain in h for h in hostDict):
                    continue

            quality = _parseQuality(str(stream['release'])) if stream.get('release') else sQuality

            if sDomain not in best_per_domain or _qualityRank(quality) < _qualityRank(best_per_domain[sDomain][1]):
                best_per_domain[sDomain] = (sUrl, quality, bDirect)

        for sDomain, (sUrl, quality, bDirect) in best_per_domain.items():
            self.sources.append({
                'source':     sDomain,
                'quality':    quality,
                'language':   'de',
                'url':        sUrl,
                'direct':     bDirect,
                'prioHoster': 0,
            })

        logger.info('[%s] %d Quellen gesamt' % (SITE_NAME, len(self.sources)))

    # ------------------------------------------------------------------ #
    def resolve(self, url):
        try:
            return url
        except:
            return
