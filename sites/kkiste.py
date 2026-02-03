# -*- coding: utf-8 -*-
import json, sys, requests, time
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting, setSetting

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'kkiste'
SITE_NAME = 'KKiste'
SITE_ICON = 'kkiste.png'


def get_working_domain():
    domains = ['kkiste.eu', 'kkiste-io.hair']
    for domain in domains:
        try:
            test_url = 'https://{}/data/browse/?lang=2&type=movies&order_by=new&page=1&limit=1'.format(domain)
            response = requests.get(test_url, timeout=5, headers={'Referer': 'https://{}/'.format(domain)})
            if response.status_code == 200 and response.text:
                return domain
        except:
            continue
    return 'kkiste.eu'  

SITE_DOMAIN = getSetting('provider.' + SITE_IDENTIFIER + '.domain', get_working_domain())
DOMAIN = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
URL_MAIN = 'https://' + DOMAIN
URL_API = URL_MAIN + '/data/browse/?lang=%s&type=%s&order_by=%s&page=%s'
URL_SEARCH = URL_MAIN + '/data/browse/?lang=2&order_by=new&page=1&search=%s'
URL_WATCH = URL_MAIN + '/data/watch/?_id=%s'
URL_THUMBNAIL = 'https://image.tmdb.org/t/p/w300%s'


HOSTER_PRIORITY = {
    'voe': 10,
    'streamruby': 10,
    'mixdrop': 9,
    'streamwish': 8,
    'vidoza': 7,
    'vidguard': 6,
    'doodstream': 5,
    'streamtape': 5,
    'filemoon': 5,
    'upstream': 5
}
MIN_PRIORITY = 6
MAX_PER_HOSTER = 5

