# -*- coding: utf-8 -*-
import sys, os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..")); from resources.lib import log_utils
import json
import requests
import urllib.parse
import time
from base64 import b64encode, b64decode
import codecs
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    import xbmc
    KODI_AVAILABLE = True
except ImportError:
    KODI_AVAILABLE = False
    xbmc = None
try:
    from resources.lib import vavoosigner
except ImportError:
    vavoosigner = None

from scrapers.modules import source_utils

def create_session():
    """Erstellt neue Session mit HTTP/1.1"""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    session.verify = False

    adapter = HTTPAdapter(
        max_retries=Retry(total=0, connect=0, read=0),
        pool_connections=1,
        pool_maxsize=1
    )
    
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

BASEURL = 'https://www2.vavoo.to/ccapi/'


def log(msg, level=xbmc.LOGINFO if KODI_AVAILABLE else None):
    msg = f"[VAVOO] {msg}"
    if KODI_AVAILABLE and xbmc:
        try:
            log_utils.log(msg, level if level else xbmc.LOGINFO, xbmc.LOGDEBUG)
        except:
            log_utils.log(msg, xbmc.LOGINFO)
    else:
        log_utils.log(msg, xbmc.LOGINFO)

def log_error(msg, ex=None):
    log(f"ERROR: {msg}", xbmc.LOGERROR if KODI_AVAILABLE else None)
    if ex:
        log(f"Exception: {ex}", xbmc.LOGERROR if KODI_AVAILABLE else None)

def get_token():
    if not vavoosigner:
        log_error("vavoosigner nicht verfügbar!")
        return None
    
    try:
        token = vavoosigner.getAuthSignature()
        if token:
            log(f"Token OK (Länge: {len(token)})")
            return token
        else:
            log_error("Kein Token!")
            return None
    except Exception as e:
        log_error("Token Fehler", e)
        return None


def callApi(action, params, method='GET', headers=None, **kwargs):
    log(f"API: {action}")
    
    if not headers:
        headers = {}

    token = get_token()
    if not token:
        log_error("Kein Token!")
        return None
    
    headers['auth-token'] = token

    headers['User-Agent'] = 'VAVOO/2.6' 
    headers['Accept'] = '*/*'
    headers['Connection'] = 'close' 
    
    try:
        url = BASEURL + action

        session = create_session()
        
        log(f"Request: {method} {url}")
        log(f"Headers: {list(headers.keys())}")

        resp = session.request(
            method,
            url,
            params=params,
            headers=headers,
            timeout=10,  
            verify=False,
            allow_redirects=True,
            **kwargs
        )

        session.close()
        
        log(f"Response: {resp.status_code}")
        
        if resp.status_code == 403:
            log_error("403 Access Denied - Token ungültig?")
            log(f"Response: {resp.text[:200]}")
            return None
        
        resp.raise_for_status()
        data = resp.json()
        
        log("✓ Success")
        return data
    
    except requests.exceptions.ConnectionError as e:
        log_error(f"Connection Error: {e}")
        log("Hinweis: Server schließt Verbindung - möglicherweise WAF/Firewall")
        return None
    
    except requests.exceptions.Timeout as e:
        log_error(f"Timeout: {e}")
        return None
    
    except Exception as e:
        log_error(f"Request failed: {e}")
        return None


def callApi2(action, params, **kwargs):
    log(f"callApi2: {action}")
    
    res = callApi(action, params)
    
    if not res:
        log_error("Initial call failed")
        return None
    
    iteration = 0
    
    while True:
        iteration += 1
        
        if iteration > 10:
            log_error("Max iterations")
            return None
        
        if type(res) is not dict or 'id' not in res or 'data' not in res:
            return res
        
        data = res['data']

        if type(data) is dict and data.get('type') == 'fetch':
            log("FETCH")
            
            try:
                fetch_params = data['params']
                body = fetch_params.get('body')
                headers = fetch_params.get('headers')

                session = create_session()
                
                resp = session.request(
                    fetch_params.get('method', 'GET').upper(),
                    data['url'],
                    headers={k: v[0] if type(v) in (list, tuple) else v for k, v in headers.items()} if headers else None,
                    data=codecs.decode(body, "base64_codec") if body else None,
                    allow_redirects=fetch_params.get('redirect', 'follow') == 'follow',
                    verify=False,
                    timeout=10
                )
                
                session.close()
                
                log(f"Fetch: {resp.status_code}")
                
                resData = {
                    'status': resp.status_code,
                    'url': resp.url,
                    'headers': dict(resp.headers),
                    'data': codecs.encode(resp.content, "base64_codec").decode().replace('\n', '') if data['body'] else None
                }
                
                res = callApi('res', {'id': res['id']}, method='POST', json=resData)
                
                if not res:
                    return None
            
            except Exception as e:
                log_error("Fetch error", e)
                return None

        elif type(data) is dict and data.get('error'):
            log_error(f"API Error: {data.get('error')}")
            return None

        else:
            if isinstance(data, list):
                log(f"✓ {len(data)} items")
            return data


