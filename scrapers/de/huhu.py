# -*- coding: UTF-8 -*-
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from scrapers.modules import cleantitle, source_utils
from resources.lib.control import getSetting, quote
from resources.lib.tools import logger
SITE_IDENTIFIER = 'huhu'
SITE_DOMAIN = 'huhu.to'
SITE_NAME = SITE_IDENTIFIER.upper()
LANG_FILTER_MAP = {'1': '1', '2': '2', '3': '4'}
LANG_LABELS = {1: ' (DE)', 2: ' (EN)', 3: ' (EN/DE-Sub)', 4: ' (JP)'}

def _lang_label(sLang):
    return LANG_LABELS.get(int(sLang) if str(sLang).isdigit() else -1, '')

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.web_link = self.base_link + '/web-vod/'
        self.list_link = self.web_link + 'api/list?id=%s'
        self.links_link = self.web_link + 'api/links?id=%s'
        self.get_link = self.web_link + 'api/get?link='
        self.api_key = 'TC2AJpYciVIFw6POgjNpiJfsnSnw'
        self.checkHoster = True
        self.sources = []

    def make_request(self, url):
        logger.debug('Huhu make_request url: %s' % url)
        headers = {
            'Referer': self.web_link,
            'Origin': self.base_link,
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/30.0 Chrome/143.0.0.0 Mobile Safari/537.36',
            'api-key': self.api_key,
            'Accept': '*/*',
            'Content-Type': 'application/json; charset=utf-8'
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            logger.debug('Huhu make_request status_code: %s' % resp.status_code)
            if resp.status_code != 200:
                logger.error('Huhu make_request non-200: %s body=%s' % (resp.status_code, resp.text[:500]))
                return None
            data = resp.json()
            logger.debug('Huhu make_request data: %s' % data)
            return data
        except Exception as e:
            logger.error('Huhu make_request error: %s' % e)
            return None

    def norm(self, value):
        try:
            return cleantitle.get(value)
        except Exception as e:
            logger.error('Huhu norm error: %s' % e)
            return (value or '').strip().lower()

    def search(self, title, kind):
        logger.debug('Huhu search start: title=%s kind=%s' % (title, kind))
        search_id = '%s.popular.search=%s' % (kind, title)
        url = self.list_link % quote(search_id)
        data = self.make_request(url)
        if not data or not isinstance(data, dict):
            logger.error('Huhu search error: invalid response for %s' % url)
            return []
        items = data.get('data', [])
        logger.debug('Huhu search result count: %s' % len(items))
        return items

    def find_media_id(self, titles, year, season, episode):
        logger.debug('Huhu find_media_id start: titles=%s year=%s season=%s episode=%s' % (titles, year, season, episode))
        kind = 'series' if int(season) > 0 else 'movie'
        try:
            for title in titles:
                if not title:
                    continue

                items = self.search(title, kind)
                norm_title = self.norm(title)

                for item in items:
                    try:
                        if not isinstance(item, dict):
                            continue

                        norm_name = self.norm(item.get('name', ''))
                        norm_original = self.norm(item.get('originalName', ''))
                        logger.debug('Huhu find_media_id comparing: norm_title=%s norm_name=%s norm_original=%s' % (norm_title, norm_name, norm_original))

                        if norm_title != norm_name and norm_title != norm_original:
                            continue

                        release_date = item.get('releaseDate', '') or ''
                        item_year = release_date[:4]
                        if year and item_year:
                            try:
                                if abs(int(item_year) - int(year)) > 1:
                                    logger.debug('Huhu find_media_id year mismatch: item_year=%s year=%s' % (item_year, year))
                                    continue
                            except ValueError:
                                pass

                        base_id = item.get('id', '')
                        if not base_id:
                            continue

                        if kind == 'series':
                            media_id = '%s.%s.%s' % (base_id, season, episode)
                        else:
                            media_id = base_id

                        logger.debug('Huhu find_media_id matched media_id: %s' % media_id)
                        return media_id

                    except Exception as e:
                        logger.error('Huhu find_media_id item error: %s' % e)
                        continue

            logger.error('Huhu find_media_id error: no match found for titles=%s year=%s' % (titles, year))
            return None

        except Exception as e:
            logger.error('Huhu find_media_id error: %s' % e)
            return None

    def parse_quality(self, name):
        if not name:
            return 'SD'
        name_lower = name.lower()
        if '2160' in name_lower or '4k' in name_lower:
            return '4K'
        elif '1440' in name_lower or '2k' in name_lower:
            return '1440p'
        elif '1080' in name_lower:
            return '1080p'
        elif '720' in name_lower:
            return '720p'
        elif '480' in name_lower:
            return '480p'
        elif '360' in name_lower:
            return '360p'
        return 'SD'

    def parse_hoster(self, name):
        name = name.split('(')[0].strip()
        mapping = {'Server C1': 'Voe'}
        return mapping.get(name, name)

    def get_lang_code(self, language):
        lang = (language or '').lower()
        if 'sub' in lang and 'de' in lang and 'en' in lang:
            return 3
        if lang.startswith('de'):
            return 1
        if lang.startswith('en'):
            return 2
        if lang.startswith('ja') or lang.startswith('jp'):
            return 4
        return 0

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        logger.debug('Huhu run start: titles=%s year=%s season=%s episode=%s imdb=%s' % (titles, year, season, episode, imdb))

        try:
            media_id = self.find_media_id(titles, year, season, episode)
            if not media_id:
                logger.error('Huhu run error: media_id not resolved for titles=%s' % titles)
                return self.sources

            links_url = self.links_link % media_id
            logger.debug('Huhu run links_url: %s' % links_url)
            links_data = self.make_request(links_url)

            if not links_data or not isinstance(links_data, list):
                logger.error('Huhu run error: invalid links_data for %s: %s' % (links_url, links_data))
                return self.sources

            logger.debug('Huhu run links_data count: %s' % len(links_data))

            sLanguage = getSetting('prefLanguage', '0')
            filter_code = LANG_FILTER_MAP.get(sLanguage) if sLanguage != '0' else None
            logger.debug('Huhu run sLanguage: %s filter_code: %s' % (sLanguage, filter_code))

            for index, link in enumerate(links_data):
                try:
                    logger.debug('Huhu run processing link %s: %s' % (index, link))

                    if not isinstance(link, dict):
                        continue

                    hoster_url = link.get('url', '').strip()
                    if not hoster_url:
                        continue

                    link_name = link.get('name', '')
                    quality = self.parse_quality(link_name)
                    hoster = self.parse_hoster(link_name)
                    language = link.get('language', 'de').split('(')[0].strip()
                    lang_code = self.get_lang_code(language)

                    if filter_code and str(lang_code) != filter_code:
                        logger.debug('Huhu run skip link %s: lang_code=%s filter_code=%s' % (index, lang_code, filter_code))
                        continue

                    final_url = self.get_link + hoster_url
                    info_label = link_name + _lang_label(lang_code)

                    source_entry = {
                        'source': hoster,
                        'quality': quality,
                        'language': language,
                        'url': final_url,
                        'direct': False,
                        'debridonly': False,
                        'info': info_label
                    }

                    logger.debug('Huhu run built source_entry %s: %s' % (index, source_entry))
                    self.sources.append(source_entry)

                except Exception as e:
                    logger.error('Huhu run link error at index %s: %s' % (index, e))
                    continue

            logger.debug('Huhu run finished, total sources: %s' % len(self.sources))
            return self.sources

        except Exception as e:
            logger.error('Huhu run error: %s' % e)
            return self.sources

    def resolve(self, url):
        logger.debug('Huhu resolve start: %s' % url)
        try:
            headers = {
                'Referer': self.web_link,
                'Origin': self.base_link,
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/30.0 Chrome/143.0.0.0 Mobile Safari/537.36'
            }

            resp = requests.get(
                url,
                headers=headers,
                timeout=10,
                verify=False,
                allow_redirects=True
            )

            logger.debug('Huhu resolve final url: %s' % resp.url)
            return resp.url

        except Exception as e:
            logger.error('Huhu resolve error: %s' % e)
            return None
