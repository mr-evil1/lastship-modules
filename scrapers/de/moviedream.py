# -*- coding: UTF-8 -*-
import re, json, base64, hashlib

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

from scrapers.modules.tools import cParser
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import source_utils
from resources.lib.control import getSetting

SITE_IDENTIFIER = 'moviedream'
SITE_DOMAIN     = 'moviedream.cx'
SITE_NAME       = 'MovieDream'
CRYPTO_KEY      = 'a2mZz5S76@2s'

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
_inv_sbox = [0] * 256
for _i, _v in enumerate(_sbox):
    _inv_sbox[_v] = _i

def _mul(a, b):
    r = 0
    for _ in range(8):
        if b & 1: r ^= a
        hi = a & 0x80; a = (a << 1) & 0xff
        if hi: a ^= 0x1b
        b >>= 1
    return r

def _inv_shift_rows(s):
    return [s[0],s[13],s[10],s[7],s[4],s[1],s[14],s[11],
            s[8],s[5],s[2],s[15],s[12],s[9],s[6],s[3]]

def _inv_mix_col(c):
    return [_mul(0xe,c[0])^_mul(0xb,c[1])^_mul(0xd,c[2])^_mul(0x9,c[3]),
            _mul(0x9,c[0])^_mul(0xe,c[1])^_mul(0xb,c[2])^_mul(0xd,c[3]),
            _mul(0xd,c[0])^_mul(0x9,c[1])^_mul(0xe,c[2])^_mul(0xb,c[3]),
            _mul(0xb,c[0])^_mul(0xd,c[1])^_mul(0x9,c[2])^_mul(0xe,c[3])]

