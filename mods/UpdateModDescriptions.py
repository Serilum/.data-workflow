# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
from urllib.parse 					import unquote
import requests
import json
import time
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Constants

sep = os.path.sep

skipMods = ["OP Permission Fallback"]

aboutPlateUrl = 'cdn.serilum.com/description/nameplate/about-the-mod.svg'
footerPlateUrl = 'cdn.serilum.com/description/nameplate/notes-n-links.svg'

def main(mainPath):
	fprefix = " [Update Mod Descriptions] "

	print("\n" + fprefix + "Starting the description generation.")

	dataPath = "." + sep + "mods" + sep + "data"
	apiDataPath = "." + sep + "api" + sep + "data"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		dataPath = mainPath + sep + "mods" + sep + "data"
		apiDataPath = mainPath + sep + "api" + sep + "data"

	descriptionsPath = dataPath + sep + "descriptions"

	try:
		with open(apiDataPath + sep + "curseforge.json", 'r') as f:
			curseForgeMods = json.load(f)
	except Exception:
		print(fprefix + "Could not read CurseForge data. Skipping.")
		return

	headers = {
		"x-api-key": os.environ["CURSEFORGE_API_KEY"],
		"Accept": "application/json"
	}

	mainByName = {}
	for mod in curseForgeMods:
		slug = mod.get("slug", "")
		if slug.endswith("-fabric") or slug.endswith("-fabric-version"):
			continue

		modName = mod.get("name", "")
		if modName == "" or modName in skipMods:
			continue

		mainByName[modName] = mod

	print(fprefix + "Processing " + str(len(mainByName)) + " descriptions.")

	for modName in naturalSort(list(mainByName.keys())):
		mod = mainByName[modName]
		slug = mod.get("slug", "")
		modId = mod.get("id", 0)
		projectType = Constants.projectTypes.get(mod.get("classId", 0), "other")

		try:
			response = requests.get(
				"https://api.curseforge.com/v1/mods/" + str(modId) + "/description",
				headers = headers,
				timeout = 15
			)
			description = response.json().get("data", "") or ""
		except Exception as e:
			print(fprefix + "Error fetching description for " + slug + ": " + str(e))
			continue

		typePath = descriptionsPath + sep + projectType
		Path(typePath).mkdir(parents=True, exist_ok=True)
		with open(typePath + sep + slug + ".txt", 'w', encoding='utf-8') as f:
			f.write(normalizeEditor(rewriteLinkouts(extractDescription(description))))

		print(fprefix + "Processed: " + modName)

		time.sleep(0.05)

	print(fprefix + "Done!")

def extractDescription(html):
	plateStart = html.find(aboutPlateUrl)
	footerStart = html.find(footerPlateUrl, plateStart + 1)
	if plateStart == -1 or footerStart == -1:
		return stripDescription(html)

	contentStart = html.find("</p>", plateStart)
	if contentStart == -1:
		return stripDescription(html)
	contentStart += len("</p>")

	contentEnd = html.rfind("<p", contentStart, footerStart)
	if contentEnd == -1:
		contentEnd = footerStart

	return html[contentStart:contentEnd].strip()

def stripDescription(html):
	m = re.search(r'badges/svg/youtube\.svg.*?</p>', html, flags=re.DOTALL)
	if m:
		html = html[m.end():]

	html = re.split(r'(?:<p[^>]*>)?(?:\s|<br\s*/?>|&nbsp;)*-{8,}<br', html, maxsplit=1)[0]

	html = re.sub(r'<strong><span style="font-size:24px">Requires the library mod.*?</a>\.?(?:\s|<br\s*/?>|&nbsp;)*(?:</span>)?(?:\s|<br\s*/?>)*</strong>', '', html, count=1, flags=re.DOTALL)
	html = re.sub(r'<strong>(?:(?!</strong>).)*?This mod is part of(?:(?!</strong>).)*?</strong>', '', html, count=1, flags=re.DOTALL)

	html = re.sub(r'^\s*<p>(?:\s|<br\s*/?>|&nbsp;|<strong>\s*</strong>)*', '<p>', html, count=1)
	html = re.sub(r'^(?:\s*<p[^>]*>(?:\s|&nbsp;|<br\s*/?>)*</p>)+', '', html)
	html = re.sub(r'(?:<p[^>]*>(?:\s|&nbsp;|<br\s*/?>)*</p>\s*)+$', '', html)

	html = html.strip()

	if html.rfind('<p') > html.rfind('</p>'):
		html += '</p>'

	return html

def normalizeEditor(html):
	html = re.sub(r'>[\r\n]+<', '><', html)
	return html.replace("&#x27;", "'").replace("&#39;", "'")

def rewriteLinkouts(html):
	def decode(match):
		url = match.group(1)
		while True:
			decoded = unquote(url)
			if decoded == url:
				return url
			url = decoded

	return re.sub(r'/linkout\?remoteUrl=([^"&]+)', decode, html)

def naturalSort(items):
	def naturalKey(value):
		return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', value.lower())]

	return sorted(items, key=naturalKey)

if __name__ == "__main__":
	main("")