def load():
    addDirectoryItem("Neue Filme", 'runPlugin&site=%s&function=showEntries&sType=movies&sOrder=new&sPage=1' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Trending Filme", 'runPlugin&site=%s&function=showEntries&sType=movies&sOrder=Trending&sPage=1' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Top bewertete Filme", 'runPlugin&site=%s&function=showEntries&sType=movies&sOrder=rating&sPage=1' % SITE_NAME, SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem("Neue Serien", 'runPlugin&site=%s&function=showEntries&sType=tvseries&sOrder=new&sPage=1' % SITE_NAME, SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Trending Serien", 'runPlugin&site=%s&function=showEntries&sType=tvseries&sOrder=Trending&sPage=1' % SITE_NAME, SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem("Genre (Filme)", 'runPlugin&site=%s&function=showGenre&sType=movies' % SITE_NAME, SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Genre (Serien)", 'runPlugin&site=%s&function=showGenre&sType=tvseries' % SITE_NAME, SITE_ICON, 'DefaultGenre.png')
    addDirectoryItem("Suche", 'runPlugin&site=%s&function=showSearch' % SITE_NAME, SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()

def showGenre():
    params = ParameterHandler()
    sType = params.getValue('sType')
    
    genres = {
        'Action': 'Action',
        'Abenteuer': 'Abenteuer',
        'Animation': 'Animation',
        'Komödie': 'Komödie',
        'Krimi': 'Krimi',
        'Dokumentation': 'Dokumentation',
        'Drama': 'Drama',
        'Familie': 'Familie',
        'Fantasy': 'Fantasy',
        'Horror': 'Horror',
        'Mystery': 'Mystery',
        'Romantik': 'Romantik',
        'Sci-Fi': 'Sci-Fi',
        'Thriller': 'Thriller',
        'Krieg': 'Krieg'
    }
    
    for genre_name in sorted(genres.keys()):
        sUrl = URL_MAIN + '/data/browse/?lang=2&type={}&order_by=new&genre={}&page=1'.format(sType, genres[genre_name])
        addDirectoryItem(genre_name, 'runPlugin&site=%s&function=showEntriesFromUrl&sUrl=%s' % (SITE_NAME, quote_plus(sUrl)), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    params = ParameterHandler()
    
    if entryUrl:
        sUrl = entryUrl
    else:
        sType = params.getValue('sType')
        sOrder = params.getValue('sOrder')
        sPage = params.getValue('sPage')
        sLang = '2' 
        sUrl = URL_API % (sLang, sType, sOrder, sPage)
    
    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('Referer', URL_MAIN + '/')
        oRequest.addHeaderEntry('Origin', URL_MAIN)
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return
    
    if 'movies' not in aJson or not aJson['movies']:
        return
    
    items = []
    
    for movie in aJson['movies']:
        if '_id' not in movie:
            continue
        
        sTitle = str(movie.get('title', ''))
        movie_id = str(movie['_id'])
        
        if sSearchText:
            if not sSearchText.lower() in sTitle.lower():
                continue
        
        
        sThumbnail = ''
        if movie.get('poster_path_season'):
            sThumbnail = URL_THUMBNAIL % movie['poster_path_season']
        elif movie.get('poster_path'):
            sThumbnail = URL_THUMBNAIL % movie['poster_path']
        elif movie.get('backdrop_path'):
            sThumbnail = URL_THUMBNAIL % movie['backdrop_path']
        
        
        sDesc = movie.get('storyline', movie.get('overview', ''))
        
        
        sQuality = ''
        if movie.get('quality'):
            sQuality = str(movie['quality'])
        
        
        sYear = ''
        if movie.get('year'):
            sYear = str(movie['year'])
        
        
        sRating = ''
        if movie.get('rating'):
            sRating = str(movie['rating'])
        
        
        isTvshow = 'Staffel' in sTitle or 'Season' in sTitle
        
        item = {
            'infoTitle': sTitle,
            'title': sTitle,
            'entryUrl': URL_WATCH % movie_id,
            'isTvshow': isTvshow,
            'poster': sThumbnail,
            'quality': sQuality,
            'year': sYear,
            'rating': sRating
        }
        
        if isTvshow:
            item['sFunction'] = 'showEpisodes'
            
            import re
            isMatchS = re.search(r'Staffel\s+(\d+)|Season\s+(\d+)', sTitle, re.IGNORECASE)
            if isMatchS:
                item['season'] = isMatchS.group(1) or isMatchS.group(2)
                item['infoTitle'] = sTitle.split(' - ')[0].strip() if ' - ' in sTitle else sTitle
            else:
                item['season'] = '1'
        
        plot = '[B][COLOR blue]{0}[/COLOR][/B]'.format(SITE_NAME)
        if sYear:
            plot += ' [COLOR yellow]({0})[/COLOR]'.format(sYear)
        if sRating:
            plot += ' [COLOR orange]★ {0}[/COLOR]'.format(sRating)
        if sDesc:
            plot += '[CR]{0}'.format(sDesc[:200])
        
        item['plot'] = plot
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    
    if bGlobal:
        return
    
    
    if 'pager' in aJson and aJson['pager'].get('currentPage'):
        currentPage = int(aJson['pager']['currentPage'])
        totalPages = int(aJson['pager'].get('totalPages', currentPage))
        
        if currentPage < totalPages:
            nextPage = currentPage + 1
            if entryUrl:
                import re
                sNextUrl = re.sub(r'page=\d+', 'page={}'.format(nextPage), sUrl)
                params.setParam('sUrl', sNextUrl)
            else:
                params.setParam('sPage', str(nextPage))
            
            addDirectoryItem('[B]>>> Nächste Seite[/B]', 'runPlugin&' + params.getParameterAsUri(), 'next.png', 'DefaultVideo.png')
    
    setEndOfDirectory(sorted=False)

def showEntriesFromUrl():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    showEntries(entryUrl=sUrl)

def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    
    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('Referer', URL_MAIN + '/')
        oRequest.addHeaderEntry('Origin', URL_MAIN)
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return
    
    if 'streams' not in aJson or not aJson['streams']:
        return
        
    episodes = set()
    for stream in aJson['streams']:
        if 'e' in stream:
            episodes.add(int(stream['e']))
    
    if not episodes:
        return
    
    items = []
    for episode in sorted(episodes):
        item = {
            'title': 'Episode {}'.format(episode),
            'entryUrl': sUrl,
            'poster': meta.get('poster'),
            'season': meta.get('season', '1'),
            'episode': str(episode),
            'infoTitle': meta.get('infoTitle')
        }
        items.append(item)
    
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()

def getHosters():
    items = []
    sUrl = params.getValue('entryUrl')
    meta = json.loads(params.getValue('meta'))
    
    try:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('Referer', URL_MAIN + '/')
        oRequest.addHeaderEntry('Origin', URL_MAIN)
        sJson = oRequest.request()
        aJson = json.loads(sJson)
    except:
        return
    
    if 'streams' not in aJson or not aJson['streams']:
        return
    
    sThumbnail = meta.get('poster')
    sTitle = meta.get('infoTitle')
    isTvshow = meta.get('isTvshow', False)
    episode = meta.get('episode') if isTvshow else None
    
    progressDialog.create(SITE_NAME, 'Suche Streams...')
    
    hoster_count = {}
    stream_list = []
    
    for stream in aJson['streams']:
        
        if episode and str(stream.get('e')) != episode:
            continue
        
        if 'stream' not in stream:
            continue
        
        sStreamUrl = stream['stream']
        
        
        if 'youtube' in sStreamUrl.lower() or 'vod' in sStreamUrl.lower():
            continue
        
        
        if sStreamUrl.startswith('//'):
            sStreamUrl = 'https:' + sStreamUrl
        elif sStreamUrl.startswith('/'):
            sStreamUrl = 'https:/' + sStreamUrl
        
        
        import re
        isMatch = re.search(r'//([^/]+)/', sStreamUrl)
        if not isMatch:
            continue
        
        sHoster = isMatch.group(1)
        if '.' in sHoster:
            sHoster = sHoster[:sHoster.rindex('.')]
        
        
        priority = 0
        for hoster, prio in HOSTER_PRIORITY.items():
            if hoster in sHoster.lower():
                priority = prio
                break
        
        if priority < MIN_PRIORITY:
            continue
        
        
        hoster_key = sHoster.lower()
        if hoster_key not in hoster_count:
            hoster_count[hoster_key] = 0
        
        if hoster_count[hoster_key] >= MAX_PER_HOSTER:
            continue
        
        hoster_count[hoster_key] += 1
        
        
        quality = 'HD'
        if stream.get('release'):
            release = str(stream['release']).upper()
            if 'CAM' in release or 'TS' in release:
                quality = 'CAM'
            elif 'SD' in release:
                quality = 'SD'
        
        stream_list.append({
            'url': sStreamUrl,
            'hoster': sHoster.upper(),
            'quality': quality,
            'priority': priority
        })
    
    progressDialog.update(50, 'Prüfe Hoster...')
    
    
    stream_list = sorted(stream_list, key=lambda x: x['priority'], reverse=True)
    
    for i, stream_data in enumerate(stream_list):
        progressDialog.update(int(50 + (i / len(stream_list)) * 50), 'Prüfe {}...'.format(stream_data['hoster']))
        
        isBlocked, finalUrl = isBlockedHoster(stream_data['url'], resolve=True)
        if not isBlocked:
            display_name = '{} [{}]'.format(stream_data['hoster'], stream_data['quality'])
            items.append((display_name, sTitle, meta, True, finalUrl, sThumbnail))
    
    progressDialog.close()
    
    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    execute('Container.Update(%s)' % url)

def showSearch():
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText:
        return
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=False)

def _search(sSearchText):
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=True)
