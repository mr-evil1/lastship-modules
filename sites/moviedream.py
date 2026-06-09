# -*- coding: utf-8 -*-
import json, sys, re, base64, hashlib, struct
import xbmcgui
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting
from resources.lib.log_utils import log, LOGDEBUG

try:
    from Crypto.Cipher import AES as _AES
    from Crypto.Util.Padding import unpad as _unpad
    HAS_CRYPTO = True
    log('[MovieDream] PyCryptodome verfuegbar', LOGDEBUG)
except ImportError:
    HAS_CRYPTO = False
    logger.warning('moviedream: PyCryptodome nicht verfuegbar, nutze Pure-Python AES')
    log('[MovieDream] PyCryptodome NICHT verfuegbar, nutze Pure-Python AES Fallback', LOGDEBUG)

oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()

SITE_IDENTIFIER = 'moviedream'
SITE_NAME       = 'MovieDream'
SITE_ICON       = 'moviedream.png'
DOMAIN          = getSetting('provider.' + SITE_IDENTIFIER + '.domain', 'moviedream.cx')
URL_MAIN        = 'https://' + DOMAIN

URL_KINO          = URL_MAIN + '/kino'
URL_MOVIES_NEW    = URL_MAIN + '/neuefilme'
URL_MOVIES_TOP    = URL_MAIN + '/beliebtefilme'
URL_MOVIES_RANDOM = URL_MAIN + '/zufallsfilm'
URL_SERIES_NEW    = URL_MAIN + '/neueserien'
URL_SERIES_TOP    = URL_MAIN + '/beliebteserien'
URL_SERIES_RANDOM = URL_MAIN + '/zufallsserie'
URL_WUNSCHBOX     = URL_MAIN + '/wunschbox'
URL_SEARCH        = URL_MAIN + '/suchergebnisse.php?text=%s&sprache=Deutsch'

CRYPTO_KEY = 'a2mZz5S76@2s'

FILM_GENRES = [
    ('Abenteuer',       '/filmgenre/Abenteuer/'),
    ('Action',          '/filmgenre/Action/'),
    ('Animation',       '/filmgenre/Animation/'),
    ('Dokumentarfilm',  '/filmgenre/Dokumentarfilm/'),
    ('Drama',           '/filmgenre/Drama/'),
    ('Familie',         '/filmgenre/Familie/'),
    ('Fantasy',         '/filmgenre/Fantasy/'),
    ('Historie',        '/filmgenre/Historie/'),
    ('Horror',          '/filmgenre/Horror/'),
    ('Komoedie',        '/filmgenre/Kom%C3%B6die/'),
    ('Kriegsfilm',      '/filmgenre/Kriegsfilm/'),
    ('Krimi',           '/filmgenre/Krimi/'),
    ('Liebesfilm',      '/filmgenre/Liebesfilm/'),
    ('Musik',           '/filmgenre/Musik/'),
    ('Mystery',         '/filmgenre/Mystery/'),
    ('Science Fiction', '/filmgenre/Science%20Fiction/'),
    ('TV-Film',         '/filmgenre/TV-Film/'),
    ('Thriller',        '/filmgenre/Thriller/'),
    ('Western',         '/filmgenre/Western/'),
]

SERIEN_GENRES = [
    ('Abenteuer',       '/seriengenre/Abenteuer/'),
    ('Action',          '/seriengenre/Action/'),
    ('Animation',       '/seriengenre/Animation/'),
    ('Doku',            '/seriengenre/Doku/'),
    ('Drama',           '/seriengenre/Drama/'),
    ('Familie',         '/seriengenre/Familie/'),
    ('Fantasy',         '/seriengenre/Fantasy/'),
    ('Horror',          '/seriengenre/Horror/'),
    ('Komoedie',        '/seriengenre/Kom%C3%B6die/'),
    ('Krieg',           '/seriengenre/Krieg/'),
    ('Krimi',           '/seriengenre/Krimi/'),
    ('Liebe',           '/seriengenre/Liebe/'),
    ('Mystery',         '/seriengenre/Mystery/'),
    ('News',            '/seriengenre/News/'),
    ('Reality',         '/seriengenre/Reality/'),
    ('Science Fiction', '/seriengenre/Science%20Fiction/'),
    ('Talk',            '/seriengenre/Talk/'),
    ('Thriller',        '/seriengenre/Thriller/'),
    ('Western',         '/seriengenre/Western/'),
]

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'

_sbox = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]
_inv_sbox = [0]*256
for _i,_v in enumerate(_sbox): _inv_sbox[_v]=_i

