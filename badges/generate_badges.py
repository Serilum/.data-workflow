# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
from decimal 						import *
import cloudscraper
import requests
import json
import patreon
import os
import sys

sep = os.path.sep

def main(mainpath):
	fprefix = " [Generate Badges] "

	print("\n" + fprefix + "Starting the generation.")

	rootpath = "." + sep + "badges"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		rootpath = mainpath + sep + "badges"

	Path(rootpath + sep + "svg").mkdir(parents=True, exist_ok=True)


	print("\n" + fprefix + "Starting the SVG file creation for CurseForge.")

	curseforgeDownloadCount = getCurseForgeDownloadCount()
	formattedCurseForgeDownloadCount = formatToReadableNumber(curseforgeDownloadCount)

	if curseforgeDownloadCount > 0:
		with open(rootpath + sep + "templates" + sep + "curseforge.svg", 'r') as curseForgeSvgTemplateFile:
			curseForgeSvgTemplate = curseForgeSvgTemplateFile.read()

		with open(rootpath + sep + "svg" + sep + "curseforge.svg", 'w') as curseForgeSvgFile:
			curseForgeSvgFile.write(curseForgeSvgTemplate.replace("%N", formattedCurseForgeDownloadCount.upper()))

		print(fprefix + "Created the CurseForge SVG file with " + formattedCurseForgeDownloadCount + " downloads.")
	else:
		print(fprefix + "The CurseForge count returned < 0. Ignoring.")



	print("\n" + fprefix + "Starting the SVG file creation for Modrinth.")

	modrinthDownloadCount = getModrinthDownloadCount()
	formattedModrinthDownloadCount = formatToReadableNumber(modrinthDownloadCount)

	if modrinthDownloadCount > 0:
		with open(rootpath + sep + "templates" + sep + "modrinth.svg", 'r') as modrinthSvgTemplateFile:
			modrinthSvgTemplate = modrinthSvgTemplateFile.read()

		with open(rootpath + sep + "svg" + sep + "modrinth.svg", 'w') as modrinthSvgFile:
			modrinthSvgFile.write(modrinthSvgTemplate.replace("%N", formattedModrinthDownloadCount.upper()))

		print(fprefix + "Created the Modrinth SVG file with " + formattedModrinthDownloadCount + " downloads.")
	else:
		print(fprefix + "The Modrinth count returned < 0. Ignoring.")



	print("\n" + fprefix + "Starting the SVG file creation for Patreon.")

	patreonMemberCount = getAllPatreonMemberCount()
	formattedPatreonCount = formatToReadableNumber(patreonMemberCount)

	if patreonMemberCount > 0:
		with open(rootpath + sep + "templates" + sep + "patreon.svg", 'r') as patreonSvgTemplateFile:
			patreonSvgTemplate = patreonSvgTemplateFile.read()

		with open(rootpath + sep + "svg" + sep + "patreon.svg", 'w') as patreonSvgFile:
			patreonSvgFile.write(patreonSvgTemplate.replace("%N", formattedPatreonCount.upper()))

		print(fprefix + "Created the Patreon SVG file with " + formattedPatreonCount + " members.")
	else:
		print(fprefix + "The Patreon count returned < 0. Ignoring.")



	print("\n" + fprefix + "Starting the SVG file creation for YouTube.")

	youtubeSubscriberCount = getYoutubeSubscriberCount()
	formattedYoutubeSubCount = formatToReadableNumber(youtubeSubscriberCount)

	if youtubeSubscriberCount > 0:
		with open(rootpath + sep + "templates" + sep + "youtube.svg", 'r') as youtubeSvgTemplateFile:
			youtubeSvgTemplate = youtubeSvgTemplateFile.read()

		with open(rootpath + sep + "svg" + sep + "youtube.svg", 'w') as youtubeSvgFile:
			youtubeSvgFile.write(youtubeSvgTemplate.replace("%N", formattedYoutubeSubCount.upper()))

		print(fprefix + "Created the YouTube SVG file with " + formattedYoutubeSubCount + " subscribers.")
	else:
		print(fprefix + "The Youtube count returned < 0. Ignoring.")

	print("\n" + fprefix + "Done with generating the SVG badges!")
	return

