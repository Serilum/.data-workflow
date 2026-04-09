# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
from decimal 						import Decimal, getcontext, ROUND_DOWN
import json
import os
import sys

sep = os.path.sep

def main(mainPath):
	fprefix = " [Generate Badges] "

	print("\n" + fprefix + "Starting the generation.")

	rootPath = "." + sep + "badges"
	apiDataPath = "." + sep + "api" + sep + "data"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		rootPath = mainPath + sep + "badges"
		apiDataPath = mainPath + sep + "api" + sep + "data"

	Path(rootPath + sep + "svg").mkdir(parents=True, exist_ok=True)


	print("\n" + fprefix + "Starting the SVG file creation for CurseForge.")

	curseforgeDownloadCount = getCurseForgeDownloadCount(apiDataPath)
	formattedCurseForgeDownloadCount = formatToReadableNumber(curseforgeDownloadCount)

	if curseforgeDownloadCount > 0:
		with open(rootPath + sep + "templates" + sep + "curseforge.svg", 'r') as curseForgeSvgTemplateFile:
			curseForgeSvgTemplate = curseForgeSvgTemplateFile.read()

		with open(rootPath + sep + "svg" + sep + "curseforge.svg", 'w') as curseForgeSvgFile:
			curseForgeSvgFile.write(curseForgeSvgTemplate.replace("%N", formattedCurseForgeDownloadCount.upper()))

		print(fprefix + "Created the CurseForge SVG file with " + formattedCurseForgeDownloadCount + " downloads.")
	else:
		print(fprefix + "The CurseForge count returned < 0. Ignoring.")



	print("\n" + fprefix + "Starting the SVG file creation for Modrinth.")

	modrinthDownloadCount = getModrinthDownloadCount(apiDataPath)
	formattedModrinthDownloadCount = formatToReadableNumber(modrinthDownloadCount)

	if modrinthDownloadCount > 0:
		with open(rootPath + sep + "templates" + sep + "modrinth.svg", 'r') as modrinthSvgTemplateFile:
			modrinthSvgTemplate = modrinthSvgTemplateFile.read()

		with open(rootPath + sep + "svg" + sep + "modrinth.svg", 'w') as modrinthSvgFile:
			modrinthSvgFile.write(modrinthSvgTemplate.replace("%N", formattedModrinthDownloadCount.upper()))

		print(fprefix + "Created the Modrinth SVG file with " + formattedModrinthDownloadCount + " downloads.")
	else:
		print(fprefix + "The Modrinth count returned < 0. Ignoring.")



	print("\n" + fprefix + "Starting the SVG file creation for Patreon.")

	patreonMemberCount = getPatreonMemberCount(apiDataPath)
	formattedPatreonCount = formatToReadableNumber(patreonMemberCount)

	if patreonMemberCount > 0:
		with open(rootPath + sep + "templates" + sep + "patreon.svg", 'r') as patreonSvgTemplateFile:
			patreonSvgTemplate = patreonSvgTemplateFile.read()

		with open(rootPath + sep + "svg" + sep + "patreon.svg", 'w') as patreonSvgFile:
			patreonSvgFile.write(patreonSvgTemplate.replace("%N", formattedPatreonCount.upper()))

		print(fprefix + "Created the Patreon SVG file with " + formattedPatreonCount + " members.")
	else:
		print(fprefix + "The Patreon count returned < 0. Ignoring.")



	print("\n" + fprefix + "Starting the SVG file creation for YouTube.")

	youtubeSubscriberCount = getYoutubeSubscriberCount(apiDataPath)
	formattedYoutubeSubCount = formatToReadableNumber(youtubeSubscriberCount)

	if youtubeSubscriberCount > 0:
		with open(rootPath + sep + "templates" + sep + "youtube.svg", 'r') as youtubeSvgTemplateFile:
			youtubeSvgTemplate = youtubeSvgTemplateFile.read()

		with open(rootPath + sep + "svg" + sep + "youtube.svg", 'w') as youtubeSvgFile:
			youtubeSvgFile.write(youtubeSvgTemplate.replace("%N", formattedYoutubeSubCount.upper()))

		print(fprefix + "Created the YouTube SVG file with " + formattedYoutubeSubCount + " subscribers.")
	else:
		print(fprefix + "The Youtube count returned < 0. Ignoring.")


	print("\n" + fprefix + "Done with generating the SVG badges!")
	return

def getCurseForgeDownloadCount(apiDataPath):
	try:
		with open(apiDataPath + sep + "curseforge.json", 'r') as f:
			mods = json.load(f)

		downloadCount = 0
		for mod in mods:
			downloadCount += mod.get("downloadCount", 0)

		return downloadCount if downloadCount > 0 else -1

	except Exception:
		return -1

def getModrinthDownloadCount(apiDataPath):
	try:
		with open(apiDataPath + sep + "modrinth.json", 'r') as f:
			hits = json.load(f)

		totalDownloads = 0
		for hit in hits:
			totalDownloads += hit.get("downloads", 0)

		return totalDownloads if totalDownloads > 0 else -1

	except Exception:
		return -1

def getPatreonMemberCount(apiDataPath):
	try:
		with open(apiDataPath + sep + "patreon.json", 'r') as f:
			data = json.load(f)

		return data.get("memberCount", -1)

	except Exception:
		return -1

def getYoutubeSubscriberCount(apiDataPath):
	try:
		with open(apiDataPath + sep + "youtube.json", 'r') as f:
			data = json.load(f)

		return data.get("subscriberCount", -1)

	except Exception:
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
