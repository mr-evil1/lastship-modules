# -*- coding: utf-8 -*-
from resources.lib.utils import isBlockedHoster
from scrapers.modules.tools import cParser
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle
from resources.lib.control import getSetting, setSetting, urljoin
try:
    from json import loads
except:
    from simplejson import loads

SITE_IDENTIFIER = 'kkiste'
SITE_DOMAIN = 'kkiste.eu'
SITE_NAME = 'KKiste'

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.browse_link = self.base_link + '/data/browse/?lang=%s&type=%s&order_by=new&page=1&limit=0'
        self.watch_link  = self.base_link + '/data/watch/?_id=%s'

        self.hoster_priority = {
            'streamtape':  5,
            'voe':        10,
            'doodstream':  5,
            'mixdrop':     9,
            'streamwish':  8,
            'filemoon':    5,
            'vidoza':      7,
            'upstream':    5,
            'streamruby': 10,
            'vidguard':    6,
            # vom Nutzer bestätigte funktionierende Hoster
            'myvidplay':   8,
            'dsvplay':     7,
            'playmono':    7,
        }
        self.min_priority  = 1   # nur Hoster aus hoster_priority zulassen
        self.max_per_hoster = 5

    # ------------------------------------------------------------------ run --
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            from resources.lib.requestHandler import cRequestHandler
            from scrapers.modules import cleantitle
            from scrapers.modules.tools import cParser
            import re
        except:
            return []

        sources = []
        try:
            t     = set([cleantitle.get(i) for i in set(titles) if i])
            years = (year, year + 1, year - 1, 0)

            lang      = '2'
            mediaType = 'tvseries' if season > 0 else 'movies'
            searchUrl = self.browse_link % (lang, mediaType)

            oRequest = cRequestHandler(searchUrl)
            oRequest.addHeaderEntry('Referer', self.base_link + '/')
            oRequest.addHeaderEntry('Origin',  self.base_link)
            sJson = oRequest.request()
            aJson = loads(sJson)

            if 'movies' not in aJson:
                return []

            movie_id = None
            for movie in aJson['movies']:
                if '_id' not in movie:
                    continue
                sTitle = str(movie.get('title', ''))
                sYear  = movie.get('year', 0)

                if season == 0:
                    if 'Staffel' in sTitle or 'Season' in sTitle:
                        continue
                    if cleantitle.get(sTitle) in t and int(sYear) in years:
                        movie_id = str(movie['_id'])
                        break
                else:
                    if ' - ' not in sTitle:
                        continue
                    sSeriesTitle = sTitle.split(' - ')[0].strip()
                    if cleantitle.get(sSeriesTitle) in t:
                        sm = re.search(r'Staffel\s+(\d+)|Season\s+(\d+)', sTitle, re.IGNORECASE)
                        if sm and int(sm.group(1) or sm.group(2)) == season:
                            movie_id = str(movie['_id'])
                            break

            if not movie_id:
                return []

            watchUrl = self.watch_link % movie_id
            oRequest = cRequestHandler(watchUrl)
            oRequest.addHeaderEntry('Referer', self.base_link + '/')
            oRequest.addHeaderEntry('Origin',  self.base_link)
            sJson = oRequest.request()
            aJson = loads(sJson)

            if 'streams' not in aJson:
                return []

            hoster_count = {}
            for stream in aJson['streams']:
                if season > 0:
                    if 'e' not in stream or int(stream['e']) != episode:
                        continue
                if 'stream' not in stream:
                    continue

                sUrl = stream['stream']
                if 'youtube' in sUrl.lower() or 'vod' in sUrl.lower():
                    continue

                # FIX: URL-Prefix korrekt aufloesen
                if sUrl.startswith('//'):
                    sUrl = 'https:' + sUrl
                elif sUrl.startswith('/'):
                    sUrl = self.base_link + sUrl  # war: 'https:/' + sUrl

                isMatch, aName = cParser.parse(sUrl, '//([^/]+)/')
                if not isMatch:
                    continue

                sName = aName[0]
                if '.' in sName:
                    sName = sName[:sName.rindex('.')]

                priority = 0
                for hoster, prio in self.hoster_priority.items():
                    if hoster in sName.lower():
                        priority = prio
                        break

                if priority < self.min_priority:
                    continue

                hoster_key = sName.lower()
                hoster_count.setdefault(hoster_key, 0)
                if hoster_count[hoster_key] >= self.max_per_hoster:
                    continue
                hoster_count[hoster_key] += 1

                quality = 'HD'
                if 'release' in stream and stream['release']:
                    release = str(stream['release']).upper()
                    if 'CAM' in release or 'TS' in release:
                        quality = 'CAM'
                    elif 'SD' in release:
                        quality = 'SD'

                sources.append({
                    'source':     sName,
                    'quality':    quality,
                    'language':   'de',
                    'url':        sUrl,
                    'direct':     False,
                    'debridonly': False,
                    'priority':   priority,
                })

            sources = sorted(sources, key=lambda x: x.get('priority', 0), reverse=True)
            return sources
        except:
            return []

    # --------------------------------------------------------------- resolve --
    def resolve(self, url):
        """
        Wird vom Framework aufgerufen bevor der eigene URL-Resolver greift.
        Gibt eine direkte Video-URL zurueck → Framework muss nichts mehr tun.
        Gibt die originale URL zurueck   → Framework-Resolver uebernimmt
        (Fallback fuer streamtape/streamruby, die dort funktionieren).
        """
        try:
            low = url.lower()
            if 'voe.sx' in low or ('voe' in low and '/e/' in low):
                return self._resolve_voe(url)
            if 'mixdrop' in low:
                return self._resolve_mixdrop(url)
            if any(x in low for x in ('streamwish', 'wishfast', 'swdyu', 'sfastwish', 'moviesm4u', 'streamwi')):
                return self._resolve_streamwish(url)
            if any(x in low for x in ('dood', 'doodstream', 'dooood')):
                return self._resolve_dood(url)
            if 'vidoza' in low:
                return self._resolve_vidoza(url)
            if any(x in low for x in ('vidguard', 'listeamed', 'bembed', 'v6embed')):
                return self._resolve_vidguard(url)
            if 'filemoon' in low or 'moonembed' in low:
                return self._resolve_filemoon(url)
        except:
            pass
        return url

    # ------------------------------------------- parallele Hoster-Prüfung --

    _CHECK_WORKERS = 8   # gleichzeitige Threads
    _CHECK_TIMEOUT = 5   # Sekunden pro Request

    def _check_url(self, url):
        """
        Prüft ob eine Hoster-URL erreichbar ist.
        HEAD-Request zuerst; bei 405 (Method Not Allowed) GET-Fallback mit
        Range-Header, damit nur wenige Bytes übertragen werden.
        Gibt True zurück wenn HTTP-Status < 400, sonst False.
        """
        try:
            import urllib.request
            import urllib.error
            headers = {
                'User-Agent': self._UA,
                'Referer':    url,
            }
            # 1. Versuch: HEAD (kein Body-Download)
            req = urllib.request.Request(url, method='HEAD')
            for k, v in headers.items():
                req.add_header(k, v)
            try:
                with urllib.request.urlopen(req, timeout=self._CHECK_TIMEOUT) as r:
                    return r.status < 400
            except urllib.error.HTTPError as e:
                if e.code != 405:
                    return False   # echter Fehler (403, 404, 410, …)
            # 2. Versuch: GET mit Range (HEAD nicht erlaubt)
            req2 = urllib.request.Request(url)
            for k, v in headers.items():
                req2.add_header(k, v)
            req2.add_header('Range', 'bytes=0-1023')
            with urllib.request.urlopen(req2, timeout=self._CHECK_TIMEOUT) as r:
                return r.status in (200, 206)
        except Exception:
            return False

    def _filter_live_sources(self, sources):
        """
        Filtert nicht erreichbare Hoster-URLs parallel heraus (HTTP-Check).
        Reihenfolge (Priority-Sort) bleibt erhalten.
        Unbekannte Hoster (priority=0) wurden bereits in run() durch
        min_priority=1 ausgeschlossen — hier kommen nur noch bekannte an.
        """
        if not sources:
            return sources
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            results = {}
            with ThreadPoolExecutor(max_workers=self._CHECK_WORKERS) as pool:
                futures = {
                    pool.submit(self._check_url, s['url']): i
                    for i, s in enumerate(sources)
                }
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        results[idx] = future.result()
                    except Exception:
                        results[idx] = False

            return [s for i, s in enumerate(sources) if results.get(i, False)]
        except Exception:
            return sources

    # -------------------------------------------------- hoster-spezifisch --

    _UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

    def _fetch(self, url, referer=None):
        oReq = cRequestHandler(url)
        oReq.addHeaderEntry('User-Agent', self._UA)
        if referer:
            oReq.addHeaderEntry('Referer', referer)
        return oReq.request() or ''

    def _resolve_voe(self, url):
        import re, base64
        html = self._fetch(url)

        # Direktes HLS-Objekt im JS
        for pat in [
            r"'hls'\s*:\s*'(https?://[^']+)'",
            r'"hls"\s*:\s*"(https?://[^"]+)"',
            r"hls\s*:\s*['\"]([^'\"]+\.m3u8[^'\"]*)['\"]",
        ]:
            m = re.search(pat, html)
            if m:
                return m.group(1)

        # atob("base64") Variante
        m = re.search(r'atob\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)', html)
        if m:
            try:
                decoded = base64.b64decode(m.group(1)).decode('utf-8')
                m2 = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', decoded)
                if m2:
                    return m2.group(1)
            except:
                pass

        # Reversed-base64 Variante (VOE kodiert manchmal rueckwaerts)
        for m in re.finditer(r'["\']([A-Za-z0-9+/=]{60,})["\']', html):
            try:
                decoded = base64.b64decode(m.group(1)[::-1]).decode('utf-8')
                if '.m3u8' in decoded:
                    m2 = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', decoded)
                    if m2:
                        return m2.group(1)
            except:
                continue

        return url

    def _resolve_mixdrop(self, url):
        import re
        html = self._fetch(url)

        # MDCore.wurl (neuere Variante)
        m = re.search(r'MDCore\.wurl\s*=\s*"([^"]+)"', html)
        if m:
            src = m.group(1)
            return ('https:' + src) if src.startswith('//') else src

        # MDCore.ref + MDCore.orig (aeltere Variante)
        ref  = re.search(r'MDCore\.ref\s*=\s*"([^"]+)"',  html)
        orig = re.search(r'MDCore\.orig\s*=\s*"([^"]+)"', html)
        if ref and orig:
            src = orig.group(1) + ref.group(1)
            return ('https:' + src) if src.startswith('//') else src

        return url

    def _resolve_streamwish(self, url):
        import re
        html = self._fetch(url, referer=url)

        for pat in [
            r'file\s*:\s*"(https?://[^"]+\.m3u8[^"]*)"',
            r"file\s*:\s*'(https?://[^']+\.m3u8[^']*)'",
            r'file\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            r'source\s+src=["\']?(https?://[^"\'>\s]+\.m3u8[^"\'>\s]*)',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return m.group(1)

        return url

    def _resolve_dood(self, url):
        import re, time, random, string
        html = self._fetch(url)

        m = re.search(r'/pass_md5/([^\'\"?\s]+)', html)
        if not m:
            return url

        base_domain = re.search(r'(https?://[^/]+)', url)
        if not base_domain:
            return url

        pass_url = base_domain.group(1) + '/pass_md5/' + m.group(1)
        base = self._fetch(pass_url, referer=url)

        if base and base.startswith('http'):
            rand  = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            token = m.group(1).split('/')[-1]
            return '{}{}&token={}&expiry={}'.format(
                base, rand, token, int(time.time() * 1000)
            )

        return url

    def _resolve_vidoza(self, url):
        import re
        html = self._fetch(url)

        for pat in [
            r'sourcesCode\s*:\s*\[.*?"src"\s*:\s*"(https?://[^"]+)"',
            r'"src"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"',
            r"'src'\s*:\s*'(https?://[^']+\.mp4[^']*)'",
            r'source\s+src=["\']?(https?://[^"\'>\s]+\.mp4[^"\'>\s]*)',
        ]:
            m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
            if m:
                return m.group(1)

        return url

    def _resolve_vidguard(self, url):
        import re, base64
        html = self._fetch(url)

        # Neuere VidGuard: _0x... obfuskiertes JS mit atob
        m = re.search(r'atob\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)', html)
        if m:
            try:
                decoded = base64.b64decode(m.group(1)).decode('utf-8')
                m2 = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', decoded)
                if m2:
                    return m2.group(1)
            except:
                pass

        # Direktes source-Tag
        m = re.search(r'source\s+src=["\']?(https?://[^"\'>\s]+\.m3u8[^"\'>\s]*)', html)
        if m:
            return m.group(1)

        return url

    def _resolve_filemoon(self, url):
        import re, base64
        html = self._fetch(url)

        # Filemoon nutzt eval(atob(...)) oder direkte jwplayer-sources
        for pat in [
            r'file\s*:\s*"(https?://[^"]+\.m3u8[^"]*)"',
            r"file\s*:\s*'(https?://[^']+\.m3u8[^']*)'",
        ]:
            m = re.search(pat, html)
            if m:
                return m.group(1)

        m = re.search(r'eval\(atob\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)\)', html)
        if m:
            try:
                decoded = base64.b64decode(m.group(1)).decode('utf-8')
                m2 = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', decoded)
                if m2:
                    return m2.group(1)
            except:
                pass

        return url
