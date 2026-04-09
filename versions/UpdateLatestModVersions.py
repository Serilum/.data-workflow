# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
import requests
import json
import time
import re
import os
import sys

sep = os.path.sep

PARSE_LEGACY_FABRIC = False

def main(mainPath):
	fprefix = " [Update Latest Mod Versions] "

	print("\n" + fprefix + "Starting the generation.")

	rootPath = "." + sep + "versions"
	apiDataPath = "." + sep + "api" + sep + "data"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		rootPath = mainPath + sep + "versions"
		apiDataPath = mainPath + sep + "api" + sep + "data"

	dataPath = rootPath + sep + "data"
	Path(dataPath).mkdir(parents=True, exist_ok=True)

	try:
		with open(apiDataPath + sep + "curseforge.json", 'r') as f:
			mods = json.load(f)
	except Exception:
		print(fprefix + "Could not read CurseForge data. Skipping.")
		return

	print(fprefix + "Processing " + str(len(mods)) + " mods.")

	modsWritten = 0
	for mod in mods:
		slug = mod.get("slug", "")
		modId = mod.get("id", 0)
		if not slug or not modId:
			continue

		print(fprefix + "Fetching versions for: " + slug)

		if not PARSE_LEGACY_FABRIC and slug.endswith("-fabric"):
			continue

		versions = fetchModVersions(fprefix, modId)
		time.sleep(0.1)

		if versions:
			sortedVersions = sortMinecraftVersions(versions)

			filepath = dataPath + sep + slug + ".json"
			with open(filepath, 'w') as f:
				json.dump(sortedVersions, f, indent=2)

			with open(dataPath + sep + slug + ".min.json", 'w') as f:
				json.dump(sortedVersions, f)

			modsWritten += 1
			print(fprefix + "Processed: " + slug + " (" + str(len(sortedVersions)) + " versions)")

	print(fprefix + "Wrote " + str(modsWritten) + " mod version files.")
	print(fprefix + "Done!")

def fetchModVersions(fprefix, modId):
	versions = {}
	index = 0

	try:
		while True:
			response = requests.get(
				"https://api.curseforge.com/v1/mods/" + str(modId) + "/files?index=" + str(index),
				headers = {
					"x-api-key": os.environ["CURSEFORGE_API_KEY"],
					"Accept": "application/json"
				},
				timeout=15
			)
			filesJson = response.json()

			if "data" not in filesJson:
				break

			for fileEntry in filesJson["data"]:
				filename = fileEntry.get("fileName", "")

				mcVersions = []
				loaders = []

				for sgv in fileEntry.get("sortableGameVersions", []):
					versionName = sgv.get("gameVersionName", "")

					if versionName in ("Forge", "Fabric", "Quilt", "NeoForge"):
						loaders.append(versionName)
					elif sgv.get("gameVersion", ""):
						mcVersions.append(sgv["gameVersion"])

				if not loaders:
					continue

				for mcVersion in mcVersions:
					modVersion = parseModVersion(filename, mcVersion)

					if not modVersion:
						modVersion = parseModVersionFromEnd(filename)

					if modVersion:
						if mcVersion not in versions:
							versions[mcVersion] = {}

						for loader in loaders:
							if loader not in versions[mcVersion]:
								versions[mcVersion][loader] = modVersion

			if "pagination" in filesJson:
				if filesJson["pagination"]["resultCount"] < 50:
					break
			else:
				break

			index += 50

	except Exception as e:
		print(fprefix + "Error fetching files for mod " + str(modId) + ": " + str(e))

	return versions

def parseModVersion(filename, mcVersion):
	name = filename
	if name.endswith(".jar"):
		name = name[:-4]

	name = name.replace("_", "-")

	mcEscaped = re.escape(mcVersion)
	match = re.search(mcEscaped + "[- ](.+)", name)
	if match:
		return match.group(1)

	return None

def parseModVersionFromEnd(filename):
	name = filename
	if name.endswith(".jar"):
		name = name[:-4]

	lastDash = name.rfind("-")
	if lastDash != -1:
		return name[lastDash + 1:]

	return None

def sortMinecraftVersions(versions):
	def versionKey(version):
		parts = version.split(".")
		result = []
		for part in parts:
			try:
				result.append(int(part))
			except ValueError:
				result.append(0)
		return result

	sortedKeys = sorted(versions.keys(), key=versionKey, reverse=True)
	return {k: dict(sorted(versions[k].items())) for k in sortedKeys}

if __name__ == "__main__":
	main("")