def _xtime(a): return ((a<<1)^0x1b) & 0xff if a & 0x80 else (a<<1)&0xff
def _mul(a,b):
    r=0
    for _ in range(8):
        if b&1: r^=a
        hi=a&0x80; a=((a<<1)&0xff);
        if hi: a^=0x1b
        b>>=1
    return r

def _sub_bytes(s): return [_sbox[b] for b in s]
def _inv_sub_bytes(s): return [_inv_sbox[b] for b in s]
def _shift_rows(s):
    return [s[0],s[5],s[10],s[15],s[4],s[9],s[14],s[3],
            s[8],s[13],s[2],s[7],s[12],s[1],s[6],s[11]]
def _inv_shift_rows(s):
    return [s[0],s[13],s[10],s[7],s[4],s[1],s[14],s[11],
            s[8],s[5],s[2],s[15],s[12],s[9],s[6],s[3]]
def _mix_col(c):
    return [_mul(2,c[0])^_mul(3,c[1])^c[2]^c[3],
            c[0]^_mul(2,c[1])^_mul(3,c[2])^c[3],
            c[0]^c[1]^_mul(2,c[2])^_mul(3,c[3]),
            _mul(3,c[0])^c[1]^c[2]^_mul(2,c[3])]
def _inv_mix_col(c):
    return [_mul(0xe,c[0])^_mul(0xb,c[1])^_mul(0xd,c[2])^_mul(0x9,c[3]),
            _mul(0x9,c[0])^_mul(0xe,c[1])^_mul(0xb,c[2])^_mul(0xd,c[3]),
            _mul(0xd,c[0])^_mul(0x9,c[1])^_mul(0xe,c[2])^_mul(0xb,c[3]),
            _mul(0xb,c[0])^_mul(0xd,c[1])^_mul(0x9,c[2])^_mul(0xe,c[3])]
def _mix_columns(s):
    r=[]
    for i in range(4): r+=_mix_col([s[i*4],s[i*4+1],s[i*4+2],s[i*4+3]])
    return r
def _inv_mix_columns(s):
    r=[]
    for i in range(4): r+=_inv_mix_col([s[i*4],s[i*4+1],s[i*4+2],s[i*4+3]])
    return r
