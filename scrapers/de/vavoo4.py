# -*- coding: utf-8 -*-
import sys, os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..")); from resources.lib import log_utils
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
DOMAIN = 'www.vavoo.to'
URL_MAIN = f'https://{DOMAIN}/web-vod/'
URL_LINKS = URL_MAIN + 'api/links?id=%s'
URL_GET = URL_MAIN + 'api/get?link='

def log(msg, level=xbmc.LOGINFO if KODI_AVAILABLE else None):
    msg = f"[VAVOO-VOD] {msg}"
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


def make_request(url):

    log(f"Request: {url}")
    
    headers = {
        'Referer': URL_MAIN,
        'Origin': f'https://{DOMAIN}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=15,
            verify=False
        )
        
        log(f"Response: {resp.status_code}")
        
        if resp.status_code != 200:
            log_error(f"Status {resp.status_code}: {resp.text[:200]}")
            return None
        
        data = resp.json()
        log("✓ JSON OK")
        return data
    
    except Exception as e:
        log_error("Request failed", e)
        return None


class source:
    
    def __init__(self):
        log("=" * 70)
        log("Vavooto Scraper (WEB-VOD API - kein Auth-Token!)")
        log(f"API: {URL_MAIN}")
        log("=" * 70)
        self.priority = 1
        self.language = ['de']
        self.domains = ['vavoo.to']
    
    def parse_quality(self, name):
        if not name:
            return 'SD'
        
        if '(' in name and 'p)' in name:
            try:
                quality_str = name.split('(')[1].split('p)')[0].strip()
                return quality_str + 'p'
            except:
                pass

        name_lower = name.lower()
        if '2160' in name_lower or '4k' in name_lower:
            return '4K'
        elif '1080' in name_lower:
            return '1080p'
        elif '720' in name_lower:
            return '720p'
        elif '480' in name_lower:
            return '480p'
        
        return '720p'
    
    def parse_hoster(self, name):
        name = name.split('(')[0].strip()

        if 'Server P2' in name:
            return 'Streamtape'
        elif 'Server W2' in name:
            return 'Doodstream'
        elif 'Server O' in name:
            return 'Vidoza'
        elif 'Server E' in name:
            return 'Mixdrop'
        elif 'Server M2' in name:
            return 'Supervideo'
        elif 'Server G2' in name:
            return 'Luluvideo'
        else:
            return name
    
    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        log("=" * 70)
        log(f"RUN: {titles[0] if titles else 'N/A'} ({year})")
        log(f"Season: {season}, Episode: {episode}")
        log(f"IMDB: {imdb}")
        log("=" * 70)
        
        sources = []
        
        if not imdb:
            log_error("No IMDB ID")
            return sources
        
        try:
            if season == 0:
                media_id = f'movie.{imdb}'
                log(f"FILM: {media_id}")
            else:
                log("SERIE - IMDB zu TMDB Konvertierung...")
                
                try:
                    V2_API_KEY = '4a65e1e644af74c98f9f2b3884669deb3fac9531ee71f39babf1dee46d264d17'
                    headers = {
                        'Content-Type': 'application/json',
                        'trakt-api-key': V2_API_KEY,
                        'trakt-api-version': '2'
                    }
                    
                    trakt_url = f'https://api.trakt.tv/shows/{imdb}'
                    result = requests.get(trakt_url, headers=headers, timeout=10, verify=False)
                    result.raise_for_status()
                    
                    tmdb_id = result.json().get('ids', {}).get('tmdb')
                    
                    if not tmdb_id:
                        log_error("Keine TMDB ID gefunden")
                        return sources
                    
                    log(f"✓ TMDB ID: {tmdb_id}")
                    media_id = f'series.{tmdb_id}.{season}.{episode}'
                    log(f"SERIE: {media_id}")
                
                except Exception as e:
                    log_error("TMDB Konvertierung fehlgeschlagen", e)
                    return sources
            links_url = URL_LINKS % media_id
            log(f"Links URL: {links_url}")
            
            links_data = make_request(links_url)
            
            if not links_data:
                log_error("Keine Links von API!")
                return sources
            
            if not isinstance(links_data, list):
                log_error(f"Ungültiger Typ: {type(links_data)}")
                return sources
            
            log(f"✓ {len(links_data)} Links gefunden")
            for idx, link in enumerate(links_data, 1):
                try:
                    if not isinstance(link, dict):
                        continue
                    hoster_url = link.get('url', '').strip()
                    if not hoster_url:
                        continue
                    
                    link_name = link.get('name', '')
                    quality = self.parse_quality(link_name)
                    hoster = self.parse_hoster(link_name)
                    language = link.get('language', 'de').split('(')[0].strip()
                    final_url = URL_GET + hoster_url
                    source_entry = {
                        'source': hoster,
                        'quality': quality,
                        'language': language,
                        'url': final_url,
                        'direct': False,
                        'debridonly': False,
                        'info': link_name
                    }
                    
                    sources.append(source_entry)
                    if idx <= 5:
                        log(f"  [{idx}] {hoster} ({quality}) - {language}")
                
                except Exception as e:
                    log_error(f"Fehler bei Link {idx}", e)
                    continue
            
            log("=" * 70)
            log(f"✓✓✓ {len(sources)} SOURCES GEFUNDEN ✓✓✓")
            log("=" * 70)
            if sources:
                quality_count = {}
                hoster_count = {}
                
                for src in sources:
                    qual = src['quality']
                    host = src['source']
                    quality_count[qual] = quality_count.get(qual, 0) + 1
                    hoster_count[host] = hoster_count.get(host, 0) + 1
                
                log(f"Qualitäten: {quality_count}")
                log(f"Hoster: {dict(list(hoster_count.items())[:5])}")
            
            return sources
        
        except Exception as e:
            log_error("run() fehlgeschlagen", e)
            return sources
    
    def resolve(self, url):
        log(f"Resolve: {url[:70]}...")
        
        try:
            headers = {
                'Referer': URL_MAIN,
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

            final_url = resp.url
            
            log(f"✓ Resolved: {final_url[:70]}...")
            
            return final_url
        
        except Exception as e:
            log_error("Resolve fehlgeschlagen", e)
            return None