def getYoutubeSubscriberCount():
	serilumChannelId = "UC6HHPQhGfduAV8yMMGtktSA"
	ytKey = os.environ["RICK_YT_API_KEY"]

	ytRequest = requests.get("https://www.googleapis.com/youtube/v3/channels?part=statistics&id=" + serilumChannelId + "&key=" + ytKey)

	ytJson = ytRequest.json()
	if "items" in ytJson:
		for item in ytJson["items"]:
			if "statistics" in item:
				stats = item["statistics"]
				if "subscriberCount" in stats:
					subCount = stats["subscriberCount"]
					return int(subCount)

	return -1

def getPatreonCount(members_json_file_path):
	with open(members_json_file_path, 'r') as json_file:
		members_json = json.load(json_file)

	if "patreon" in members_json:
		patreons = members_json["patreon"]
		return len(patreons)

	return -1

def getAllPatreonMemberCount():
	scraper = cloudscraper.create_scraper()
	rawPatreonRequest = scraper.get("https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.vercel.app%2Fapi%3Fusername%3Dserilum%26type%3Dpatrons&style=flat") # requests.get("https://patreon.com/serilum")
	rawPatreonPageData = rawPatreonRequest.text

	for pSpl in rawPatreonPageData.split(">"):
		inside = pSpl.split("<")[0]

		if "patrons" in inside:
			patreonCount = inside.split(" ")[0]
			if patreonCount.isnumeric():
				return int(patreonCount)			

	print("\n\nPatreon returns -1. Raw page data:\n\n")
	print(rawPatreonPageData)
	print("\n\n\n")
	return -1

def oldGetAllPatreonMemberCount():
	scraper = cloudscraper.create_scraper()
	rawPatreonRequest = scraper.get("https://patreon.com/serilum") # requests.get("https://patreon.com/serilum")
	rawPatreonPageData = rawPatreonRequest.text

	for rawSpan in rawPatreonPageData.split("<span "):
		span = ("<span " + rawSpan).split("</span>")[0] + "</span>"

		if "patron-count" in span:
			patreonCount = span.split(">")[1].split("<")[0].strip()
			if patreonCount.isnumeric():
				return int(patreonCount)

	print("\n\nPatreon returns -1. Raw page data:\n\n")
	print(rawPatreonPageData)
	print("\n\n\n")
	return -1

def getCurseForgeDownloadCount():
	modsChecked = []
	downloadCount = 0

	index = 0
	hasNextPage = True
	while hasNextPage:
		index += 50

		cfResponse = requests.get("https://api.curseforge.com/v1/mods/search?gameId=432&primaryAuthorId=7049004&index=" + str(index), headers = { "x-api-key" : os.environ["CF_API_KEY"], "Accept" : "application/json" })
		cfJson = cfResponse.json()

		if "data" in cfJson:
			for entry in cfJson["data"]:
				if "name" in entry:
					modName = entry["name"]

					if modName in modsChecked:
						continue

					modsChecked.append(modName)

				if "downloadCount" in entry:
					downloadCount += entry["downloadCount"]
		else:
			hasNextPage = False

		if "pagination" in cfJson:
			if cfJson["pagination"]["resultCount"] < 50:
				hasNextPage = False
		else:
			hasNextPage = False

	if downloadCount == 0:
		return -1

	return downloadCount

def getModrinthDownloadCount():
	mrResponse = requests.get('https://api.modrinth.com/v2/search?facets=[["author:Serilum"]]&limit=500', headers = { "Authorization" : os.environ['MR_API_KEY'] })
	mrJson = mrResponse.json()

	if "hits" in mrJson:
		totalDownloads = 0
		for hit in mrJson["hits"]:
			if "downloads" in hit:
				totalDownloads += hit["downloads"]

		return totalDownloads

	return -1

def formatToReadableNumber(num):
	getcontext().prec = 1
	getcontext().rounding = ROUND_DOWN

	_num = Decimal(num)
	num = float(f'{_num:.3g}')
	magnitude = 0
	while abs(num) >= 1000:
		magnitude += 1
		num /= 1000.0

	num = int(num * 10) / 10
	return f"{f'{num:f}'.rstrip('0').rstrip('.')}{['', 'k', 'M', 'B', 'T'][magnitude]}"

if __name__ == "__main__":
	main("")