def _add_round_key(s,rk): return [a^b for a,b in zip(s,rk)]
def _key_expansion(key):
    n=len(key)//4; nr=n+6
    w=[list(key[i*4:i*4+4]) for i in range(n)]
    rcon=[0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36]
    for i in range(n,4*(nr+1)):
        temp=w[i-1][:]
        if i%n==0: temp=[_sbox[temp[1]]^rcon[i//n-1],_sbox[temp[2]],_sbox[temp[3]],_sbox[temp[0]]]
        elif n>6 and i%n==4: temp=[_sbox[b] for b in temp]
        w.append([a^b for a,b in zip(w[i-n],temp)])
    rks=[]
    for i in range(nr+1): rks+=w[i*4]+w[i*4+1]+w[i*4+2]+w[i*4+3]
    return rks, nr

def _aes_decrypt_block(ct, rks, nr):
    s=list(ct)
    s=_add_round_key(s, rks[nr*16:(nr+1)*16])
    for r in range(nr-1,-1,-1):
        s=_inv_shift_rows(s); s=_inv_sub_bytes(s)
        s=_add_round_key(s, rks[r*16:(r+1)*16])
        if r>0: s=_inv_mix_columns(s)
    return bytes(s)

def _pure_python_aes_cbc_decrypt(key, iv, ciphertext):
    rks, nr = _key_expansion(key)
    out=b''
    prev=iv
    for i in range(0,len(ciphertext),16):
        blk=ciphertext[i:i+16]
        dec=_aes_decrypt_block(blk, rks, nr)
        out+=bytes(a^b for a,b in zip(dec,prev))
        prev=blk
    pad=out[-1]
    return out[:-pad]


def _evp_bytes_to_key(password_bytes, salt_bytes, dklen=48):
    d = b''
    prev = b''
    while len(d) < dklen:
        prev = hashlib.md5(prev + password_bytes + salt_bytes).digest()
        d += prev
    return d[:dklen]


def _cryptojs_decrypt(enc_json_raw, password):
    log('[%s] _cryptojs_decrypt called' % SITE_NAME, LOGDEBUG)
    try:
        enc_json_str = enc_json_raw.replace('\\"', '"').replace('\\/', '/')
        data  = json.loads(enc_json_str)
        ct    = base64.b64decode(data['ct'])
        iv    = bytes.fromhex(data['iv'])
        salt  = bytes.fromhex(data['s'])
        kiv   = _evp_bytes_to_key(password.encode('utf-8'), salt, dklen=48)
        key   = kiv[:32]
        log('[%s] _cryptojs_decrypt: key=%s iv=%s HAS_CRYPTO=%s' % (SITE_NAME, key.hex(), iv.hex(), HAS_CRYPTO), LOGDEBUG)
        if HAS_CRYPTO:
            cipher = _AES.new(key, _AES.MODE_CBC, iv)
            result = _unpad(cipher.decrypt(ct), _AES.block_size).decode('utf-8')
        else:
            result = _pure_python_aes_cbc_decrypt(key, iv, ct).decode('utf-8')
        log('[%s] _cryptojs_decrypt: OK -> %s' % (SITE_NAME, result[:80]), LOGDEBUG)
        return result
    except Exception as e:
        logger.error('moviedream _cryptojs_decrypt: %s' % str(e))
        log('[%s] _cryptojs_decrypt: Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)
        return None


def load():
    log('[%s] Load %s' % (SITE_NAME, SITE_NAME), LOGDEBUG)
    logger.info('Load %s' % SITE_NAME)
    addDirectoryItem('Kino',      'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_KINO),      SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Filme',     'runPlugin&site=%s&function=showMovieMenu'       % SITE_NAME,                  SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Serien',    'runPlugin&site=%s&function=showSeriesMenu'      % SITE_NAME,                  SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Suche',     'runPlugin&site=%s&function=showSearch'          % SITE_NAME,                  SITE_ICON, 'DefaultAddonsSearch.png')
    setEndOfDirectory()



def showMovieMenu():
    log('[%s] showMovieMenu called' % SITE_NAME, LOGDEBUG)
    addDirectoryItem('Neueste', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES_NEW),    SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Beliebt', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES_TOP),    SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Zufall',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_MOVIES_RANDOM), SITE_ICON, 'DefaultMovies.png')
    addDirectoryItem('Genre',   'runPlugin&site=%s&function=showMovieGenres'      % SITE_NAME,                     SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showMovieGenres():
    log('[%s] showMovieGenres called' % SITE_NAME, LOGDEBUG)
    for sLabel, sPath in FILM_GENRES:
        sUrl = URL_MAIN + sPath
        addDirectoryItem(sLabel, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()



def showSeriesMenu():
    log('[%s] showSeriesMenu called' % SITE_NAME, LOGDEBUG)
    addDirectoryItem('Neueste', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES_NEW),    SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Beliebt', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES_TOP),    SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Zufall',  'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, URL_SERIES_RANDOM), SITE_ICON, 'DefaultTVShows.png')
    addDirectoryItem('Genre',   'runPlugin&site=%s&function=showSeriesGenres'     % SITE_NAME,                     SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()


def showSeriesGenres():
    log('[%s] showSeriesGenres called' % SITE_NAME, LOGDEBUG)
    for sLabel, sPath in SERIEN_GENRES:
        sUrl = URL_MAIN + sPath
        addDirectoryItem(sLabel, 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultGenre.png')
    setEndOfDirectory()

def _getNextPageUrl(sHtml, entryUrl):
    m_last = re.search(r'if\s*\(\s*(\d+)\s*==\s*(\d+)\s*\)\s*\{\s*\$\(["\']\.righter', sHtml)
    if m_last:
        current = int(m_last.group(1))
        last    = int(m_last.group(2))
        log('[%s] _getNextPageUrl: Seite %d von %d' % (SITE_NAME, current, last), LOGDEBUG)
        if current >= last:
            log('[%s] _getNextPageUrl: letzte Seite erreicht' % SITE_NAME, LOGDEBUG)
            return None
        nextP = current + 1
    else:
        m_cur = re.search(r'class="pagenumberselected"[^>]*href="\?p=(\d+)"', sHtml)
        if not m_cur:
            log('[%s] _getNextPageUrl: pagenumberselected nicht gefunden' % SITE_NAME, LOGDEBUG)
            return None
        nextP = int(m_cur.group(1)) + 1

    baseUrl = re.sub(r'\?p=\d+', '', entryUrl).rstrip('?')
    nextUrl = baseUrl + '?p=%d' % nextP
    log('[%s] _getNextPageUrl: naechste Seite -> %s' % (SITE_NAME, nextUrl), LOGDEBUG)
    return nextUrl


def showEntries(entryUrl=None, sSearchText=None, bGlobal=False):
    log('[%s] showEntries called - entryUrl: %s, sSearchText: %s, bGlobal: %s' % (SITE_NAME, entryUrl, sSearchText, bGlobal), LOGDEBUG)
    if not entryUrl: entryUrl = params.getValue('sUrl')
    log('[%s] showEntries: Using entryUrl: %s' % (SITE_NAME, entryUrl), LOGDEBUG)

    oRequest = cRequestHandler(entryUrl)
    oRequest.addHeaderEntry('User-Agent', UA)
    oRequest.addHeaderEntry('Referer', URL_MAIN + '/')
    oRequest.cacheTime = 60 * 60 * 4
    sHtmlContent = oRequest.request()

    if not sHtmlContent:
        log('[%s] showEntries: Leere Antwort von %s' % (SITE_NAME, entryUrl), LOGDEBUG)
        setEndOfDirectory()
        return

    log('[%s] showEntries: HTML Content Laenge: %d' % (SITE_NAME, len(sHtmlContent)), LOGDEBUG)

    pattern = (r'<a[^>]*class="linkto"[^>]*href="((?:film|serie)/[^"]+)"[^>]*>'
               r'[\s\S]*?<div[^>]*class="imgboxwiths"[^>]*>'
               r'<img[^>]*src="([^"]+)"[^>]*>'
               r'([^<]+)'
               r'</div>')
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    log('[%s] showEntries: Pattern-Match: %s, Treffer: %d' % (SITE_NAME, isMatch, len(aResult) if isMatch else 0), LOGDEBUG)

    if not isMatch:
        log('[%s] showEntries: Kein Match auf %s' % (SITE_NAME, entryUrl), LOGDEBUG)
        setEndOfDirectory()
        return

    items  = []
    hNames = []

    for sRelUrl, sThumbnail, sName in aResult:
        sName = sName.strip()
        if not sName: continue
        if sSearchText:
            if not all(w.lower() in sName.lower() for w in sSearchText.split()): continue

        isTvshow = sRelUrl.startswith('serie/')
        sUrl = URL_MAIN + '/' + sRelUrl

        if sThumbnail.startswith('http'): pass
        elif sThumbnail.startswith('//'): sThumbnail = 'https:' + sThumbnail
        else: sThumbnail = URL_MAIN + '/' + sThumbnail.lstrip('/')

        if isTvshow:
            if sName in hNames: continue
            hNames.append(sName)

        infoTitle = sName
        if bGlobal: sName = SITE_NAME + ' - ' + sName

        item = {}
        item.setdefault('infoTitle', infoTitle)
        item.setdefault('title',     sName)
        item.setdefault('entryUrl',  sUrl)
        item.setdefault('isTvshow',  isTvshow)
        item.setdefault('poster',    sThumbnail)
        item.setdefault('plot',      '[B][COLOR blue]%s[/COLOR][/B][CR]%s[CR]' % (SITE_NAME, infoTitle))
        items.append(item)

    if not items:
        log('[%s] showEntries: Keine Eintraege fuer %s' % (SITE_NAME, entryUrl), LOGDEBUG)
        setEndOfDirectory()
        return

    log('[%s] showEntries: Zeige %d Items' % (SITE_NAME, len(items)), LOGDEBUG)
    xsDirectory(items, SITE_NAME)

    if bGlobal: return

    if not sSearchText:
        sNextUrl = _getNextPageUrl(sHtmlContent, entryUrl)
        if sNextUrl and sNextUrl != entryUrl:
            log('[%s] showEntries: Naechste Seite: %s' % (SITE_NAME, sNextUrl), LOGDEBUG)
            addDirectoryItem('[B]>>>[/B]', 'runPlugin&site=%s&function=showEntries&sUrl=%s' % (SITE_NAME, sNextUrl), 'next.png', 'next.png')
        else:
            log('[%s] showEntries: Keine naechste Seite gefunden' % SITE_NAME, LOGDEBUG)

    setEndOfDirectory()



def _getMovieMeta(sHtml):
    log('[%s] _getMovieMeta called' % SITE_NAME, LOGDEBUG)
    meta = {}
    isM, v = cParser.parseSingleResult(sHtml, r'<h2[^>]*>\s*([^<]+?)\s*</h2>')
    if isM: meta['title'] = unescape(v.strip())
    isM, v = cParser.parseSingleResult(sHtml, r'<b>Regisseur:\s*</b>([^<]+)')
    if isM and v.strip() not in ('N/A', ''): meta['director'] = v.strip()
    isM, v = cParser.parseSingleResult(sHtml, r'<b>Schauspieler:\s*</b>([^<]+)')
    if isM and v.strip() not in ('N/A', ''): meta['cast'] = v.strip()
    isM, v = cParser.parseSingleResult(sHtml, r'<b>Genre:\s*</b>([^<]+)')
    if isM: meta['genre'] = v.strip()
    isM, v = cParser.parseSingleResult(sHtml, r'<b>L.nge:\s*</b>(\d+)')
    if isM:
        try: meta['duration'] = int(v)
        except: pass
    isM, v = cParser.parseSingleResult(sHtml, r'<b>Jahr:\s*</b>(\d{4})')
    if isM:
        try: meta['year'] = int(v)
        except: pass
    isM, v = cParser.parseSingleResult(sHtml, r'<b>IMDB Rating:\s*</b>([\d.,]+)\s*/\s*10')
    if isM:
        try: meta['rating'] = float(v.replace(',', '.'))
        except: pass
    isM, v = cParser.parseSingleResult(sHtml, r'src="(\.\./\.\./cover/[^"]+)"')
    if not isM:
        isM, v = cParser.parseSingleResult(sHtml, r'src="(cover/[^"]+)"')
    if isM:
        p = v
        if not p.startswith('http'):
            p = URL_MAIN + '/' + p.lstrip('.').lstrip('/')
        meta['poster'] = p
    isM, v = cParser.parseSingleResult(sHtml, r'<p\s[^>]*style="font-size:\s*16px[^"]*"[^>]*>([^<]+)</p>')
    if not isM:
        isM, v = cParser.parseSingleResult(sHtml, r'<p\s[^>]*style="font-size:\s*16px[^"]*"[^>]*>(.*?)</p>')
    if isM:
        try: v = unescape(v.strip())
        except: pass
        meta['plot'] = v
    log('[%s] _getMovieMeta: Ergebnis: %s' % (SITE_NAME, str(meta)), LOGDEBUG)
    return meta


def _buildPlot(meta, infoTitle=''):
    parts = ['[B][COLOR blue]%s[/COLOR][/B]' % SITE_NAME]
    t = meta.get('title') or infoTitle
    if t: parts.append('[B]%s[/B]' % t)
    info = []
    if meta.get('year'):     info.append('[B]Jahr:[/B] %s'       % meta['year'])
    if meta.get('duration'): info.append('[B]Laenge:[/B] %s Min.' % meta['duration'])
    if meta.get('genre'):    info.append('[B]Genre:[/B] %s'      % meta['genre'])
    if meta.get('director'): info.append('[B]Regie:[/B] %s'      % meta['director'])
    if meta.get('cast'):     info.append('[B]Cast:[/B] %s'       % meta['cast'])
    if meta.get('rating'):   info.append('[B]IMDB:[/B] %.1f/10'  % meta['rating'])
    if info: parts.append('  '.join(info))
    if meta.get('plot'): parts.append('[CR]' + meta['plot'])
    return '[CR]'.join(parts)


def showSeasons():
    log('[%s] showSeasons called' % SITE_NAME, LOGDEBUG)
    sUrl  = params.getValue('entryUrl')
    meta  = json.loads(params.getValue('meta'))
    log('[%s] showSeasons: URL: %s' % (SITE_NAME, sUrl), LOGDEBUG)

    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('User-Agent', UA)
    oRequest.cacheTime = 60 * 60 * 12
    sHtmlContent = oRequest.request()
    log('[%s] showSeasons: HTML Laenge: %d' % (SITE_NAME, len(sHtmlContent)), LOGDEBUG)

    detailMeta = _getMovieMeta(sHtmlContent)
    sPlot      = _buildPlot(detailMeta, meta.get('infoTitle', ''))
    if detailMeta.get('poster'): meta['poster'] = detailMeta['poster']

    isMatch, aSeasons = cParser.parse(sHtmlContent, r'id="seasonbutton(\d+)"')
    log('[%s] showSeasons: seasonbutton Match: %s -> %s' % (SITE_NAME, isMatch, aSeasons if isMatch else []), LOGDEBUG)
    if not isMatch:
        isMatch, aSeasons = cParser.parse(sHtmlContent, r'href="[^"]+/staffel-(\d+)"')
        log('[%s] showSeasons: staffel-href Fallback: %s -> %s' % (SITE_NAME, isMatch, aSeasons if isMatch else []), LOGDEBUG)
    if not isMatch:
        aSeasons = ['1']
        log('[%s] showSeasons: Keine Staffeln, nutze [1]' % SITE_NAME, LOGDEBUG)

    items = []
    for sSeason in aSeasons:
        item = {}
        item.setdefault('title',     'Staffel ' + sSeason)
        item.setdefault('entryUrl',  sUrl)
        item.setdefault('poster',    meta.get('poster', ''))
        item.setdefault('season',    sSeason)
        item.setdefault('infoTitle', meta.get('infoTitle', ''))
        item.setdefault('sFunction', 'showEpisodes')
        item.setdefault('isTvshow',  True)
        item.setdefault('plot',      sPlot)
        items.append(item)

    log('[%s] showSeasons: Zeige %d Staffeln' % (SITE_NAME, len(items)), LOGDEBUG)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory(sorted=True)


def showEpisodes():
    log('[%s] showEpisodes called' % SITE_NAME, LOGDEBUG)
    sUrl    = params.getValue('entryUrl')
    meta    = json.loads(params.getValue('meta'))
    sSeason = meta['season']
    log('[%s] showEpisodes: URL: %s, Staffel: %s' % (SITE_NAME, sUrl, sSeason), LOGDEBUG)

    sStaffelUrl = sUrl.rstrip('/') + '/staffel-' + str(sSeason)
    log('[%s] showEpisodes: Staffel-URL: %s' % (SITE_NAME, sStaffelUrl), LOGDEBUG)

    oRequest = cRequestHandler(sStaffelUrl)
    oRequest.addHeaderEntry('User-Agent', UA)
    oRequest.cacheTime = 60 * 60 * 12
    sHtmlContent = oRequest.request()
    log('[%s] showEpisodes: HTML Laenge: %d' % (SITE_NAME, len(sHtmlContent) if sHtmlContent else 0), LOGDEBUG)

    pattern = r'href="(/serie/[^"]+/staffel-%s/episode-(\d+))"' % re.escape(str(sSeason))
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    log('[%s] showEpisodes: Pattern Match: %s, Treffer: %d' % (SITE_NAME, isMatch, len(aResult) if isMatch else 0), LOGDEBUG)

    if not isMatch:
        log('[%s] showEpisodes: Keine Episoden Staffel %s' % (SITE_NAME, sSeason), LOGDEBUG)
        setEndOfDirectory()
        return

    items = []
    for sEpRelUrl, sEpisode in aResult:
        sEpUrl = URL_MAIN + sEpRelUrl
        item = {}
        item.setdefault('title',     'Folge ' + sEpisode)
        item.setdefault('entryUrl',  sEpUrl)
        item.setdefault('poster',    meta.get('poster', ''))
        item.setdefault('season',    int(sSeason))
        item.setdefault('episode',   int(sEpisode))
        item.setdefault('infoTitle', meta.get('infoTitle', ''))
        item.setdefault('isTvshow',  True)
        item.setdefault('sFunction', 'getHosters')
        item.setdefault('plot',      meta.get('plot', ''))
        items.append(item)
        log('[%s] showEpisodes: Folge %s -> %s' % (SITE_NAME, sEpisode, sEpUrl), LOGDEBUG)

    log('[%s] showEpisodes: Zeige %d Episoden' % (SITE_NAME, len(items)), LOGDEBUG)
    xsDirectory(items, SITE_NAME)
    setEndOfDirectory()


def getHosters():
    log('[%s] getHosters called' % SITE_NAME, LOGDEBUG)
    isProgressDialog = True
    isResolve        = True
    items            = []

    sUrl = params.getValue('entryUrl')
    if sUrl.startswith('//'): sUrl = 'https:' + sUrl
    log('[%s] getHosters: URL: %s' % (SITE_NAME, sUrl), LOGDEBUG)

    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('User-Agent', UA)
    oRequest.addHeaderEntry('Referer', URL_MAIN + '/')
    oRequest.cacheTime = 0
    sHtmlContent = oRequest.request()
    log('[%s] getHosters: HTML Laenge: %d' % (SITE_NAME, len(sHtmlContent) if sHtmlContent else 0), LOGDEBUG)

    detailMeta = _getMovieMeta(sHtmlContent)
    meta       = json.loads(params.getValue('meta'))
    log('[%s] getHosters: Meta: %s' % (SITE_NAME, str(meta)), LOGDEBUG)

    if detailMeta.get('poster'):   meta['poster']   = detailMeta['poster']
    if detailMeta.get('year'):     meta['year']     = detailMeta['year']
    if detailMeta.get('genre'):    meta['genre']    = detailMeta['genre']
    if detailMeta.get('cast'):     meta['cast']     = detailMeta['cast']
    if detailMeta.get('rating'):   meta['rating']   = detailMeta['rating']
    if detailMeta.get('duration'): meta['duration'] = detailMeta['duration']
    if detailMeta.get('director'): meta['director'] = detailMeta['director']
    meta['plot'] = _buildPlot(detailMeta, meta.get('infoTitle', ''))

    sThumbnail = meta.get('poster', '')
    if meta.get('isTvshow', False):
        sTitle = '%s S%02dE%02d' % (meta['infoTitle'], int(meta.get('season', 0)), int(meta.get('episode', 0)))
        meta.setdefault('mediatype', 'tvshow')
    else:
        sTitle = meta.get('infoTitle', '')
        meta.setdefault('mediatype', 'movie')

    log('[%s] getHosters: Titel: %s' % (SITE_NAME, sTitle), LOGDEBUG)
    enc_list_pat = r"CryptoJSAesJson\.decrypt\s*\(\s*'(\{(?:[^'\\]|\\.)+\})'\s*,\s*'[^']+'\s*\)"
    isMatch, enc_jsons = cParser.parse(sHtmlContent, enc_list_pat)

    log('[%s] getHosters: CryptoJS-Bloecke: Match=%s Anzahl=%d' % (SITE_NAME, isMatch, len(enc_jsons) if isMatch else 0), LOGDEBUG)
    _, logo_names = cParser.parse(sHtmlContent, r"hosterlogos/([A-Za-z0-9_-]+?)(?:HD)?\.png")
    log('[%s] getHosters: Logos gefunden: %s' % (SITE_NAME, logo_names), LOGDEBUG)

    aResult = []
    if isMatch:
        for i, enc_json in enumerate(enc_jsons):
            log('[%s] getHosters: Entschluessel Block %d: %s...' % (SITE_NAME, i, enc_json[:50]), LOGDEBUG)
            decrypted = _cryptojs_decrypt(str(enc_json), CRYPTO_KEY)
            if decrypted:
                decrypted = decrypted.strip().strip('"').replace('\\/', '/')
            hname = logo_names[i] if i < len(logo_names) else 'Unknown'
            if decrypted.startswith('http'):
                aResult.append((decrypted, hname))
                log('[%s] getHosters: OK Hoster=%s URL=%s' % (SITE_NAME, hname, decrypted[:60]), LOGDEBUG)
            else:
                log('[%s] getHosters: Entschluesselung fehlgeschlagen: %s' % (SITE_NAME, hname), LOGDEBUG)


    if not aResult:
        log('[%s] getHosters: Kein AES-Treffer, versuche Fallback' % SITE_NAME, LOGDEBUG)
        HOSTER_PAT = r'(?:videzz\.net|doodcdn\.(?:com|io|pro)|vinovo\.to|vidoza\.net|streamtape\.(?:com|to)|voe\.sx|mixdrop\.(?:co|to)|dood\.(?:la|re|to|watch))'
        fbPat = r'(?:href|data-url)=["\']?(https?://' + HOSTER_PAT + r'[^"\'>\s]*)["\']?[^>]*>\s*([^<]{2,40})'
        isMatch2, aResult2 = cParser.parse(sHtmlContent, fbPat)
        log('[%s] getHosters: Fallback Match=%s Treffer=%d' % (SITE_NAME, isMatch2, len(aResult2) if isMatch2 else 0), LOGDEBUG)
        if isMatch2:
            aResult = [(url, lbl.strip()) for url, lbl in aResult2]

    if not aResult:
        log('[%s] getHosters: Keine Hoster auf %s' % (SITE_NAME, sUrl), LOGDEBUG)
        xbmcgui.Dialog().notification('[B]%s[/B]' % SITE_NAME, 'Kein funktionierender Stream vorhanden', SITE_ICON, 5000)
        url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
        execute('Container.Update(%s)' % url)
        return

    log('[%s] getHosters: %d Hoster-Links gefunden' % (SITE_NAME, len(aResult)), LOGDEBUG)

    if isProgressDialog: progressDialog.create(SITE_NAME, 'Erstelle Hosterliste ...')
    t = 0

    for sHosterUrl, sHosterLabel in aResult:
        t += 100 / len(aResult)
        hoster = sHosterLabel.strip().rstrip(' HD') or _hosterNameFromUrl(sHosterUrl)
        if isProgressDialog: progressDialog.update(int(t), '[CR]Ueberpruefe ' + hoster.upper())
        log('[%s] getHosters: Verarbeite Hoster=%s URL=%s' % (SITE_NAME, hoster, sHosterUrl), LOGDEBUG)

        resolvedUrl = sHosterUrl
        if 'vinovo.to' in sHosterUrl:
            log('[%s] getHosters: Loese Vinovo auf: %s' % (SITE_NAME, sHosterUrl), LOGDEBUG)
            resolvedUrl = _resolveVinovo(sHosterUrl) or sHosterUrl
            log('[%s] getHosters: Vinovo aufgeloest: %s' % (SITE_NAME, resolvedUrl), LOGDEBUG)

        if isResolve:
            isBlocked, resolvedUrl = isBlockedHoster(resolvedUrl, resolve=isResolve)
            if not resolvedUrl:
                resolvedUrl = sHosterUrl
            log('[%s] getHosters: isBlocked=%s resolvedUrl=%s' % (SITE_NAME, isBlocked, resolvedUrl), LOGDEBUG)
            #if isBlocked:
                #log('[%s] getHosters: Blockiert: %s' % (SITE_NAME, hoster), LOGDEBUG)
                #continue
        elif isBlockedHoster(hoster)[0]:
            log('[%s] getHosters: Label blockiert: %s' % (SITE_NAME, hoster), LOGDEBUG)
            continue

        slim_meta = {k: meta[k] for k in ('infoTitle', 'title', 'poster', 'isTvshow', 'season', 'episode', 'mediatype', 'year', 'rating') if k in meta}
        items.append((hoster, sTitle, slim_meta, isResolve, resolvedUrl, sThumbnail))
        log('[%s] getHosters: Hinzugefuegt: %s' % (SITE_NAME, hoster), LOGDEBUG)

    if isProgressDialog: progressDialog.close()
    log('[%s] getHosters: Gesamt Items: %d' % (SITE_NAME, len(items)), LOGDEBUG)

    if len(items) == 0:
        log('[%s] getHosters: Keine gueltigen Hoster!' % SITE_NAME, LOGDEBUG)
        xbmcgui.Dialog().notification('[B]%s[/B]' % SITE_NAME, 'Kein funktionierender Stream vorhanden', SITE_ICON, 5000)

    url = '%s?action=showHosters&items=%s' % (sys.argv[0], quote(json.dumps(items)))
    log('[%s] getHosters: Container.Update: %s' % (SITE_NAME, url[:100]), LOGDEBUG)
    execute('Container.Update(%s)' % url)


def _resolveVinovo(embedUrl):
    log('[%s] _resolveVinovo: %s' % (SITE_NAME, embedUrl), LOGDEBUG)
    try:
        isMatch, fileId = cParser.parseSingleResult(embedUrl, r'/(?:d|e|f)/([a-z0-9]+)')
        if not isMatch:
            log('[%s] _resolveVinovo: keine fileId' % SITE_NAME, LOGDEBUG)
            return None
        log('[%s] _resolveVinovo: fileId=%s' % (SITE_NAME, fileId), LOGDEBUG)
        apiUrl   = 'https://vinovo.to/api/file/url/' + fileId
        oRequest = cRequestHandler(apiUrl)
        oRequest.setRequestType(1)
        oRequest.addHeaderEntry('User-Agent', UA)
        oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        oRequest.addHeaderEntry('Origin',  'https://vinovo.to')
        oRequest.addHeaderEntry('Referer', 'https://vinovo.to/d/' + fileId)
        oRequest.addHeaderEntry('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        oRequest.cacheTime = 0
        sResponse = oRequest.request()
        log('[%s] _resolveVinovo: Antwort: %s' % (SITE_NAME, sResponse[:120] if sResponse else 'leer'), LOGDEBUG)
        try: jData = json.loads(sResponse)
        except:
            log('[%s] _resolveVinovo: JSON-Parse-Fehler' % SITE_NAME, LOGDEBUG)
            return None
        streamUrl = (jData.get('url') or jData.get('stream_url')
                     or jData.get('file') or jData.get('hls') or jData.get('mp4'))
        if not streamUrl and 'sources' in jData:
            src = jData['sources']
            streamUrl = src[0].get('file') if src else None
        log('[%s] _resolveVinovo: Stream-URL: %s' % (SITE_NAME, streamUrl), LOGDEBUG)
        return streamUrl
    except Exception as e:
        logger.error('%s _resolveVinovo: %s' % (SITE_NAME, str(e)))
        log('[%s] _resolveVinovo: Fehler: %s' % (SITE_NAME, str(e)), LOGDEBUG)
        return None


def _hosterNameFromUrl(url):
    for name in ('videzz', 'doodcdn', 'dood', 'vinovo', 'vidoza', 'streamtape', 'voe', 'mixdrop'):
        if name in url: return name.capitalize()
    return 'Unknown'

def showSearch():
    log('[%s] showSearch called' % SITE_NAME, LOGDEBUG)
    sSearchText = oNavigator.showKeyBoard()
    if not sSearchText: return
    log('[%s] showSearch: Text: %s' % (SITE_NAME, sSearchText), LOGDEBUG)
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=False)


def _search(sSearchText):
    log('[%s] _search: %s' % (SITE_NAME, sSearchText), LOGDEBUG)
    showEntries(URL_SEARCH % quote_plus(sSearchText), sSearchText, bGlobal=True)
