# -*- coding: utf-8 -*-
# Copyright 2022 sorax
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import xbmcaddon
import xbmcgui
import xbmcplugin

import json
import sys

from bs4 import BeautifulSoup

from libs.network import fetchHtml
from libs.network import fetchJson


# -- Addon --
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
addon_name = addon.getAddonInfo("name")
addon_icon = addon.getAddonInfo("icon")

base_path = sys.argv[0]


# -- Settings --
dgs = addon.getSettingInt("dgs2")
interval = addon.getSettingInt("interval2")
quality = addon.getSettingInt("quality2")
update = addon.getSettingInt("update2")
source = addon.getSettingInt("source2")


def sandmann():
    li_refresh = xbmcgui.ListItem(label=addon.getLocalizedString(30020))
    xbmcplugin.addDirectoryItem(addon_handle, base_path, li_refresh, True)

    html = fetchWebsite()

    if dgs == 0:
        episodes = getEpisodes(html, 1)
    elif dgs == 2:
        episodes = getEpisodes(html, 2)
    else:
        episodes = getEpisodes(html, 1) + getEpisodes(html, 2)

    item_list = []
    for episode, description in episodes:
        path = getEpisodePath(episode)
        details = fetchEpisodeDetails(path)

        item_list.append((details["stream"], getListItem(details, description), False))

    # xbmcgui.Dialog().ok("DEBUG", f'{item_list[0]}')
    xbmcplugin.addDirectoryItems(addon_handle, item_list, len(item_list))
    xbmcplugin.endOfDirectory(addon_handle)


def fetchWebsite():
    url = "https://www.sandmann.de/videos/"
    html = fetchHtml(url)

    return html


def getEpisodes(html, count):
    soup = BeautifulSoup(html, "html.parser")
    episodes = soup.select(f"#main > .count{count} .manualteaserpicture")
    html_descriptions = soup.select(f"#main > .count{count} .manualteasershorttext p")
    descriptions = [p.get_text() for p in html_descriptions]

    return list(zip(episodes, descriptions))


def getEpisodePath(episode):
    jsb_string = episode.get("data-jsb")
    jsb_object = json.loads(jsb_string)

    return jsb_object["media"]


def fetchEpisodeDetails(path):
    json = fetchJson(f"https://www.sandmann.de{path}")

    streams = {}
    for stream in json["_mediaArray"][0]["_mediaStreamArray"]:
        streams[stream["_quality"]] = stream["_stream"]

    title = json["rbbtitle"].split(" | ")
    previewImage = "https://www.sandmann.de" + json["_previewImage"].rsplit("/", 1)[0]

    return {
        "date": title[2],
        # "dgs": json["dgs"],
        "duration": json["_duration"],
        "fanart": previewImage + "/size=1920x1080.jpg",
        "stream": streams["auto"],
        "thumb": previewImage + "/size=640x360.jpg",
        "title": f"{title[2]} | {title[0]}"
    }


def getListItem(item, description):
    li = xbmcgui.ListItem()
    li.setLabel(item["title"])
    li.setArt({
        "fanart": item["fanart"],
        "thumb": item["thumb"]
    })
    li.setInfo(
        type="video",
        infoLabels={
            "aired": item["date"],
            "duration": item["duration"],
            "plot": description,
        }
    )
    li.setProperty("IsPlayable", "true")

    return li
