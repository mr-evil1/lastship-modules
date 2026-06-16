# -*- coding: utf-8 -*-

import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import xbmc
    KODI_AVAILABLE = True
except ImportError:
    KODI_AVAILABLE = False
    xbmc = None

from scrapers.modules import source_utils

BASE_URL     = 'https://vavoo.to'
URL_ITEM     = BASE_URL + '/mediahubmx-item.json'
URL_SOURCE   = BASE_URL + '/mediahubmx-source.json'
URL_RESOLVE  = BASE_URL + '/mediahubmx-resolve.json'
PING_URL     = 'https://www.vavoo.tv/api/app/ping'
APP_VERSION  = '4.2.2'
APP_PACKAGE  = 'tv.vavoo.app'
DOMAIN       = 'vavoo.to'

import os, time as _time_, json as _json_

try:
    import xbmcvfs as _xbmcvfs_
    _CACHE_DIR = xbmc.translatePath('special://temp/')
except Exception:
    _CACHE_DIR = ''

if not _CACHE_DIR or not os.path.isdir(_CACHE_DIR):
    for _d in [
        os.path.expanduser('~'),
        os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '',
    ]:
        if _d and os.path.isdir(_d) and os.access(_d, os.W_OK):
            _CACHE_DIR = _d
            break
    else:
        _CACHE_DIR = '/tmp/'

_SIG_CACHE_FILE = os.path.join(_CACHE_DIR, '.vavoo_sig_vavoo.py')
_UUID_FILE      = os.path.join(_CACHE_DIR, '.vavoo_device_id')
_SIG_TTL        = 840


def log(msg, level='DEBUG'):
    _lvl = xbmc.LOGDEBUG if level == 'DEBUG' else xbmc.LOGERROR if level == 'ERROR' else xbmc.LOGINFO
    try:
        xbmc.log(f'[Vavoo] {msg}', _lvl)
    except Exception:
        print(f'[Vavoo][{level}] {msg}')


def _get_uuid():
    log(f'UUID-Datei: {_UUID_FILE}')
    if os.path.isfile(_UUID_FILE):
        _c = open(_UUID_FILE).read().strip()
        import re
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', _c, re.I):
            log(f'UUID aus Cache: {_c}')
            return _c
        log('UUID-Datei ungültig, generiere neu')
    else:
        log('UUID-Datei nicht gefunden, generiere neu')

    b = bytearray(os.urandom(16))
    b[6] = (b[6] & 0x0f) | 0x40
    b[8] = (b[8] & 0x3f) | 0x80
    h = b.hex()
    _id = f'{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}'
    try:
        open(_UUID_FILE, 'w').write(_id + '\n')
        log(f'UUID gespeichert: {_id}')
    except Exception as e:
        log(f'UUID speichern fehlgeschlagen: {e}', 'ERROR')
    return _id


