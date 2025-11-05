# -*- coding: utf-8 -*-

import json
import requests
import urllib.parse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import xbmc
    KODI_AVAILABLE = True
except ImportError:
    KODI_AVAILABLE = False
    xbmc = None

from scrapers.modules import source_utils

MEDIAHUBMX_SOURCE_URL = 'https://vavoo.to/mediahubmx-source.json'
MEDIAHUBMX_RESOLVE_URL = 'https://vavoo.to/mediahubmx-resolve.json'
DOMAIN = 'vavoo.to'

def getAuthSignature():
    _headers = {
        "user-agent": "okhttp/4.11.0", 
        "accept": "application/json", 
        "content-type": "application/json; charset=utf-8", 
        "content-length": "1106", 
        "accept-encoding": "gzip"
    }
    
    _data = {
        "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
        "reason": "app-blur",
        "locale": "de",
        "theme": "dark",
        "metadata": {
            "device": {
                "type": "Handset",
                "brand": "google",
                "model": "Nexus",
                "name": "21081111RG",
                "uniqueId": "d10e5d99ab665233"
            },
            "os": {
                "name": "android",
                "version": "7.1.2",
                "abis": ["arm64-v8a","armeabi-v7a","armeabi"],
                "host": "android"
            },
            "app": {
                "platform": "android",
                "version": "3.1.20",
                "buildId": "289515000",
                "engine": "hbc85",
                "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"],
                "installer": "app.revanced.manager.flutter"
            },
            "version": {
                "package": "tv.vavoo.app",
                "binary": "3.1.20",
                "js": "3.1.20"
            }
        },
        "appFocusTime": 0,
        "playerActive": False,
        "playDuration": 0,
        "devMode": False,
        "hasAddon": True,
        "castConnected": False,
        "package": "tv.vavoo.app",
        "version": "3.1.20",
        "process": "app",
        "firstAppStart": 1743962904623,
        "lastAppStart": 1743962904623,
        "ipLocation": "",
        "adblockEnabled": True,
        "proxy": {
            "supported": ["ss","openvpn"],
            "engine": "ss",
            "ssVersion": 1,
            "enabled": True,
            "autoServer": True,
            "id": "pl-waw"
        },
        "iap": {"supported": False}
    }
    
    try:
        req = requests.post('https://www.vavoo.tv/api/app/ping', json=_data, headers=_headers, timeout=10, verify=False).json()
        return req.get("addonSig")
    except:
        return None

def get_mediahubmx_headers():
    signature = getAuthSignature()
    headers = {
        "user-agent": "MediaHubMX/2", 
        "content-type": "application/json; charset=utf-8", 
        "accept-encoding": "gzip"
    }
    
    if signature:
        headers["mediahubmx-signature"] = signature
    
    return headers

def get_media_data(titles, year, season=0, episode=0, imdb=''):
    try:
        if season == 0:
            mediatype = 'movie'
            result = requests.get(
                f'https://api.themoviedb.org/3/find/{imdb}?api_key=be7e192d9ff45609c57344a5c561be1d&external_source=imdb_id',
                timeout=10,
                verify=False
            ).json()["movie_results"][0]
            
            _data = {
                "language": "de",
                "region": "AT", 
                "type": "movie",
                "ids": {"tmdb_id": result["id"]},
                "name": result["title"],
                "episode": {},
                "clientVersion": "3.0.2"
            }
        else:
            mediatype = 'series'
            result = requests.get(
                f'https://api.themoviedb.org/3/find/{imdb}?api_key=be7e192d9ff45609c57344a5c561be1d&external_source=imdb_id',
                timeout=10,
                verify=False
            ).json()["tv_results"][0]
            
            _data = {
                "language": "de",
                "region": "AT",
                "type": "series", 
                "ids": {"tmdb_id": result["id"]},
                "name": result["name"],
                "episode": {"season": season, "episode": episode},
                "clientVersion": "3.0.2"
            }
        
        headers = get_mediahubmx_headers()
        
        response = requests.post(
            MEDIAHUBMX_SOURCE_URL,
            json=_data,
            headers=headers,
            timeout=15,
            verify=False
        )
        
        if response.status_code != 200:
            return None
        
        return response.json()
    
    except:
        return None

