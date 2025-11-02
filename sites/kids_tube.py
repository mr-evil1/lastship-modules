# -*- coding: utf-8 -*-


# 2024.11.01
import xbmc
import xbmcgui, sys, urllib, urllib.parse, xbmcplugin,xbmcaddon
import requests
import random

import json
from resources.lib.ParameterHandler import ParameterHandler
from resources.lib.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.control import progressDialog, quote_plus, unescape, quote, execute
from resources.lib.indexers.navigatorXS import navigator
from resources.lib.utils import isBlockedHoster
from resources.lib.control import getSetting
oNavigator = navigator()
addDirectoryItem = oNavigator.addDirectoryItem
setEndOfDirectory = oNavigator._endDirectory
xsDirectory = oNavigator.xsDirectory
params = ParameterHandler()
from resources.lib import youtube_fix
from resources.lib.control import getSetting,setSetting


addon = xbmcaddon.Addon
Addon = xbmcaddon.Addon

SITE_IDENTIFIER = 'kids_tube'
SITE_NAME = 'Kids Tube'
SITE_ICON = 'kids_tube.png'


ACTIVE = True


#################### Hauptmenü ####################

def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    # Abfrage ob Youtube installiert ist
    if getSetting('plugin_' + SITE_IDENTIFIER) == 'true':
        if not xbmc.getCondVisibility('System.HasAddon(%s)' % 'plugin.video.youtube'):
            xbmc.executebuiltin('InstallAddon(%s)' % 'plugin.video.youtube')
    #addDirectoryItem(SITE_NAME_1+" : Neues", 'runPlugin&site=%s&function=showEntries_1&sUrl=%s' % (SITE_NAME, URL_MAIN_1), SITE_ICON, 'DefaultMovies.png')
    #addDirectoryItem(SITE_NAME_1+" : Filme", 'runPlugin&site=%s&function=showEntries_1&sUrl=%s' % (SITE_NAME, URL_MOVIES_1), SITE_ICON, 'DefaultMovies.png')
    #addDirectoryItem(SITE_NAME_1+" : Genre", 'runPlugin&site=%s&function=showGenre_1&sUrl=%s' % (SITE_NAME, URL_MOVIES_1), SITE_ICON, 'DefaultMovies.png')
    #addDirectoryItem(SITE_NAME_1+" : Suche", 'runPlugin&site=%s&function=showSearch_1&sUrl=%s' % (SITE_NAME, URL_MOVIES_1), SITE_ICON, 'DefaultMovies.png')
    if not params.getValue("action1"):# == 'runPlugin':
        main_list()
    else:
        action1 = params.getValue("action1")
        if action1.startswith('#'):
            action1 = action1.split('#')[1]
            sub_listw(action1)
        elif action1.startswith('*'):
            action1 = action1.split('*')[1]
            search(action1)
        else:
            sub_list(action1)
    #close_item_list()
    setEndOfDirectory()

#################### Dokus4.me ####################

SITE_NAME_1 = 'Kinderserien.tv'
SITE_ICON_1 = 'kids_tube.png'
URL_MAIN_1 = 'https://kinderserien.tv/'
URL_MOVIES_1 = URL_MAIN_1 + 'serien/kinderfilme/'
URL_SERIES_1 = URL_MAIN_1 + 'serien/'
URL_SEARCH_1 = URL_MAIN_1 + '?s=%s'

def showGenre_1():
    params = ParameterHandler()
    oRequest = cRequestHandler(URL_MAIN_1)
    sHtmlContent = oRequest.request()
    pattern = 'Serien</h2>(.*?)</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
    if not isMatch:
        return

    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN_1 + sUrl
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_1&sUrl=%s' % (SITE_NAME, sUrl), SITE_ICON, 'DefaultMovies.png')
    setEndOfDirectory()

        
def showEntries_1(entryUrl=False,sSearchText=False,bGlobal=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + 'page/' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=True)
    sHtmlContent = oRequest.request()
    pattern = 'class="item-thumbnail">.*?href="([^"]+).*?title="([^"]+).*?src="([^"]+).*?'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showHosters_1&sThumbnail=%s&entryUrl=%s' % (SITE_NAME,sThumbnail, sUrl), SITE_ICON, 'DefaultMovies.png')

    if not bGlobal and not sSearchText:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        
        addDirectoryItem(sName, 'runPlugin&site=%s&function=showEntries_1&page=%s&sUrl=%s' % (SITE_NAME, int(sPageNr),sUrl), SITE_ICON, 'DefaultMovies.png')

    setEndOfDirectory()

