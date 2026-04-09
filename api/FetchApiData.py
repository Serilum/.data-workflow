# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
import cloudscraper
import requests
import json
import time
import os
import sys

sep = os.path.sep

def main(mainPath):
	fprefix = " [Fetch API Data] "

	print("\n" + fprefix + "Starting API data fetching.")

	rootPath = "." + sep + "api"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		rootPath = mainPath + sep + "api"

	dataPath = rootPath + sep + "data"
	Path(dataPath).mkdir(parents=True, exist_ok=True)

	fetchCurseForge(fprefix, dataPath)
	fetchModrinth(fprefix, dataPath)
	fetchPatreon(fprefix, dataPath)
	fetchYoutube(fprefix, dataPath)

	print(fprefix + "Done fetching all API data!")

def fetchCurseForge(fprefix, dataPath):
	print(fprefix + "Fetching CurseForge data.")

	mods = []
	modsChecked = []

	index = 0
	hasNextPage = True

	try:
		while hasNextPage:
			cfResponse = requests.get(
				"https://api.curseforge.com/v1/mods/search?gameId=432&primaryAuthorId=7049004&index=" + str(index),
				headers = {
					"x-api-key": os.environ["CURSEFORGE_API_KEY"],
					"Accept": "application/json"
				},
				timeout=15
			)
			cfJson = cfResponse.json()

			if "data" not in cfJson:
				break

			for entry in cfJson["data"]:
				modName = entry.get("name", "")

				if modName in modsChecked:
					continue
				modsChecked.append(modName)

				mods.append({
					"id": entry.get("id", 0),
					"name": modName,
					"slug": entry.get("slug", ""),
					"downloadCount": entry.get("downloadCount", 0),
					"latestFilesIndexes": entry.get("latestFilesIndexes", []),
				})

			if "pagination" in cfJson:
				if cfJson["pagination"]["resultCount"] < 50:
					hasNextPage = False
			else:
				hasNextPage = False

			index += 50
			time.sleep(0.1)

	except Exception as e:
		print(fprefix + "Error fetching CurseForge data: " + str(e))
		return

	with open(dataPath + sep + "curseforge.json", 'w') as f:
		json.dump(mods, f, indent=2)

	with open(dataPath + sep + "curseforge.min.json", 'w') as f:
		json.dump(mods, f)

	print(fprefix + "Saved CurseForge data for " + str(len(mods)) + " mods.")

def fetchModrinth(fprefix, dataPath):
	print(fprefix + "Fetching Modrinth data.")

	try:
		hits = []
		offset = 0
		limit = 100

		while True:
			mrResponse = requests.get(
				'https://api.modrinth.com/v2/search?facets=[["author:Serilum"]]&limit=' + str(limit) + '&offset=' + str(offset),
				headers = { "Authorization": os.environ["MODRINTH_API_KEY"] },
				timeout=15
			)
			mrJson = mrResponse.json()

			pageHits = mrJson.get("hits", [])
			hits.extend(pageHits)

			if len(pageHits) < limit:
				break

			offset += limit
			time.sleep(0.1)

		with open(dataPath + sep + "modrinth.json", 'w') as f:
			json.dump(hits, f, indent=2)

		with open(dataPath + sep + "modrinth.min.json", 'w') as f:
			json.dump(hits, f)

		print(fprefix + "Saved Modrinth data for " + str(len(hits)) + " mods.")

	except Exception as e:
		print(fprefix + "Error fetching Modrinth data: " + str(e))

def fetchPatreon(fprefix, dataPath):
	print(fprefix + "Fetching Patreon data.")

	try:
		scraper = cloudscraper.create_scraper()
		rawPatreonRequest = scraper.get("https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.vercel.app%2Fapi%3Fusername%3Dserilum%26type%3Dpatrons&style=flat")
		rawPatreonPageData = rawPatreonRequest.text

		memberCount = -1
		for pSpl in rawPatreonPageData.split(">"):
			inside = pSpl.split("<")[0]

			if "patrons" in inside:
				patreonCount = inside.split(" ")[0]
				if patreonCount.isnumeric():
					memberCount = int(patreonCount)
					break

		if memberCount == -1:
			print(fprefix + "Patreon returned -1. Raw data:")
			print(rawPatreonPageData)

		with open(dataPath + sep + "patreon.json", 'w') as f:
			json.dump({"memberCount": memberCount}, f, indent=2)

		with open(dataPath + sep + "patreon.min.json", 'w') as f:
			json.dump({"memberCount": memberCount}, f)

		print(fprefix + "Saved Patreon data: " + str(memberCount) + " members.")

	except Exception as e:
		print(fprefix + "Error fetching Patreon data: " + str(e))

def fetchYoutube(fprefix, dataPath):
	print(fprefix + "Fetching YouTube data.")

	try:
		serilumChannelId = "UC6HHPQhGfduAV8yMMGtktSA"
		ytKey = os.environ["RICK_YT_API_KEY"]

		ytRequest = requests.get(
			"https://www.googleapis.com/youtube/v3/channels?part=statistics&id=" + serilumChannelId + "&key=" + ytKey,
			timeout=15
		)
		ytJson = ytRequest.json()

		subscriberCount = -1
		if "items" in ytJson:
			for item in ytJson["items"]:
				if "statistics" in item:
					stats = item["statistics"]
					if "subscriberCount" in stats:
						subscriberCount = int(stats["subscriberCount"])

		with open(dataPath + sep + "youtube.json", 'w') as f:
			json.dump({"subscriberCount": subscriberCount}, f, indent=2)

		with open(dataPath + sep + "youtube.min.json", 'w') as f:
			json.dump({"subscriberCount": subscriberCount}, f)

		print(fprefix + "Saved YouTube data: " + str(subscriberCount) + " subscribers.")

	except Exception as e:
		print(fprefix + "Error fetching YouTube data: " + str(e))

if __name__ == "__main__":
	main("")
