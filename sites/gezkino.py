# -*- coding: utf-8 -*-
import json
import re
import os
import sqlite3
import hashlib
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import xbmcgui
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, dataPath, getSetting
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.log_utils import log, LOGDEBUG

oNavigator        = navigator()
addDirectoryItem  = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory       = oNavigator.xsDirectory
params            = ParameterHandler()

SITE_IDENTIFIER = 'gezkino'
SITE_NAME       = 'GEZ Kino'
SITE_ICON       = 'gezkino.png'
DOMAIN          = getSetting('provider.' + SITE_IDENTIFIER + '.domain', 'mediathekviewweb.de')

API_URL         = 'https://mediathekviewweb.de/api/query'
IPTV_URL        = 'https://raw.githubusercontent.com/jnk22/kodinerds-iptv/master/iptv/clean/clean_tv_main.m3u'
MIN_DURATION    = 4680
QUERY_TERMS     = ['Spielfilm', 'Spielfilme', 'Spielfilm-Highlights', 'Filme', 'Kino - Filme']
SKIP_WORDS      = ['audiodeskription', 'audio description', 'ad version', 'hörfilm', 'deskription', 'barrierefrei version']

STRIP_MARKERS   = [
    ' - Spielfilm', u' \u2013 Spielfilm', ' - Spiellfilm', u' \u2013 Spiellfilm', ', Spielfilm',
    u' \xd6sterreich', ', Deutschland', ', Schweiz', ', Belgien', ', Frankreich', ', Spanien',
    ', Niederlande', ', Irland', ', Luxemburg', ', Italien', ', USA', ', Kosovo',
    u', Gro\xdfbritannien', ', Tschechische Republik', ', Norwegen', ', BRD', u', D\xe4nemark',
    ', Australien', ', Schweden', ', Video:', u', Pr\xe4sentiert:', ', Kurzfilm',
    ' Fernsehfilm', ' Heimatfilm', ' - Thriller', ' - Drama',
    ' - Aufstand der Pferdefreunde Spielfilm', u'\xab', u'\xbb',
]

GENRES = [
    ('Live-TV',                    'Live-TV'),
    ('Action',                     'Action'),
    ('Abenteuer',                  'Abenteuer'),
    ('Animation',                  'Animation'),
    (u'Kom\xf6dien',               u'Kom\xf6die'),
    ('Krimi',                      'Krimi'),
    ('Dokumentationen',            'Doku'),
    ('Dramen',                     'Drama'),
    ('Familie',                    'Familie'),
    ('Fantasy',                    'Fantasy'),
    ('Historie',                   'Historie'),
    ('Horror',                     'Horror'),
    ('Musik',                      'Musik'),
    ('Mystery',                    'Mystery'),
    ('Liebesfilme und Romantik',   'Romanze'),
    ('Science Fiction',            'Sci-Fi'),
    ('TV-Film',                    'TV-Film'),
    ('Thriller',                   'Thriller'),
    ('Krieg',                      'Krieg'),
    ('Western',                    'Western'),
    ('Sonstige (Unkategorisiert)', 'Sonstige'),
]

_GENRES_MAP = {
    28: 'Action', 12: 'Abenteuer', 16: 'Animation', 35: u'Kom\xf6die', 80: 'Krimi', 99: 'Doku',
    18: 'Drama', 10751: 'Familie', 14: 'Fantasy', 36: 'Historie', 27: 'Horror', 10402: 'Musik',
    9648: 'Mystery', 10749: 'Romanze', 878: 'Sci-Fi', 10770: 'TV-Film', 53: 'Thriller',
    10752: 'Krieg', 37: 'Western',
}
_TMDB_KEY = '60b3801a9e76b5706ee2a432f06423e6'

DB_DIR  = os.path.join(dataPath, 'gezkino')
DB_PATH = os.path.join(DB_DIR, 'movie_metadata.db')
if not os.path.exists(DB_DIR):
    try:
        os.makedirs(DB_DIR)
    except Exception:
        pass


