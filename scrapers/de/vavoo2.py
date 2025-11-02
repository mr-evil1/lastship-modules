# -*- coding: utf-8 -*-
import json, random, xbmcgui, time, os
import requests
from base64 import b64encode, b64decode
from scrapers.modules import source_utils
from scrapers.modules.tools import cParser

SITE_IDENTIFIER = 'vavoo'
SITE_DOMAIN = 'vavoo.to'
SITE_NAME = SITE_IDENTIFIER.upper()

session = requests.session()

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['vavoo.to']
        self.base_link = 'https://' + self.domains[0] +'/'
        self.BASEURL = self.base_link +'ccapi/'


    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        action = 'links'
        params = dict()
        if season == 0:
            mediatype = 'movie'
            params['id'] = '%s.%s' % (mediatype, imdb)
        else:
            V2_API_KEY = '4a65e1e644af74c98f9f2b3884669deb3fac9531ee71f39babf1dee46d264d17'
            headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': '2'}
            sUrl = 'https://api.trakt.tv/shows/{0}'.format(imdb)
            result = requests.get(sUrl, headers=headers)
            result = json.loads(result.content)
            id = result['ids']['tmdb']
            mediatype = 'series'
            params['id'] = '%s.%s.%s.%s' % (mediatype, id, str(season), str(episode))

        params['language'] = 'de'

        data = self.callApi2(action, params)
        for i in data:
            if not 'language' in str(i): continue
            isMatch, quality = cParser.parseSingleResult(i['name'], "\(([^\)]+)")
            if not isMatch: quality = 'SD'
            url = i['url']
            valid, hoster = source_utils.is_host_valid(url, hostDict)
            if valid:
                sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': [url, False], 'info': i['name'] + ' | ' + i['language'], 'direct': False})


        return sources

    def resolve(self, url):
        if url[1]:
            params = {'link': url[0]}
            action = 'open'
            data = self.callApi2(action, params)
            url = data[0]['url']
            return self.unshorten(url)
        else:
            return url[0]

    def callApi(self, action, params, method='GET', headers=None, jsonreq=None):
        if not headers:
            headers = dict()
        headers['auth-token'] = self.getAuthSignature()
        if method == 'GET':
            resp = session.request(method, (self.BASEURL + action), params=params, headers=headers)
        else:
            resp = session.request(method, (self.BASEURL + action), params=params, headers=headers, json=jsonreq)
        data = resp.json()
        return data

    def callApi2(self, action, params):
        res = self.callApi(action, params)
        while True:
            if type(res) is not dict or 'id' not in res or 'data' not in res:
                return res
            data = res['data']
            if type(data) is dict and data.get('type') == 'fetch':
                params = data['params']
                body = params.get('body')
                headers = params.get('headers')
                resp = session.request(params.get('method', 'GET').upper(), data['url'], headers={k: v[0] if type(v) in (list, tuple) else v for k, v in list(headers.items())} if headers else None,
                                       data=b64decode(body) if body else None, allow_redirects=params.get('redirect', 'follow') == 'follow', verify=False)
                headers = dict(resp.headers)
                resData = {'status': resp.status_code,
                           'url': resp.url,
                           'headers': headers,
                           'data': b64encode(resp.content).decode("utf-8").replace('\n', '') if data['body'] else None}
                res = self.callApi('res', {'id': res['id']}, method='POST', jsonreq=resData)
            elif type(data) is dict and data.get('error'):
                raise ValueError(data['error'])
            else:
                return data

    def getAuthSignature(self):
        from resources.lib.control import dataPath as cachepath
        home = xbmcgui.Window(10000)

        def set_cache(key, value, timeout=300):
            data = {"sigValidUntil": int(time.time()) + timeout, "value": value}
            home.setProperty(key, json.dumps(data))
            file = os.path.join(cachepath, key)
            with open(file + ".json", "w") as k:
                json.dump(data, k, indent=4)

        def get_cache(key):
            keyfile = home.getProperty(key)
            if keyfile:
                r = json.loads(keyfile)
                if r.get('sigValidUntil', 0) > int(time.time()):
                    return r.get('value')
                home.clearProperty(key)
            try:
                file = os.path.join(cachepath, key)
                with open(file + ".json") as k:
                    r = json.load(k)
                sigValidUntil = r.get('sigValidUntil', 0)
                if sigValidUntil > int(time.time()):
                    value = r.get('value')
                    data = {"sigValidUntil": sigValidUntil, "value": value}
                    home.setProperty(key, json.dumps(data))
                    return value
                os.remove(file)
            except:
                return

        signfile = get_cache('signfile')
        if signfile: return signfile
        veclist = get_cache('veclist')
        if not veclist:
            veclist = requests.get("https://raw.githubusercontent.com/michaz1988/michaz1988.github.io/master/data.json").json()
            set_cache('veclist', veclist, timeout=3600)
        sig = None
        i = 0
        while (not sig and i < 50):
            i += 1
            vec = {"vec": random.choice(veclist)}
            req = requests.post('https://www.vavoo.tv/api/box/ping2', data=vec).json()
            if req.get('signed'):
                sig = req['signed']
            elif req.get('data', {}).get('signed'):
                sig = req['data']['signed']
            elif req.get('response', {}).get('signed'):
                sig = req['response']['signed']
        set_cache('signfile', sig)
        return sig

    def unshorten(self, url):
        from contextlib import closing
        with closing(session.head(url, verify=False)) as req:
            r = req
        if not r.headers.get('location'):
            return url
        tmp_url = url
        try:
            for redir in session.resolve_redirects(r, r.request, verify=False):
                if redir.status_code == 200: 
                    return redir.url
                else:
                    tmp_url = redir.url
            else: 
                return tmp_url
        except requests.exceptions.TooManyRedirects:
            return url