def _key_expansion(key):
    n = len(key) // 4; nr = n + 6
    w = [list(key[i*4:i*4+4]) for i in range(n)]
    rcon = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36]
    for i in range(n, 4*(nr+1)):
        temp = w[i-1][:]
        if i % n == 0:
            temp = [_sbox[temp[1]]^rcon[i//n-1],_sbox[temp[2]],_sbox[temp[3]],_sbox[temp[0]]]
        elif n > 6 and i % n == 4:
            temp = [_sbox[b] for b in temp]
        w.append([a^b for a, b in zip(w[i-n], temp)])
    rks = []
    for i in range(nr+1): rks += w[i*4]+w[i*4+1]+w[i*4+2]+w[i*4+3]
    return rks, nr

def _aes_decrypt_block(ct, rks, nr):
    s = list(ct)
    s = [a^b for a,b in zip(s, rks[nr*16:(nr+1)*16])]
    for r in range(nr-1, -1, -1):
        s = _inv_shift_rows(s)
        s = [_inv_sbox[b] for b in s]
        s = [a^b for a,b in zip(s, rks[r*16:(r+1)*16])]
        if r > 0:
            tmp = []
            for i in range(4): tmp += _inv_mix_col([s[i*4],s[i*4+1],s[i*4+2],s[i*4+3]])
            s = tmp
    return bytes(s)

def _pure_aes_cbc_decrypt(key, iv, ciphertext):
    rks, nr = _key_expansion(key)
    out = b''; prev = iv
    for i in range(0, len(ciphertext), 16):
        blk = ciphertext[i:i+16]
        dec = _aes_decrypt_block(blk, rks, nr)
        out += bytes(a^b for a,b in zip(dec, prev))
        prev = blk
    pad = out[-1]
    return out[:-pad]

def _evp_bytes_to_key(pwd, salt, dklen=48):
    d = b''; prev = b''
    while len(d) < dklen:
        prev = hashlib.md5(prev + pwd + salt).digest()
        d += prev
    return d[:dklen]

def _cryptojs_decrypt(enc_json_raw, password):
    try:
        data  = json.loads(enc_json_raw.replace('\\"', '"').replace('\\/', '/'))
        ct    = base64.b64decode(data['ct'])
        iv    = bytes.fromhex(data['iv'])
        salt  = bytes.fromhex(data['s'])
        kiv   = _evp_bytes_to_key(password.encode('utf-8'), salt)
        key   = kiv[:32]
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            result = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16).decode('utf-8')
        except ImportError:
            result = _pure_aes_cbc_decrypt(key, iv, ct).decode('utf-8')
        return result.strip().strip('"').replace('\\/', '/')
    except Exception:
        return None



class source:
    def parse_quality(self, url):
        u = url.lower()
        if '2160' in u or '4k'   in u: return '4K'
        if '1080' in u:                return '1080p'
        if '720'  in u:                return '720p'
        if '480'  in u:                return '480p'
        return 'HD'

    def __init__(self):
        self.priority    = 1
        self.language    = ['de']
        self.domain      = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link   = 'https://' + self.domain
        self.search_link = self.base_link + '/searchy.php?ser=%s'
        self.imdb_link   = (self.base_link +
                            '/suchergebnisse.php?text=&imdbid=%s'
                            '&jahr=&sprache=Deutsch&genre=&regie='
                            '&schauspieler1=&schauspieler2=')
        self.sources     = []

    def _search_by_imdb(self, imdb, is_serie):
        """Sucht per suchergebnisse.php anhand der IMDB-ID.
        Akzeptiert imdb mit oder ohne 'tt'-Prefix; gibt erste passende URL zurueck oder None."""
        if not imdb:
            return None
        numeric_id = imdb[2:] if imdb.lower().startswith('tt') else imdb
        if not numeric_id.isdigit():
            return None

        prefix = 'serie/' if is_serie else 'film/'
        pat = r'href=["\'](((?:film|serie)/\d+)[^"\']*)["\']'

        oRequest = cRequestHandler(self.imdb_link % numeric_id, caching=True)
        sHtml    = oRequest.request()
        if not sHtml:
            return None

        isMatch, aResult = cParser.parse(sHtml, pat)
        if not isMatch:
            return None

        for full_path, base in aResult:
            if base.startswith(prefix):
                return self.base_link + '/' + full_path
        return None

    def _search(self, titles, is_serie):
        """Sucht per searchy.php, gibt erste passende URL zurueck oder None."""
        prefix = 'serie/' if is_serie else 'film/'
        pat = r'href=["\'](/((?:film|serie)/[^"\']*))["\']'  # single- und double-quote
        for title in titles:
            oRequest = cRequestHandler(self.search_link % quote_plus(title), caching=True)
            sHtml    = oRequest.request()
            if not sHtml: continue
            isMatch, aResult = cParser.parse(sHtml, pat)
            if not isMatch: continue
            for full_path, rel in aResult:
                if rel.startswith(prefix):
                    return self.base_link + full_path
        return None

    def _get_hosters(self, sHtml, hostDict):
        """Entschluesselt CryptoJS-Bloecke und gibt gueltige Hoster-URLs zurueck."""
        enc_pat = r"CryptoJSAesJson\.decrypt\s*\(\s*'(\{(?:[^'\\]|\\.)+\})'\s*,\s*'[^']+'\s*\)"
        isMatch, enc_jsons = cParser.parse(sHtml, enc_pat)
        _, logo_names      = cParser.parse(sHtml, r"hosterlogos/([A-Za-z0-9_-]+?)(?:HD)?\.png")

        result = []
        if isMatch:
            for i, enc in enumerate(enc_jsons):
                url = _cryptojs_decrypt(str(enc), CRYPTO_KEY)
                if url and url.startswith('http'):
                    result.append(url)

        for url in result:
            valid, hoster = source_utils.is_host_valid(url, hostDict)
            if not valid: continue
            self.sources.append({
                'source':   hoster,
                'quality':  self.parse_quality(url),
                'language': 'de',
                'url':      url,
                'direct':   False,
            })

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        try:
            is_serie = season != 0
            sUrl = self._search_by_imdb(imdb, is_serie) or self._search(titles, is_serie)
            if not sUrl: return self.sources

            if not is_serie:
                oRequest = cRequestHandler(sUrl, caching=True)
                sHtml    = oRequest.request()
            else:
                epUrl    = sUrl.rstrip('/') + '/staffel-%s/episode-%s' % (season, episode)
                oRequest = cRequestHandler(epUrl, caching=True)
                sHtml    = oRequest.request()

            if sHtml:
                self._get_hosters(sHtml, hostDict)

        except Exception:
            pass

        return self.sources

    def resolve(self, url):
        return url