def resolve_stream_url(stream_url):
    try:
        headers = get_mediahubmx_headers()
        
        _data = {
            "language": "de",
            "region": "AT", 
            "url": stream_url,
            "clientVersion": "3.0.2"
        }
        
        response = requests.post(
            MEDIAHUBMX_RESOLVE_URL,
            json=_data,
            headers=headers, 
            timeout=10,
            verify=False
        )
        
        if response.status_code != 200:
            return None
        
        resolved_data = response.json()
        return resolved_data.get("data", {}).get("url")
    
    except:
        return None

def is_blocked_hoster(url):
    if not url:
        return True, 'Unknown', None, False
    
    blocked_hosters = [
        'openload', 'streamango', 'verystream', 'vshare', 'thevideo', 'vidtodo'
    ]
    
    hoster = 'Unknown'
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        if 'streamtape' in domain:
            hoster = 'Streamtape'
        elif 'dood' in domain:
            hoster = 'Doodstream'
        elif 'vidoza' in domain:
            hoster = 'Vidoza'
        elif 'mixdrop' in domain:
            hoster = 'Mixdrop'
        elif 'supervideo' in domain:
            hoster = 'Supervideo'
        elif 'luluvideo' in domain:
            hoster = 'Luluvideo'
        elif 'voe' in domain:
            hoster = 'Voe'
        elif 'filemoon' in domain:
            hoster = 'Filemoon'
        elif 'upstream' in domain:
            hoster = 'Upstream'
        else:
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                hoster = domain_parts[-2].capitalize()
            else:
                hoster = domain.capitalize()
    except:
        pass
    
    is_blocked = any(blocked in url.lower() for blocked in blocked_hosters)
    
    prio_hosters = ['Streamtape', 'Doodstream', 'Voe', 'Filemoon']
    prio_hoster = hoster in prio_hosters
    
    return is_blocked, hoster, url, prio_hoster

def parse_quality(tag, stream_url):
    if not tag:
        tag = ""
    tag_lower = tag.lower()
    url_lower = stream_url.lower()
    if '4k' in tag_lower or '2160' in tag_lower or '4k' in url_lower:
        return '4K'
    elif '1440' in tag_lower or '2k' in tag_lower or '1440' in url_lower:
        return '1440p'
    elif '1080' in tag_lower or '1080' in url_lower:
        return '1080p'
    elif '720' in tag_lower or '720' in url_lower:
        return '720p'
    elif '480' in tag_lower or '480' in url_lower:
        return '480p'
    elif '360' in tag_lower or '360' in url_lower:
        return '360p'
    return 'SD'

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['vavoo.to']
        self.sources = []
    
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        self.sources = []
        
        if not imdb:
            return self.sources
        
        try:
            mirrors = get_media_data(titles, year, season, episode, imdb)
            
            if not mirrors:
                return self.sources
            
            for i in mirrors:
                try:
                    if "de" in i.get('languages', []):
                        stream_url = i.get("url")
                        if not stream_url:
                            continue
                        
                        resolved_url = resolve_stream_url(stream_url)
                        if not resolved_url:
                            continue
                        
                        is_blocked, hoster, sUrl, prio_hoster = is_blocked_hoster(resolved_url)
                        
                        if is_blocked:
                            continue
                        
                        if sUrl:
                            quality = parse_quality(i.get("tag", ""), resolved_url)
                            
                            source_entry = {
                                'source': hoster,
                                'quality': quality,
                                'language': 'de',
                                'url': sUrl,
                                'direct': True,
                                'debridonly': False,
                                'info': f"MediaHubMX_{quality}"
                            }
                            
                            self.sources.append(source_entry)
                
                except:
                    continue
            
            return self.sources
        
        except:
            return self.sources
    
    def resolve(self, url):
        try:
            resolved_url = resolve_stream_url(url)
            
            if resolved_url:
                return resolved_url
            else:
                headers = {
                    'Referer': f'https://{DOMAIN}/',
                    'Origin': f'https://{DOMAIN}',
                    'User-Agent': 'Mozilla/5.0'
                }
                
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=10,
                    verify=False,
                    allow_redirects=True
                )
                
                return resp.url
        
        except:
            return None