class source:
    
    def __init__(self):
        log("=" * 60)
        log("Vavooto Scraper (HTTP/1.1 + Connection: close)")
        log("=" * 60)
        self.priority = 1
        self.language = ['de']
        self.domains = [ 'vavoo.to']
    
    def parse_quality(self, info):
        if not info:
            return 'SD'
        info = str(info).lower()
        if '2160' in info or '4k' in info:
            return '4K'
        elif '1440' in info or '2k' in info:
            return '1440p'
        elif '1080' in info:
            return '1080p'
        elif '720' in info:
            return '720p'
        elif '480' in info:
            return '480p'
        elif '360' in info:
            return '360p'
        return 'SD'
    
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        log("=" * 60)
        log(f"RUN: {titles[0] if titles else 'N/A'} ({year}) S{season}E{episode}")
        log(f"IMDB: {imdb}")
        log("=" * 60)
        
        sources = []
        
        if not imdb:
            log_error("No IMDB")
            return sources
        
        try:
            params = {'language': 'de'}
            
            if season == 0:
                params['id'] = f'movie.{imdb}'
                log(f"FILM: {params['id']}")
            else:
                log("SERIE - IMDB->TMDB")
                
                try:
                    V2_API_KEY = '4a65e1e644af74c98f9f2b3884669deb3fac9531ee71f39babf1dee46d264d17'
                    headers = {
                        'Content-Type': 'application/json',
                        'trakt-api-key': V2_API_KEY,
                        'trakt-api-version': '2'
                    }
                    
                    result = requests.get(f'https://api.trakt.tv/shows/{imdb}', headers=headers, timeout=10, verify=False)
                    result.raise_for_status()
                    
                    tmdb_id = result.json().get('ids', {}).get('tmdb')
                    
                    if not tmdb_id:
                        log_error("No TMDB ID")
                        return sources
                    
                    log(f"✓ TMDB: {tmdb_id}")
                    params['id'] = f'series.{tmdb_id}.{season}.{episode}.de'
                
                except Exception as e:
                    log_error("TMDB failed", e)
                    return sources

            log("Getting links...")
            links = callApi2('links', params)
            
            if not links:
                log_error("No links!")
                return sources
            
            if not isinstance(links, list):
                log_error(f"Invalid type: {type(links)}")
                return sources
            
            log(f"✓ {len(links)} LINKS")

            for idx, link in enumerate(links, 1):
                try:
                    if not isinstance(link, dict):
                        continue
                    
                    url = link.get('url', '').strip()
                    if not url:
                        continue
                    
                    name = link.get('name', '')
                    quality = self.parse_quality(name)
                    
                    try:
                        hoster = urllib.parse.urlparse(url).netloc
                    except:
                        hoster = 'unknown'
                    
                    sources.append({
                        'source': hoster,
                        'quality': quality,
                        'language': link.get('language', 'de'),
                        'url': url,
                        'direct': False,
                        'debridonly': False,
                        'info': name
                    })
                    
                    if idx <= 3:
                        log(f"  [{idx}] {hoster} ({quality})")
                
                except:
                    continue
            
            log("=" * 60)
            log(f"✓ {len(sources)} SOURCES")
            log("=" * 60)
            
            return sources
        
        except Exception as e:
            log_error("run() failed", e)
            return sources
    
    def resolve(self, url):
        log(f"Resolve: {url[:60]}...")
        
        try:
            result = callApi2('open', {'link': url})
            
            if result and isinstance(result, list) and len(result) > 0:
                resolved_url = result[0].get('url')
                if resolved_url:
                    log("✓ Resolved")
                    
                    headers = result[0].get('headers', {})
                    if headers:
                        try:
                            from urlresolver.lib import helpers
                        except:
                            try:
                                from resolveurl.lib import helpers
                            except:
                                return resolved_url
                        
                        return resolved_url + helpers.append_headers(headers)
                    
                    return resolved_url
            
            return None
        
        except Exception as e:
            log_error("Resolve failed", e)
            return None