def showHosters_1():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, aResult = cParser.parse(sHtmlContent, 'src="([^"]+)" f')
    if isMatch:
        for sUrl in aResult:
            sUrl = sUrl.split('?')[0].strip()
            hoster = {'link': sUrl, 'name': cParser.urlparse(sUrl)}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl_1')
    return hosters

def getHosterUrl_1(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]

def showSearch_1():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search_1(False, sSearchText)
    cGui().setEndOfDirectory()

def _search_1(oGui, sSearchText):
    showEntries_1(URL_SEARCH_1 % cParser().quotePlus(sSearchText), oGui, sSearchText)

#################### Youtube Kanäle ####################


URL_MAIN = 'http://www.youtube.com'
# URL_SEARCH = URL_MAIN + '?s=%s'

channellist = [
    ("[COLORred]YouTube:[/COLOR] Kanäle", "Kanäle", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Filme", "Kinder Filme", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Serien", "Kinder Serien", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Klassiker", "Kinder Klassiker", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Märchen", "Kinder Geschichten", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Hörbücher", "Kinder Buch", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Wissen", "Kinder Wissen", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
    ("[COLORred]YouTube:[/COLOR] Musik", "Kinder Musik", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
]

sublists = {
    'Kanäle': [
        ("[COLORyellow]KIKA[/COLOR] von ARD & ZDF", "user/meinKiKA", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORyellow]KiKANiNCHEN[/COLOR] von ARD & ZDF", "channel/UCv4Pvhg1LY8U9E-XF8hn6WA", "https://yt3.googleusercontent.com/PHGbrL1fSJgdN-1S69zDJ7GUVuw9ypSiq8skG1GAzxcESnwCgRYwv0yhe7sTR_5VS-NwjjIxyA=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORyellow]ZDFtivi[/COLOR] von ZDF", "user/ZDFtiviKinder", "Tivi.png"),
        ("[COLORyellow]Löwenzahn TV[/COLOR] von ZDF", "channel/UCOPJAVJeBhqWL8k7K9Wx6SQ", "Zahn.png"),
        ("[COLORyellow]Sesamstrasse[/COLOR] von NDR", "user/SesamstrasseNDR", "Sesam.png"),
        ("[COLORyellow]Kindernetz[/COLOR] von SWR", "user/Kindernetz", "Kinder.png"),
        ("[COLORyellow]Die Sendung mit der Maus[/COLOR] von WDR", "channel/UCRWSxXBnz9IRS4SgRhG2wpQ", "Maus.png"),
        ("[COLORyellow]Toggolino[/COLOR] von SuperRTL", "user/TOGGOLINOde", "Toggo.png"),
        ("[COLORyellow]Disney Channel[/COLOR] Deutschland", "user/DisneyChannelGermany", "Disney.png"),
        ("[COLORyellow]Disney Junior[/COLOR] Deutschland", "user/DisneyJuniorGermany", "DisneyJR.png"),
        ("[COLORyellow]Nickelodeon[/COLOR] Deutschland", "user/nickelodeonoffiziell", "Nick.png"),
        ("[COLORyellow]Boomerang[/COLOR] Deutschland", "user/BoomerangDE", "Boom.png"),
        ("[COLORyellow]Cartoon Network[/COLOR] Deutschland", "user/cartoonnetworkde", "Cartoon.png"),
        ("[COLORyellow]Kixi[/COLOR] Kinderfilme, Lehrfilme, Lernserien", "channel/UCF2IFFQyO5gbhvOCObh1WTQ", "Kixi.png"),
        ("[COLORyellow]Karussell[/COLOR] KinderTV", "channel/UCdT-eMkUGKqvVebDkn1KqlQ", "https://yt3.googleusercontent.com/95cCyBJIjuANCB5IDAyHvang2jGlPBt_jbY__nNHOz6gFH5ErboDnmqb879peVqKnWrRX4gJxA=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORyellow]Kinderlieder zum Mitsingen und Bewegen[/COLOR]", "channel/UCctbi1Jw2jiVhj2ogdwiFdA", "https://yt3.googleusercontent.com/BGoTUkK-TRjC6fC1fFP700dgrV5cjuHw-O8OcgGnqsHi3RoeU7b0hKm-0eS4dDOg-PWs5lz9Ew=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORyellow]Kinderlieder von Volker Rosin[/COLOR]", "channel/UC7HM-Pm3mLzZBvhJKFnL6oA", "https://yt3.googleusercontent.com/JJrATrwxWPSfcl96xTQqdKCsPoRu-szzn_NTvazvFG9Vx8aAvTHZBT_WuznsbOuiClwdTf0RXw=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORyellow]Ric TV[/COLOR]", "user/RICTVChannel", "Ric.png"),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Serien': [
        ("[COLORyellow]Feuerwehrman Sam[/COLOR]", "playlist/PLK-pDTpRfGThLNOPhnUn_442Sr3X94ehe", "Sam.png"),
        ("[COLORyellow]Bob der Baumeister[/COLOR]", "playlist/PLiK4BrMh3Fy8z0X2Q1nh9Ts5Uq_XVXoB1", "Bob.png"),
        ("[COLORyellow]Peppa Pig[/COLOR]", "playlist/PLIHhW2rjlyqazX9VsDH3OB_BvXu3y2arK", "Peppa.png"),
        ("[COLORyellow]Die Fixies[/COLOR]", "playlist/PLMu5a51zMv6zUI7ydYUdLkwHLyAq9mlw5", "Fixies.png"),
        ("[COLORyellow]Caillou[/COLOR]", "playlist/PLYbELRCXraUV5CxUx0VFqALe5B2NOnDM-", "Caillou.png"),
        ("[COLORyellow]Tom der Abschleppwagen[/COLOR]", "playlist/PLfrJ8rAzdNSWKpsTGcZGNLyjsVDiwyj90", "Tom.png"),
        ("[COLORyellow]Bali[/COLOR]", "playlist/PLALmJHHn-zwQIeiWIqC0LZV4c9-GXNvsd", "Bali.png"),
        ("[COLORyellow]Der kleine Nick[/COLOR]", "playlist/PLEeEPFBqG6FIlRKzCUGaxMHTtmG9BHT1r", "KleinNick.png"),
        ("[COLORyellow]Peter Pan[/COLOR] Spannende Abenteuer", "playlist/PLEsSrAkc-N6rXexCXeRYvk3m69rYU6LmT", "Peter.png"),
        ("[COLORyellow]Wendy[/COLOR] Pferde sind ihr Leben", "playlist/PLAqP3cngI26r65PV1PZbYoSc5sjMHmt2_", "Wendy.png"),
        ("[COLORyellow]Justice League[/COLOR] DC Kids", "playlist/PLWH6DXF9upwP53YyfSKaLD_XbMwwgphuB", "Justice.png"),
        ("[COLORyellow]Benjamin Blümchen[/COLOR] BenjaminBlümchen.tv", "playlist/PL1SAyTUFBb74hUX32r6aqasGENGL4YShb", "Ben.png"),
        ("[COLORyellow]Bibi Blocksberg[/COLOR] BibiBlocksberg.tv", "playlist/PLOZg6nrLYB7-EgluZK6CuMBzJtKhvFIAU", "Bibi.png"),
        ("[COLORyellow]Mister Bean[/COLOR]", "playlist/PLiDbV9ObbZLV_R9ofcSdJSPP4PSrobk3g", "Bean.png"),
        ("[COLORorange]Pink Panther[/COLOR] 1. Klassik Serie", "playlist/PL546904B9DC923B31", "Pink1.png"),
        ("[COLORlime]Pink Panther[/COLOR] 2. Die neue Serie", "playlist/PL2MVdpCy9PxFMwC6UaXwNOTZMPUxiU6KB", "Pink2.png"),
        ("[COLORorange]Tom & Jerry[/COLOR] 1. Klassik Serie", "playlist/PLUCHDQsTRtWb1AlJQV0_ojhg5hpLjpdC_", "Jerry1.png"),
        ("[COLORlime]Tom & Jerry[/COLOR] 2. Die neue Serie", "playlist/PL2MVdpCy9PxFf_BZJfjTtNuXTBdyu1ig9", "Jerry2.png"),
        ("[COLORorange]Wickie und die starken Männer[/COLOR] 1. Klassik Serie", "playlist/PLGP11O3gIZb-CAn5df2AE687pqGLxv2hr", "Wickie1.png"),
        ("[COLORlime]Wickie und die starken Männer[/COLOR] 2. Die neue Serie", "playlist/PLGP11O3gIZb8jsxU_InVjehKgJy1Z1Eyj", "Wickie2.png"),
        ("[COLORorange]Biene Maja[/COLOR] 1. Klassik Serie", "playlist/PLdHRcaRTf6chVA47IIGwDRJbvgkgBS6Xz", "Maja1.png"),
        ("[COLORlime]Biene Maja[/COLOR] 2. Die neue Serie", "playlist/PLdHRcaRTf6cie56jn0JUsHVGMMSU4AqY-", "Maja2.png"),
        ("[COLORorange]Heidi[/COLOR] 1. Klassik Serie", "playlist/-J_Clayv2_c&list=PLwz9HrBqSQF-WEycaVv_2m5o_4rmxICyn", "Heidi1.png"),
        ("[COLORlime]Heidi[/COLOR] 2. Die neue Serie", "playlist/PLwz9HrBqSQF9Y9W6hf-AwwBxTunNYrFvA", "Heidi2.png"),
        ("[COLORorange]Das Dschungelbuch[/COLOR] 1. Klassik Serie", "playlist/PLYekapbFEdMmzDN29jkQwATMx3BgznsdM", "Mogli1.png"),
        ("[COLORlime]Das Dschungelbuch[/COLOR] 2. Die neue Serie", "playlist/PL_YOcJJS3cSLJ6-4pXn9SURAkw8Z98FdV", "Mogli2.png"),
        ("[COLORorange]Robin Hood[/COLOR] 1. Klassik Serie", "playlist/PLYekapbFEdMlSWa8pmtr1EEQGI3lEofb3", "Robin1.png"),
        ("[COLORlime]Robin Hood[/COLOR] 2. Die neue Serie", "playlist/PLM5esjyCBU_qStUbQ_YqpE--k700AWoG5", "Robin2.png"),
        ("[COLORorange]Die Schlümpfe[/COLOR] 1. Klassik Serie", "playlist/PLe9POcs8knUCprw4_XXxTm8hkGBVw6NHs", "Schlumpf1.png"),
        ("[COLORorange]Simba der Löwenkönig[/COLOR] 1. Klassik Serie", "playlist/PLYekapbFEdMlAfVPEpc9EQxHP4nCIXd3T", "Simba.png"),
        ("[COLORorange]Christoph Columbus[/COLOR] 1. Klassik Serie", "playlist/PLYekapbFEdMnpBAXde80pONK86-k_TPFl", "Chris.png"),
        ("[COLORorange]Meister Eder & sein Pumuckl[/COLOR] 1. Klassik Serie", "playlist/PLpalD7hdQxE3nzQxRxxfmFk9D33EuPPtO", "Pumuckl.png"),
        ("[COLORorange]Calimero[/COLOR] 1. Klassik Serie", "channel/UCnjYE_WVG0PMRH6HSlWJr5Q", "Calimero1.png"),
        ("[COLORorange]Grisu der kleine Drache[/COLOR] 1. Klassik Serie", "playlist/PLOE3ysCGNx-1kamFgtU8gGwIvuPmI2FEi", "Grisu.png"),
        ("[COLORorange]Alfred J Kwak[/COLOR] 1. Klassik Serie", "playlist/PL58016D15BD79A97F", "Alfred.png"),
        ("[COLORorange]Scooby Doo[/COLOR] 1. Klassik Serie", "playlist/PLJYf0JdTApCqEYfW77tMTtqN-gA65_LPW", "Scooby.png"),
        ("[COLORorange]Kleo, das fliegende Einhorn[/COLOR] Staffel 1", "playlist/PLx7XyMBfhgopl8zhHyagkK5MZP-CzXZCl", "Kleo.png"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Klassiker': [
        ("[COLORorange]Flipper[/COLOR] Staffel 1", "playlist/PLHEDxAYF32QJmHISru7c-MZn_sYt9MpCL", "Flipper.png"),
        ("[COLORorange]Flipper[/COLOR] Staffel 2", "playlist/PLHEDxAYF32QIXWcvfBkxxzmfW6xI-i4Gl", "Flipper.png"),
        ("[COLORorange]Flipper[/COLOR] Staffel 3", "playlist/PLHEDxAYF32QJPtxGimOndyo8VunXLk62Q", "Flipper.png"),
        ("[COLORorange]Pan Tau[/COLOR] Staffel 1-3", "playlist/PLx7XyMBfhgoo-6tYzBcnVJv4BCZC41q_W", "https://yt3.googleusercontent.com/m9EMpzxqRblZQ9CuD6_b-KZEbXeGs_fYern_BKeANOTlQTZ-YynVvcUTKpoo3I0gVQ3X_0A1qK4=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORorange]Die rote Zora und ihre Bande[/COLOR] Alle Folgen", "playlist/PLx7XyMBfhgookKfFmo-hE7YfMCRA9YJIw", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORorange]Die Strandclique[/COLOR] Staffel 1", "playlist/PLx7XyMBfhgoq2FJuMdl7RNh1TJGzZN7Kj", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORorange]Gegen den Wind[/COLOR] Staffel 1", "playlist/PLx7XyMBfhgoqH3sckwgLRpmSI06VTEWUX", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORorange]Trickfilm-Klassiker[/COLOR] DEFA", "playlist/PLx7XyMBfhgoq5obBLDvi58-ljZfZb0qzp", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORorange]Spielfilmklassiker zu Weihnachten[/COLOR]", "playlist/PLx7XyMBfhgoqJHGE11Dr3oEhWMCDvRFLo", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORorange]Kinderfilm Klassiker[/COLOR]", "playlist/PLAroxwS0jZuTN6tscgrR_ubgHM4UaFBPv", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/kids_tube.png"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Filme': [
        ("[COLORyellow]Kinderfilme[/COLOR] von Netzkino", "playlist/PLfEblejE-l3k5xxDsBiKVhdNqWAuCIYRr", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Zeichentrickfilme[/COLOR] von Netzkino", "playlist/PLfEblejE-l3l8AwrdcuMp-p31uwBaJJXl", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Pferdefilme[/COLOR] von Netzkino", "playlist/PLfEblejE-l3k3qM4Q1GlnGdGeRjzlZvRn", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Hundefilme[/COLOR] von Netzkino", "playlist/PLfEblejE-l3nIBgJeAv7KO1DPvC2yN8-5", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Tennie Komödien[/COLOR] von Netzkino", "playlist/PLfEblejE-l3kyX48AXCaOnKFLxxkasxOM", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Familienkino[/COLOR] von Netzkino", "playlist/PLfEblejE-l3nta_dpVmIwGomgE_a3sm6g", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Weihnachtskino[/COLOR] von Netzkino", "playlist/PLfEblejE-l3n9NKla09pwoYVLtnrL2kv3", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORyellow]Kinderkino[/COLOR] von Netzkino", "channel/UCmZUsl5MLqXIhuSTVP6x-EA", "special://home/addons/plugin.video.lastship.reborn/resources/art/sites/netzkino.png"),
        ("[COLORorange]Kinderfilme[/COLOR] von Kixi", "playlist/PLAroxwS0jZuS521YByzaxA6ZO5VO-ppXJ", "Kixi.png"),
        ("[COLORorange]Zeichentrickfilme[/COLOR] von Kixi", "playlist/PLAroxwS0jZuQSy2pjwruhzz44-kQ0YHEh", "Kixi.png"),
        ("[COLORorange]Tierfilme[/COLOR] von Kixi", "playlist/PLAroxwS0jZuQQlgJJ3_-imn1abL4A4Zlc", "Kixi.png"),
        ("[COLORorange]Hundefilme[/COLOR] von Kixi", "playlist/PLAroxwS0jZuQC6yoU8LJF3USzgQBlrzx5", "Kixi.png"),
        ("[COLORorange]Familienfilme[/COLOR] von Kixi", "playlist/PLAroxwS0jZuQUBhbxcAUlfh9qeJGV_tom", "Kixi.png"),
        ("[COLORorange]Weihnachtsfilmefilme[/COLOR] von Kixi", "playlist/PLAroxwS0jZuTLDgN-YeW2Yy0trylROSs4", "Kixi.png"),
        ("[COLORorange]Kinderfilme Klassiker[/COLOR] von Kixi", "playlist/PLAroxwS0jZuQUke_UTBPvbyCB27G0NtwA", "Kixi.png"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Geschichten': [
        ("[COLORyellow]Unser Sandmännchen[/COLOR] von RBB", "user/sandmannshop", "Sand.png"),
        ("[COLORyellow]German Fairy Tales[/COLOR]", "playlist/PLYJXC9hVK9ZdUXMrhOTC-kpfIEwJQ2c0u", "Fairy.png"),
        ("[COLORyellow]Märchen für Kinder[/COLOR] Gutenachtgeschichten", "playlist/PLRSUQa10y6VFV1kYPPc1hH0kSksmCvGU1", "Maerchen.png"),
        ("[COLORyellow]Gute Nacht Geschichten[/COLOR] DE.BedtimeStory.TV", "playlist/PLSeYZc0WTfTc-eqLP1bZLj0fJ13ZVfzBv", "Bed.png"),
        ("[COLORyellow]Deine Märchenwelt[/COLOR] Märchen, Geschichten, Sagen", "playlist/PLvsVeezf83quto2DL-5J4ZPmm2cYgwaFU", "Maerchen.png"),
        ("[COLORyellow]Geschichten für Kinder[/COLOR]", "playlist/PLT8zuqWPJkYAJI2jiNa67Q3YaRMOVR-uL", "Kids.png"),
        ("[COLORyellow]SimsalaGrimm[/COLOR]", "playlist/PLN5h7nQDQsiNAygibR61TxqtquFrvydt6", "Grimm.png"),
        ("[COLORyellow]Grimms Märchen[/COLOR] Filme", "playlist/PL9A89EE24241DACF2", "Grimm2.png"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Buch': [
        ("[COLORyellow]Kinder- & Jugend Hörspiele[/COLOR] HoerTalk", "playlist/PL6IcxBEYItDV7PWjFYdnHF9IsvAAGPaRx", "Talk.png"),
        ("[COLORyellow]Jugend Hörspiele[/COLOR] Spooks", "playlist/PLBCqvaIr4yUkjmEq5okDt5UAcNhqPgbq6", "Spooks.png"),
        ("[COLORyellow]PUMUCKL Hörspiele 1960-1975[/COLOR] Hörspiel Fabrik", "playlist/PLv_ENFPXiu3hRZIrlhauZbojCmT_N6mJf", "Pumuckl.png"),
        ("[COLORyellow]TIM & STRUPPI Hörspiele[/COLOR] Hörspiel Fabrik", "playlist/PLv_ENFPXiu3h0BNMfk7NvPyEkZVpZgE6P", "Tim.png"),
        ("[COLORyellow]BENJAMIN BLÜMCHEN Hörspiele[/COLOR] BenjaminBlümchen.tv", "playlist/PL1SAyTUFBb762GpJFH19_NvETovF_-NXu", "Ben.png"),
        ("[COLORyellow]BIBI BLOCKSBERG[/COLOR] BibiBlocksberg.tv", "playlist/PLOZg6nrLYB79IpjmXsBPoq2tuW1DjEb1J", "Bibi.png"),
        ("[COLORyellow]BARBIE Hörspiele[/COLOR] ", "playlist/PLTIFt51Pse_rIf7mf0uLdqXzgdbkwJ2kf", "Barbie.png"),
        ("[COLORyellow]KASPERLE Hörspiele[/COLOR] Eulenspiegel", "playlist/PLWf5n0LLW8SH2w3gSefz2uQyEQiWWMues",  "Kasper.png"),
        ("[COLORyellow]GRIMMS Märchen Hörspiele[/COLOR] Märchenwelt", "playlist/PL_7pajp36h-R_VBtOQMaFg7SAmlT02fX8", "Grimm2.png"),
        ("[COLORyellow]Märchen Hörspiele[/COLOR] Hörspiel Fuchs", "playlist/PL49N08rhGF4dp7S5egoLmLT50_MqtTtVD", "Maerchen.png"),
        ("[COLORyellow]Märchen Hörspiele[/COLOR] Hörspiel Cafe", "playlist/PLSw94V8UrQVpzaPo-ajaueBLKUM2QxdnH", "Maerchen.png"),
        ("[COLORyellow]Klassische Hörspiele[/COLOR] Märchenwelt", "playlist/PL_7pajp36h-QXzz1ncxNJFtg2GZzHV1dL", "Klassik.png"),
        ("[COLORyellow]Christliche Hörspiele[/COLOR] die Bibel", "channel/UCJSF-0y7Pz7VUNH3cCdqwLw", "Bibel.png"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Wissen': [
        ("[COLORyellow]PIXI[/COLOR] Wissen TV", "playlist/PLHKaBnKI1TKo__fOVrZIDHibsTqsuKjDL", "Pixi.png"),
        ("[COLORyellow]KiWi[/COLOR] Schlaue Fragen, schlaue Antworten!", "playlist/PLVWZ8fAnW6IbmOFpTtp6ImFFW-K4T83YN", "Schlau.png"),
        ("[COLORyellow]KiWi[/COLOR] Professor Schlaufuchs", "playlist/PLVWZ8fAnW6IbqKL4j7uaR4RtPsqB6rKc0", "Fuchs.png"),
        ("[COLORyellow]Planet Schule[/COLOR] von ARD", "playlist/PL93F091E59FDFDDBF", "Schule.png"),
        ("[COLORyellow]Checker Welt[/COLOR] Experimente", "playlist/PLXHkZNhCrU2ZGzKXPeq_8NY8ZF3coQyR9", "Checker.png"),
        ("[COLORyellow]DIY Inspiration Kids Club[/COLOR] Experimente", "playlist/PLjXEwjXTkbzqewdd_3DTgb0GZ_0LhECPJ", "DIY.png"),
        ("[COLORyellow]PAXI[/COLOR] European Space Agency", "playlist/PLbyvawxScNbvwcIVrGQV4p6g6cp9pH0To", "Paxi.png"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],

    'Kinder Musik': [
        ("[COLORyellow]Sing mit Mir[/COLOR] Kinderlieder", "playlist/PLu791Jb5lWoCOzceiS6SDeGW_u1s7x-0h", "Sing.png"),
        ("[COLORyellow]Hurra[/COLOR] Kinderlieder", "playlist/PLz8hTTrU37YTw06tseX2sHpXMbDK9x_Ds", "Hurra.png"),
        ("[COLORyellow]Kinderlieder[/COLOR] zum Mitsingen und Tanzen", "playlist/PLM9BsUcYb5Mn8xN72IX5LUHj25_ssTN5_", "Beste.png"),
        ("[COLORyellow]Karaoke[/COLOR] Kinderlieder mit Bien Maja, Wickie und Co.", "playlist/PLCywMP0BLGOk_cTbmLNENN711N3Yw0hRF", "Karaoke.png"),
        ("[COLORyellow]Disney[/COLOR] Titelmusik", "playlist/PL4BrNFx1j7E6a6IKg8N0IgnkoamHlCHWa", "DisneyM.png"),
        ("[COLORyellow]KinderliederTV.de[/COLOR]", "playlist/PLmMaywx47bx5w5YJ3uLJz73X81srE4wlQ", "KTV.png"),
        ("[COLORyellow]GiraffenaffenTV[/COLOR]", "channel/UCUWTq9Jq97CNE9j28OarHbQ", "https://yt3.googleusercontent.com/5f81fzOw1sMs0u9zlz8hUqXWrDJ5XWbdsTM3z2VMgoAsPX_cENGCip8_YI8Yx9xsp7BfDjmZyQ=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORyellow]Kika TanzAlarm[/COLOR] | Mehr auf KiKA.de", "playlist/PLIFhkWbVDf6wcorvcRTbQvSYvYemSvJoa", "https://yt3.googleusercontent.com/eVEM7kLayi8-pFKQ2jMVMqWMMf-Sj-LFtPD5oD5d4vctMxwa_MxvYkYQOihpO8YxHO3Fo8qHVA=s160-c-k-c0x00ffffff-no-rj"),
        ("[COLORyellow]Weitere[/COLOR]", "Weitere", ""),
        ("[COLORyellow]Suche[/COLOR]", "Suche", ""),
    ],
}


def search_playlists(query, max_results=5):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    my_keys = ['AIzaSyBQ68nE4JxFSlyogirJUo8b4TYF2iGMJms', 'AIzaSyAyvS7LLZsBF6mNWiAmISYvdJWtu_MSvf4']
    key = random.choice(my_keys)
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'playlist',
        'maxResults': max_results,
        'key': key}

    response = requests.get(search_url, params=params)

    if response.status_code == 200:
        data = response.json()
        playlists = data.get('items', [])
        sublists = []

        if not playlists:
            xbmcgui.Dialog().notification('Kids_Tube', 'Not found')
        else:
            for i, item in enumerate(playlists, start=1):
                playlist_title = item['snippet']['title']
                playlist_id = item['id']['playlistId']
                playlist_icon = item['snippet']['thumbnails']['default']['url']
                sublists.append({'title': playlist_title, 'id': 'playlist/'+playlist_id, 'icon': playlist_icon})
        return sublists
    else:
        xbmcgui.Dialog().notification('Kids_Tube', 'Not found')


def sub_list(action):
    youtube_fix.YT()
    params = ParameterHandler()
    action1 = '#' + str(action) + ' deutsch für kinder'
    action2 = '*' + str(action)
    apikey = Addon('plugin.video.youtube').getSetting('youtube.api.key')
    for List in sublists[str(action)]:
        name = List[0]
        id = List[1]
        icon = List[2]
        if apikey == '' or apikey == None:
            sUrl="plugin://plugin.video.youtube/" + id + "/?addon_id=plugin.video.lastship.reborn"
        else:
            sUrl="plugin://plugin.video.youtube/" + id + "/"
        if 'Weitere' in id:
            addDirectoryItem(name, 'runPlugin&site=%s&function=load&action1=%s' % (SITE_NAME, action1), SITE_ICON, 'DefaultMovies.png')
        elif 'Suche' in id:
            addDirectoryItem(name, 'runPlugin&site=%s&function=load&action1=%s' % (SITE_NAME, action2), SITE_ICON, 'DefaultMovies.png')

        else:
            addDirectoryItem(name, sUrl, SITE_ICON, 'DefaultMovies.png',isAction=False)


    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def sub_listw(action):

    youtube_fix.YT()
    apikey = Addon('plugin.video.youtube').getSetting('youtube.api.key')

    sublist2 = search_playlists(action, max_results=50)
    for List in sublist2:
        name = "[COLORyellow]%s[/COLOR]" % List['title']
        id = List['id']
        icon = List['icon']
        if apikey == '' or apikey == None:
            sUrl="plugin://plugin.video.youtube/" + id + "/?addon_id=plugin.video.lastship.reborn"
        else:
            sUrl="plugin://plugin.video.youtube/" + id + "/"

        
        params.setParam('trumb', icon)
        params.setParam('sUrl', sUrl)
        addDirectoryItem(name, sUrl, SITE_ICON, 'DefaultMovies.png',isAction=False)

        #cGui().addFolder(cGuiElement(name,SITE_IDENTIFIER,''),params,bIsFolder=True)
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def search(action1):
    youtube_fix.YT()
    apikey = Addon('plugin.video.youtube').getSetting('youtube.api.key')

    while True:
        heading = 'Was soll gesucht werden'
        keyboard = xbmc.Keyboard('default', 'heading', True)
        keyboard.setDefault()
        keyboard.setHeading(heading)
        keyboard.setHiddenInput(False)
        keyboard.doModal()
        if keyboard.isConfirmed() and not keyboard.getText() == '':
            break
    query = keyboard.getText()
    sublist2 = search_playlists(query + ' ' + action1 + ' deutsch', max_results=50)
    for List in sublist2:
        name = "[COLORyellow]%s[/COLOR]" % List['title']
        id = List['id']
        icon = List['icon']
        if apikey == '' or apikey == None:
            sUrl="plugin://plugin.video.youtube/" + id + "/?addon_id=plugin.video.lastship.reborn"
        else:
            sUrl="plugin://plugin.video.youtube/" + id + "/"
        
        params.setParam('trumb', icon)
        params.setParam('sUrl', sUrl)
        addDirectoryItem(name, sUrl, SITE_ICON, 'DefaultMovies.png',isAction=False)

        #cGui().addFolder(cGuiElement(name,SITE_IDENTIFIER,''),params,bIsFolder=True)
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def main_list():
    params = ParameterHandler()
    for name, id, icon in channellist:
        addDirectoryItem(name, 'runPlugin&site=%s&function=load&action1=%s&trumb=%s' % (SITE_NAME,id,icon), SITE_ICON, 'DefaultMovies.png')

    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)