def getAuthSignature(force=False):
    log(f'getAuthSignature() force={force}')
    log(f'Cache-Dir: {_CACHE_DIR}')
    log(f'Sig-Cache-Datei: {_SIG_CACHE_FILE}')

    if not force and os.path.isfile(_SIG_CACHE_FILE):
        _age = _time_.time() - os.path.getmtime(_SIG_CACHE_FILE)
        log(f'Sig-Cache gefunden, Alter: {int(_age)}s (TTL={_SIG_TTL}s)')
        if _age < _SIG_TTL:
            _sig = open(_SIG_CACHE_FILE).read().strip()
            if _sig:
                log(f'Sig aus Cache: {_sig[:30]}...')
                return _sig
            log('Sig-Cache leer')
        else:
            log('Sig-Cache abgelaufen')
    else:
        log('Kein Sig-Cache vorhanden, hole neu')

    _ts  = int(_time_.time() * 1000)
    _uid = _get_uuid()
    log(f'Ping an {PING_URL} mit UUID={_uid}')

    _headers = {
        'User-Agent':   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) vavoo/4.2.2 Chrome/146.0.7680.166 Electron/41.1.0 Safari/537.36',
        'Accept':       '*/*',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin':       'https://vavoo.to',
        'Referer':      'https://vavoo.to/',
        'Connection':   'keep-alive',
        'Content-Type': 'application/json',
    }
    _data = {
        'reason': 'app-focus',
        'locale': 'de',
        'theme':  'dark',
        'metadata': {
            'device': {'type': 'desktop', 'uniqueId': _uid},
            'os':     {'name': 'linux', 'version': 'x86_64', 'abis': ['x64'], 'host': 'localhost'},
            'app':    {'platform': 'electron'},
            'version':{'package': APP_PACKAGE, 'binary': APP_VERSION, 'js': APP_VERSION},
        },
        'appFocusTime': 0, 'playerActive': False, 'playDuration': 0,
        'devMode': False, 'hasAddon': True, 'castConnected': False,
        'package': APP_PACKAGE, 'version': APP_VERSION, 'process': 'app',
        'firstAppStart': _ts, 'lastAppStart': _ts,
        'ipLocation': None, 'adblockEnabled': True,
        'proxy': {'supported': ['ss'], 'engine': 'Mu', 'enabled': False, 'autoServer': True},
        'iap': {'supported': False},
    }
    try:
        resp = requests.post(PING_URL, json=_data, headers=_headers, timeout=10, verify=False)
        log(f'Ping HTTP-Status: {resp.status_code}')
        rjson = resp.json()
        log(f'Ping Response Keys: {list(rjson.keys())}')
        sig = rjson.get('addonSig', '')
        if sig:
            log(f'addonSig erhalten: {sig[:30]}...')
            try:
                open(_SIG_CACHE_FILE, 'w').write(sig)
                log('Sig in Cache gespeichert')
            except Exception as e:
                log(f'Sig-Cache speichern fehlgeschlagen: {e}', 'ERROR')
        else:
            log('addonSig fehlt in Ping-Response!', 'ERROR')
            log(f'Volle Response: {str(rjson)[:300]}', 'ERROR')
        return sig
    except Exception as e:
        log(f'Ping fehlgeschlagen: {e}', 'ERROR')
        if os.path.isfile(_SIG_CACHE_FILE):
            _sig = open(_SIG_CACHE_FILE).read().strip()
            log(f'Fallback auf alten Sig-Cache: {_sig[:30]}...')
            return _sig
        return None


def _get_headers(signature=None):
    h = {
        'user-agent':      'MediaHubMX/2',
        'content-type':    'application/json; charset=utf-8',
        'accept-encoding': 'gzip',
    }
    if signature:
        h['mediahubmx-signature'] = signature
    return h


def _base_payload():
    return {'language': 'de', 'region': 'AT', 'clientVersion': '3.1.0'}


def get_media_data(titles, year, season=0, episode=0, imdb=''):
    log(f'get_media_data() imdb={imdb} season={season} episode={episode}')
    log(f'titles Typ: {type(titles).__name__} | Wert: {str(titles)[:200]}')
    try:
        mediatype = 'movie' if season == 0 else 'series'

        if isinstance(titles, dict):
            tmdb_id   = str(titles.get('tmdb_id') or titles.get('tmdb') or '')
            item_name = titles.get('title') or titles.get('originaltitle') or ''
            imdb      = imdb or titles.get('imdb_id') or titles.get('imdbnumber') or ''
        else:
            tmdb_id   = ''
            item_name = titles[0] if isinstance(titles, list) and titles else str(titles)

        ids = {}
        if tmdb_id:
            ids['tmdb_id'] = tmdb_id
            log(f'IDs aus titles-Dict: tmdb_id={tmdb_id}')
        if imdb:
            ids['imdb_id'] = imdb
            log(f'imdb_id={imdb}')

        if not ids:
            log('Weder tmdb_id noch imdb_id verfügbar, abbruch!', 'ERROR')
            return None

        sig = getAuthSignature()
        if not sig:
            log('Keine Signature vorhanden!', 'ERROR')
            return None
        log(f'Signature OK: {sig[:30]}...')

        headers = _get_headers(sig)

        item_payload = _base_payload()
        item_payload.update({
            'type':    mediatype,
            'ids':     ids,
            'name':    item_name,
            'episode': {} if season == 0 else {'season': season, 'episode': episode},
        })
        log(f'POST {URL_ITEM} ids={ids} name={item_name}')
        item_resp = requests.post(URL_ITEM, json=item_payload, headers=headers, timeout=15, verify=False)
        log(f'item.json HTTP-Status: {item_resp.status_code}')

        if item_resp.status_code == 200 and isinstance(item_resp.json(), dict):
            source_payload = item_resp.json()
            source_payload['language']      = 'de'
            source_payload['region']        = 'AT'
            source_payload['clientVersion'] = '3.1.0'
            log(f'item.json OK, IDs: {source_payload.get("ids")}')
        else:
            log(f'item.json Fehler ({item_resp.status_code}), Fallback auf item_payload', 'ERROR')
            source_payload = item_payload

        log(f'POST {URL_SOURCE}')
        source_resp = requests.post(URL_SOURCE, json=source_payload, headers=headers, timeout=15, verify=False)
        log(f'source.json HTTP-Status: {source_resp.status_code}')

        if source_resp.status_code != 200:
            log(f'source.json Fehler: {source_resp.text[:200]}', 'ERROR')
            return None

        result = source_resp.json()
        if isinstance(result, list):
            log(f'source.json liefert {len(result)} Einträge')
            for idx, r in enumerate(result[:5]):
                log(f'  [{idx}] name={r.get("name")} lang={r.get("languages")} tag={r.get("tag")} url={str(r.get("url",""))[:60]}')
        else:
            log(f'source.json unerwartetes Format: {type(result)} | {str(result)[:200]}', 'ERROR')
            return None

        return result

    except Exception as e:
        log(f'get_media_data Exception: {e}', 'ERROR')
        import traceback
        log(traceback.format_exc(), 'ERROR')
        return None