def _init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS movie_cache
                            (search_title TEXT PRIMARY KEY, plot TEXT, rating TEXT,
                             poster_url TEXT, local_poster TEXT, genres_json TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS film_list
                            (hash_id TEXT PRIMARY KEY, title TEXT, video_url TEXT,
                             search_name TEXT, year TEXT, genres_json TEXT)''')
            conn.commit()
    except Exception as e:
        log('[%s] _init_db Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)

_init_db()


def _clean_title(title):
    s = title
    for m in STRIP_MARKERS:
        s = re.split(re.escape(m), s, flags=re.I)[0]
    s = re.sub(r'^(Spielfilm|Spiellfilm):\s*', '', s, flags=re.I)
    s = s.replace(u'\u2013', '-').replace(u'\u2014', '-')
    s = re.sub(r'\(.*?\)', '', s)
    s = s.strip().rstrip(u'( ,.-_\u2013\u2014\xbb')
    year_match = re.search(r'(\d{4})', title)
    year = year_match.group(1) if year_match else None
    return s, year


def _get_tmdb(session, title, year=None):
    try:
        p = {'api_key': _TMDB_KEY, 'query': title, 'language': 'de-DE', 'include_adult': 'false'}
        if year:
            p['year'] = year
        res = session.get('https://api.themoviedb.org/3/search/movie', params=p, timeout=5).json()
        results = res.get('results', [])
        if not results and year:
            p.pop('year')
            results = session.get('https://api.themoviedb.org/3/search/movie', params=p, timeout=5).json().get('results', [])
        if results:
            mv = results[0]
            path = mv.get('poster_path')
            rd = mv.get('release_date', '')
            tmdb_year = rd.split('-')[0] if '-' in rd else None
            genres_list = [_GENRES_MAP[g] for g in mv.get('genre_ids', []) if g in _GENRES_MAP]
            if not genres_list:
                genres_list = ['Mediathek']
            return {
                'poster':      ('https://image.tmdb.org/t/p/w342' + path) if path else '',
                'plot':        mv.get('overview', 'Keine Beschreibung.'),
                'rating':      str(mv.get('vote_average', 'N/A')),
                'genres_list': genres_list,
                'year':        tmdb_year,
            }
    except Exception as e:
        log('[%s] _get_tmdb Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)
    return None


def _fetch_mediathek(query_term):
    try:
        payload = json.dumps({
            'queries': [{'fields': ['topic'], 'query': query_term}],
            'size': 2000, 'sortBy': 'timestamp', 'sortOrder': 'desc',
        })
        oReq = cRequestHandler(API_URL, caching=False, method='POST', data=payload)
        oReq.addHeaderEntry('Content-Type', 'application/json')
        sHtml = oReq.request()
        if not sHtml:
            return []
        return json.loads(sHtml).get('result', {}).get('results', [])
    except Exception as e:
        log('[%s] _fetch_mediathek Fehler bei "%s": %s' % (SITE_NAME, query_term, str(e)), LOGDEBUG)
        return []


def _fetch_iptv():
    try:
        oReq = cRequestHandler(IPTV_URL, caching=False)
        sHtml = oReq.request()
        return sHtml.splitlines() if sHtml else []
    except Exception as e:
        log('[%s] _fetch_iptv Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)
        return []


def _hole_aus_db(genre_filter, search_str=None, start_char=None, year_filter=None):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='film_list'")
            if not c.fetchone():
                return None
            rows = conn.execute('''
                SELECT f.title, f.video_url, f.search_name, f.year, f.genres_json,
                       c.local_poster, c.plot, c.rating
                FROM film_list f
                LEFT JOIN movie_cache c ON (f.search_name || \'_\' || f.year) = c.search_title
            ''').fetchall()
            if not rows:
                return None
        result = []
        for r in rows:
            g_list  = json.loads(r[4])
            is_tv   = 'Live-TV' in g_list
            title   = r[0]
            fy      = r[3]
            if search_str and search_str.lower() not in title.lower():
                continue
            if start_char:
                fc = title[0].upper()
                if start_char == '#':
                    if fc.isalpha():
                        continue
                elif fc != start_char:
                    continue
            if year_filter and fy != year_filter:
                continue
            if genre_filter not in ('AZ', 'YEAR'):
                if genre_filter == 'Live-TV':
                    if not is_tv: continue
                elif genre_filter == 'Alle':
                    if is_tv: continue
                elif genre_filter == 'Sonstige':
                    if is_tv or (g_list and g_list != ['Mediathek']): continue
                else:
                    if genre_filter not in g_list: continue
            result.append({
                'title':  title,
                'url':    r[1],
                'plot':   r[6] if r[6] else 'Keine Beschreibung.',
                'rating': r[7] if r[7] else 'N/A',
                'thumb':  r[5] if r[5] else '',
                'genres': g_list,
                'year':   fy,
            })
        result.sort(key=lambda x: x['title'].lower())
        return result
    except Exception as e:
        log('[%s] _hole_aus_db Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)
        return []


def _zeige_filmliste(genre_filter, search_str=None, start_char=None, year_filter=None, bGlobal=False):
    log('[%s] _zeige_filmliste genre=%s search=%s char=%s year=%s' % (SITE_NAME, genre_filter, search_str, start_char, year_filter), LOGDEBUG)
    filme = _hole_aus_db(genre_filter, search_str=search_str, start_char=start_char, year_filter=year_filter)
    if filme is None:
        if xbmcgui.Dialog().yesno(SITE_NAME, 'Datenbank leer. Jetzt aktualisieren?'):
            syncDB()
            filme = _hole_aus_db(genre_filter, search_str=search_str, start_char=start_char, year_filter=year_filter) or []
        else:
            filme = []
    if not filme:
        log('[%s] _zeige_filmliste: Keine Filme' % SITE_NAME, LOGDEBUG)
        setEndOfDirectory()
        return
    items = []
    for film in filme:
        sName     = film['title']
        infoTitle = sName
        if bGlobal:
            sName = SITE_NAME + ' - ' + sName
        is_tv = 'Live-TV' in film['genres']
        item = {}
        item['infoTitle'] = infoTitle
        item['title']     = sName
        item['entryUrl']  = film['url']
        item['isTvshow']  = False
        item['poster']    = film['thumb']
        item['year']      = film['year']
        item['sFunction'] = 'showHosters'
        item['mediatype'] = 'movie'
        item['rating']    = film['rating'] if film['rating'] not in ('N/A', 'LIVE') else ''
        item['plot']      = '[B][COLOR blue]%s[/COLOR][/B][CR]%s[CR]%s' % (SITE_NAME, infoTitle, film['plot'])
        items.append(item)
    log('[%s] _zeige_filmliste: Zeige %d Items' % (SITE_NAME, len(items)), LOGDEBUG)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def load():
    log('[%s] load called' % SITE_NAME, LOGDEBUG)
    addDirectoryItem('[ Alle Spielfilme ]',            'runPlugin&site=%s&function=showAll'      % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('[ Filme A-Z ]',                  'runPlugin&site=%s&function=showAZMenu'   % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('[ Nach Jahren sortiert... ]',    'runPlugin&site=%s&function=showYearMenu' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('[ Nach Genres filtern... ]',     'runPlugin&site=%s&function=showGenreMenu'% SITE_NAME, SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem('[ Film suchen... ]',             'runPlugin&site=%s&function=showSearch'   % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    addDirectoryItem('[ Datenbank aktualisieren ]',    'runPlugin&site=%s&function=syncDB'       % SITE_NAME, SITE_ICON, 'DefaultAddonProgram.png')
    setEndOfDirectory()


def showAll(entryUrl=None, sSearchText=None, bGlobal=False):
    log('[%s] showAll called bGlobal=%s sSearchText=%s' % (SITE_NAME, bGlobal, sSearchText), LOGDEBUG)
    _zeige_filmliste('Alle', search_str=sSearchText, bGlobal=bGlobal)


def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    showAll(entryUrl=entryUrl, sSearchText=sSearchText, bGlobal=bGlobal)


def showAZMenu():
    log('[%s] showAZMenu called' % SITE_NAME, LOGDEBUG)
    for ch in ['#'] + list(string.ascii_uppercase):
        addDirectoryItem(ch, 'runPlugin&site=%s&function=showAZList&sChar=%s' % (SITE_NAME, ch), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showAZList():
    ch = params.getValue('sChar')
    log('[%s] showAZList char=%s' % (SITE_NAME, ch), LOGDEBUG)
    _zeige_filmliste('AZ', start_char=ch)


def showYearMenu():
    log('[%s] showYearMenu called' % SITE_NAME, LOGDEBUG)
    jahre = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("""
                SELECT DISTINCT year FROM film_list
                WHERE year IS NOT NULL AND year != ''
                  AND LENGTH(year) = 4 AND year GLOB '[0-9][0-9][0-9][0-9]'
            """).fetchall()
            jahre = sorted([r[0] for r in rows], reverse=True)
    except Exception as e:
        log('[%s] showYearMenu Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)
    if not jahre:
        addDirectoryItem('Keine Daten. Bitte DB aktualisieren.', '', SITE_ICON, 'DefaultMovies.png')
    else:
        for jahr in jahre:
            addDirectoryItem('Jahr ' + jahr, 'runPlugin&site=%s&function=showYearList&sYear=%s' % (SITE_NAME, jahr), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()


def showYearList():
    year = params.getValue('sYear')
    log('[%s] showYearList year=%s' % (SITE_NAME, year), LOGDEBUG)
    _zeige_filmliste('YEAR', year_filter=year)


def showGenreMenu():
    log('[%s] showGenreMenu called' % SITE_NAME, LOGDEBUG)
    for label, internal in GENRES:
        addDirectoryItem(label, 'runPlugin&site=%s&function=showGenreList&sGenre=%s' % (SITE_NAME, quote_plus(internal)), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showGenreList():
    genre = params.getValue('sGenre')
    log('[%s] showGenreList genre=%s' % (SITE_NAME, genre), LOGDEBUG)
    _zeige_filmliste(genre)


def showSearch():
    log('[%s] showSearch called' % SITE_NAME, LOGDEBUG)
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        return
    log('[%s] showSearch: "%s"' % (SITE_NAME, sSearchText), LOGDEBUG)
    _zeige_filmliste('AZ', search_str=sSearchText)


def _search(sSearchText):
    log('[%s] _search: "%s"' % (SITE_NAME, sSearchText), LOGDEBUG)
    _zeige_filmliste('AZ', search_str=sSearchText, bGlobal=True)


def showHosters():
    log('[%s] showHosters called' % SITE_NAME, LOGDEBUG)
    try:
        raw_meta = params.getValue('meta')
        meta = json.loads(raw_meta) if raw_meta else {}
    except Exception:
        meta = {}
    sUrl       = meta.get('entryUrl') or params.getValue('entryUrl') or ''
    sTitle     = meta.get('infoTitle', '')
    sThumbnail = meta.get('poster', '')
    log('[%s] showHosters URL=%s Titel=%s' % (SITE_NAME, sUrl, sTitle), LOGDEBUG)
    if not sUrl:
        log('[%s] showHosters: Keine URL' % SITE_NAME, LOGDEBUG)
        setEndOfDirectory()
        return
    import xbmc
    li = xbmcgui.ListItem(label=sTitle, path=sUrl)
    li.setInfo('video', {'title': sTitle, 'mediatype': 'movie'})
    if sThumbnail:
        li.setArt({'thumb': sThumbnail, 'poster': sThumbnail})
    li.setProperty('IsPlayable', 'true')
    xbmc.Player().play(sUrl, li)
    log('[%s] showHosters: xbmc.Player().play() -> %s' % (SITE_NAME, sUrl), LOGDEBUG)


def getHosters():
    showHosters()


def syncDB():
    log('[%s] syncDB called' % SITE_NAME, LOGDEBUG)
    progressDialog.create(SITE_NAME, 'Starte parallele Abfrage...')

    raw_mediathek  = {}
    raw_iptv_lines = []

    progressDialog.update(5, 'Lade Mediatheken + IPTV parallel...')

    with ThreadPoolExecutor(max_workers=6) as ex:
        med_futures  = {ex.submit(_fetch_mediathek, q): q for q in QUERY_TERMS}
        iptv_future  = ex.submit(_fetch_iptv)
        all_futures  = list(med_futures.keys()) + [iptv_future]
        for future in as_completed(all_futures):
            if progressDialog.iscanceled():
                ex.shutdown(wait=False, cancel_futures=True)
                progressDialog.close()
                return
            if future is iptv_future:
                raw_iptv_lines = future.result()
            else:
                raw_mediathek[med_futures[future]] = future.result()

    progressDialog.update(28, 'Verarbeite Ergebnisse...')
    seen_titles = set()
    results_map = {}

    for q in QUERY_TERMS:
        for m in raw_mediathek.get(q, []):
            url   = m.get('url_video', '')
            title = m.get('title', '')
            if not url or not title or url in results_map:
                continue
            if any(x in title.lower() for x in SKIP_WORDS):
                continue
            if m.get('duration', 0) < MIN_DURATION:
                continue
            clean_name, prod_year = _clean_title(title)
            if not clean_name:
                continue
            norm = clean_name.strip().lower()
            if norm in seen_titles:
                continue
            seen_titles.add(norm)
            results_map[url] = {
                'title': clean_name, 'year': prod_year if prod_year else '',
                'video_url': url, 'search': clean_name,
                'plot': 'Keine Info.', 'rating': 'N/A', 'genres_list': ['Mediathek'], 'thumb': '',
            }

    for i in range(len(raw_iptv_lines)):
        if raw_iptv_lines[i].startswith('#EXTINF'):
            logo_m = re.search(r'tvg-logo="([^"]+)"', raw_iptv_lines[i])
            name   = raw_iptv_lines[i].split(',')[-1].strip()
            if i + 1 < len(raw_iptv_lines) and raw_iptv_lines[i + 1].startswith('http'):
                url = raw_iptv_lines[i + 1].strip()
                results_map[url] = {
                    'title': '[TV] ' + name, 'year': '', 'video_url': url, 'search': name,
                    'plot': 'Live-TV Sender', 'rating': 'LIVE', 'genres_list': ['Live-TV'],
                    'logo_url': logo_m.group(1) if logo_m else '', 'thumb': '',
                }

    if progressDialog.iscanceled():
        progressDialog.close()
        return

    progressDialog.update(32, u'Pr\xfcfe Cache...')
    to_fetch      = []
    movie_urls    = [url for url, mv in results_map.items() if 'Live-TV' not in mv['genres_list']]
    cache_key_map = {('%s_%s' % (results_map[url]['search'], results_map[url]['year'])): url for url in movie_urls}

    try:
        with sqlite3.connect(DB_PATH) as conn:
            for url, mv in results_map.items():
                if 'Live-TV' in mv['genres_list']:
                    mv['thumb'] = mv.get('logo_url', '')
            if cache_key_map:
                keys = list(cache_key_map.keys())
                ph   = ','.join('?' * len(keys))
                rows = conn.execute(
                    'SELECT search_title, plot, rating, local_poster, genres_json FROM movie_cache WHERE search_title IN (%s)' % ph,
                    keys
                ).fetchall()
                cached = {row[0]: row for row in rows}
                for ck, url in cache_key_map.items():
                    mv = results_map[url]
                    if ck in cached:
                        row = cached[ck]
                        mv['plot'], mv['rating'], mv['thumb'] = row[1], row[2], row[3] or ''
                        mv['genres_list'] = json.loads(row[4])
                    else:
                        to_fetch.append((url, mv, ck))
    except Exception as e:
        log('[%s] syncDB Cache-Check Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)

    total_fetch     = len(to_fetch)
    tmdb_results    = {}
    completed_count = [0]
    count_lock      = threading.Lock()
    _tl             = threading.local()

    def _sess():
        if not hasattr(_tl, 's'):
            import requests as _req
            _tl.s = _req.Session()
        return _tl.s

    def _do_fetch(args):
        url, mv, ck = args
        tmdb = _get_tmdb(_sess(), mv['search'], mv['year'])
        with count_lock:
            completed_count[0] += 1
        return url, ck, tmdb

    if total_fetch > 0:
        progressDialog.update(35, 'TMDB: 0 / %d...' % total_fetch)
        with ThreadPoolExecutor(max_workers=20) as executor:
            fmap = {executor.submit(_do_fetch, a): a for a in to_fetch}
            for future in as_completed(fmap):
                if progressDialog.iscanceled():
                    executor.shutdown(wait=False, cancel_futures=True)
                    progressDialog.close()
                    return
                url, ck, tmdb = future.result()
                tmdb_results[url] = (ck, tmdb)
                done = completed_count[0]
                if done % 10 == 0 or done == total_fetch:
                    pct = 35 + int((done / total_fetch) * 57)
                    progressDialog.update(pct, 'TMDB: %d / %d...' % (done, total_fetch))

    progressDialog.update(94, 'Speichere in Datenbank...')
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('DELETE FROM film_list')
            for url, (ck, tmdb) in tmdb_results.items():
                mv = results_map[url]
                if tmdb:
                    mv['plot']        = tmdb['plot']
                    mv['rating']      = tmdb['rating']
                    mv['genres_list'] = tmdb['genres_list']
                    mv['thumb']       = tmdb['poster']
                    if tmdb.get('year'):
                        mv['year'] = tmdb['year']
                    conn.execute(
                        'INSERT OR REPLACE INTO movie_cache VALUES (?,?,?,?,?,?)',
                        (ck, tmdb['plot'], tmdb['rating'], tmdb['poster'], tmdb['poster'], json.dumps(tmdb['genres_list']))
                    )
            for url, mv in results_map.items():
                fy = str(mv['year']).strip()
                if not fy or fy.lower() == 'none' or not fy.isdigit():
                    fy = ''
                conn.execute(
                    'INSERT OR REPLACE INTO film_list VALUES (?,?,?,?,?,?)',
                    (hashlib.md5(url.encode()).hexdigest(), mv['title'], url,
                     mv['search'], fy, json.dumps(mv['genres_list']))
                )
            conn.commit()
    except Exception as e:
        log('[%s] syncDB Speicherfehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)

    progressDialog.close()
    xbmcgui.Dialog().notification(SITE_NAME, 'Datenbank erfolgreich aktualisiert!', xbmcgui.NOTIFICATION_INFO, 3000)