def resolve_stream_url(stream_url, sig=None):
    log(f'resolve_stream_url() url={stream_url[:80]}')
    try:
        if sig is None:
            sig = getAuthSignature()
        headers = _get_headers(sig)

        payload = _base_payload()
        payload['url'] = stream_url

        log(f'POST {URL_RESOLVE}')
        resp = requests.post(URL_RESOLVE, json=payload, headers=headers, timeout=15, verify=False)
        log(f'resolve.json HTTP-Status: {resp.status_code}')

        if resp.status_code != 200:
            log(f'resolve.json Fehler: {resp.text[:200]}', 'ERROR')
            return None

        data = resp.json()
        log(f'resolve.json Response-Typ: {type(data).__name__}')

        if isinstance(data, dict):
            url = data.get('url') or data.get('data', {}).get('url')
            log(f'resolve URL (dict): {str(url)[:80]}')
            return url
        if isinstance(data, list) and data:
            url = data[0].get('url')
            log(f'resolve URL (list[0]): {str(url)[:80]}')
            return url

        log('resolve.json: keine URL gefunden!', 'ERROR')
        return None

    except Exception as e:
        log(f'resolve_stream_url Exception: {e}', 'ERROR')
        import traceback
        log(traceback.format_exc(), 'ERROR')
        return None


def is_blocked_hoster(url):
    if not url:
        return True, 'Unknown', None, False

    blocked_hosters = ['openload', 'streamango', 'verystream', 'vshare', 'thevideo', 'vidtodo']

    hoster = 'Unknown'
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        if 'streamtape' in domain:   hoster = 'Streamtape'
        elif 'dood'     in domain:   hoster = 'Doodstream'
        elif 'vidoza'   in domain:   hoster = 'Vidoza'
        elif 'mixdrop'  in domain:   hoster = 'Mixdrop'
        elif 'supervideo' in domain: hoster = 'Supervideo'
        elif 'luluvideo' in domain:  hoster = 'Luluvideo'
        elif 'voe'      in domain:   hoster = 'Voe'
        elif 'filemoon' in domain:   hoster = 'Filemoon'
        elif 'upstream' in domain:   hoster = 'Upstream'
        elif 'veev'     in domain:   hoster = 'Veev'
        elif 'vidsonic' in domain:   hoster = 'Vidsonic'
        else:
            parts = domain.split('.')
            hoster = parts[-2].capitalize() if len(parts) >= 2 else domain.capitalize()
    except Exception:
        pass

    is_blocked  = any(b in url.lower() for b in blocked_hosters)
    prio_hosters = ['Streamtape', 'Doodstream', 'Voe', 'Filemoon', 'Veev']
    prio_hoster  = hoster in prio_hosters

    return is_blocked, hoster, url, prio_hoster


def parse_quality(tag, stream_url):
    tag      = (tag or '').lower()
    url_low  = (stream_url or '').lower()
    if   '4k'   in tag or '2160' in tag or '4k'   in url_low: return '4K'
    elif '1440' in tag or '2k'   in tag or '1440' in url_low: return '1440p'
    elif '1080' in tag or '800'  in tag or '1080' in url_low: return '1080p'
    elif '720'  in tag or '720'  in url_low:                   return '720p'
    elif '480'  in tag or '480'  in url_low:                   return '480p'
    elif '360'  in tag or '360'  in url_low:                   return '360p'
    return 'SD'


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains  = [DOMAIN]
        self.sources  = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        self.sources = []
        log(f'=== run() START imdb={imdb} titles={titles} year={year} season={season} episode={episode} ===')

        if not imdb:
            log('Keine IMDB-ID übergeben, abbruch', 'ERROR')
            return self.sources

        try:
            sig = getAuthSignature()
            log(f'Signature nach getAuthSignature: {"OK" if sig else "FEHLT"}')

            mirrors = get_media_data(titles, year, season, episode, imdb)
            log(f'get_media_data Ergebnis: {len(mirrors) if mirrors else 0} Einträge')

            if not mirrors:
                log('Keine Mirrors gefunden, abbruch')
                return self.sources

            de_count = sum(1 for i in mirrors if isinstance(i, dict) and 'de' in i.get('languages', []))
            log(f'Davon mit Sprache DE: {de_count}')

            for idx, i in enumerate(mirrors):
                try:
                    if not isinstance(i, dict):
                        log(f'  [{idx}] kein dict, übersprungen')
                        continue

                    langs = i.get('languages', [])
                    if 'de' not in langs:
                        log(f'  [{idx}] {i.get("name")} | Sprache={langs} → übersprungen (kein DE)')
                        continue

                    stream_url = i.get('url')
                    if not stream_url:
                        log(f'  [{idx}] {i.get("name")} | keine URL, übersprungen')
                        continue

                    log(f'  [{idx}] {i.get("name")} | {langs} | {i.get("tag")} → resolve...')
                    resolved_url = resolve_stream_url(stream_url, sig)

                    if not resolved_url:
                        log(f'  [{idx}] resolve fehlgeschlagen!', 'ERROR')
                        continue

                    is_blocked, hoster, sUrl, prio_hoster = is_blocked_hoster(resolved_url)
                    log(f'  [{idx}] Hoster={hoster} blocked={is_blocked} prio={prio_hoster}')

                    if is_blocked or not sUrl:
                        log(f'  [{idx}] Hoster blockiert oder URL leer, übersprungen')
                        continue

                    quality = parse_quality(i.get('tag', ''), resolved_url)
                    log(f'  [{idx}] → HINZUGEFÜGT: {hoster} {quality}')

                    self.sources.append({
                        'source':      hoster,
                        'quality':     quality,
                        'language':    'de',
                        'url':         sUrl,
                        'direct':      True,
                        'debridonly':  False,
                        'info':        f'Vavoo_{quality}',
                    })

                except Exception as e:
                    log(f'  [{idx}] Fehler: {e}', 'ERROR')
                    continue

        except Exception as e:
            log(f'run() Exception: {e}', 'ERROR')
            import traceback
            log(traceback.format_exc(), 'ERROR')

        log(f'=== run() END: {len(self.sources)} Quellen gefunden ===')
        return self.sources

    def resolve(self, url):
        log(f'resolve() url={url[:80]}')
        try:
            resolved = resolve_stream_url(url)
            if resolved:
                log(f'resolve() → {resolved[:80]}')
                return resolved
            log('resolve() via Direktabruf...')
            resp = requests.get(
                url,
                headers={'Referer': f'https://{DOMAIN}/', 'Origin': f'https://{DOMAIN}', 'User-Agent': 'Mozilla/5.0'},
                timeout=10, verify=False, allow_redirects=True
            )
            log(f'resolve() Direktabruf → {resp.url[:80]}')
            return resp.url
        except Exception as e:
            log(f'resolve() Exception: {e}', 'ERROR')
            return None
