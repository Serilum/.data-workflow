# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
from PIL 						import Image, ImageSequence
from io 						import BytesIO
import requests
import json
import time
import re
import os
import sys

sep = os.path.sep

skipMods = ["OP Permission Fallback"]

loaderIds = { 1 : "forge", 4 : "fabric", 6 : "neoforge" }

def main(mainPath):
	fprefix = " [Update Mod Data] "

	print("\n" + fprefix + "Starting the generation.")

	rootPath = "." + sep + "web"
	apiDataPath = "." + sep + "api" + sep + "data"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		rootPath = mainPath + sep + "web"
		apiDataPath = mainPath + sep + "api" + sep + "data"

	dataPath = rootPath + sep + "data"
	logoPath = rootPath + sep + "logo"
	Path(dataPath).mkdir(parents=True, exist_ok=True)
	Path(logoPath).mkdir(parents=True, exist_ok=True)

	try:
		with open(apiDataPath + sep + "curseforge.json", 'r') as f:
			curseForgeMods = json.load(f)
	except Exception:
		print(fprefix + "Could not read CurseForge data. Skipping.")
		return

	modrinthProjects = []
	try:
		with open(apiDataPath + sep + "modrinth_projects.json", 'r') as f:
			modrinthProjects = json.load(f)
	except Exception:
		print(fprefix + "Could not read Modrinth project data. Continuing without it.")

	bundleCategories = fetchBundleCategories(fprefix)

	cfBySlug = {}
	cfById = {}
	mainByName = {}
	for mod in curseForgeMods:
		slug = mod.get("slug", "")
		modId = mod.get("id", 0)

		cfById[modId] = mod
		if slug:
			cfBySlug[slug] = mod

		if slug.endswith("-fabric") or slug.endswith("-fabric-version"):
			continue

		modName = mod.get("name", "")
		if modName == "" or modName in skipMods:
			continue

		mainByName[modName] = mod

	mrByName = {}
	for project in modrinthProjects:
		name = project.get("name", "")
		if name:
			mrByName[name] = project

	print(fprefix + "Processing " + str(len(mainByName)) + " mods.")

	modData = {}
	for modName in naturalSort(list(mainByName.keys())):
		mod = mainByName[modName]
		slug = mod.get("slug", "")

		loaderVersions = getLoaderVersions(mod)
		forgeVersions = sortVersionsDesc(loaderVersions["forge"])
		fabricVersions = sortVersionsDesc(loaderVersions["fabric"])
		neoforgeVersions = sortVersionsDesc(loaderVersions["neoforge"])
		versionLatest = getLatestFullVersions(mod)

		isBundle = "Serilum's" in modName and "Bundle" in modName

		fabricSlug = ""
		fabricVersionLatest = {}
		fabricProjectId = -1
		fabricMod = cfBySlug.get(slug + "-fabric")
		if fabricMod is None:
			fabricMod = cfBySlug.get(slug + "-fabric-version")
		if fabricMod is not None:
			fabricProjectId = fabricMod.get("id", -1)
			fabricVersionLatest = getLatestFullVersions(fabricMod)
			if len(fabricVersions) > 0:
				fabricSlug = fabricMod.get("slug", "")

		dependencies = []
		if isBundle:
			dependencies = ["collective"]
		else:
			for depId in mod.get("dependencies", []):
				depMod = cfById.get(depId)
				if depMod is not None:
					depSlug = depMod.get("slug", "")
					if depSlug != "" and depSlug not in dependencies:
						dependencies.append(depSlug)
			dependencies = naturalSort(dependencies)

		mrProject = mrByName.get(modName)
		environment = "both"
		iconUrl = ""
		if mrProject is not None:
			environment = simplifyEnvironment(mrProject.get("environment", []))
			iconUrl = mrProject.get("icon_url", "") or ""

		logoFileType = saveLogo(fprefix, iconUrl, logoPath, slug)

		specificData = {}
		specificData["description"] = mod.get("summary", "")
		specificData["slug"] = slug
		specificData["fabric_slug"] = fabricSlug
		specificData["fabric_versions"] = fabricVersions
		specificData["forge_versions"] = forgeVersions
		specificData["neoforge_versions"] = neoforgeVersions
		specificData["version_latest"] = versionLatest
		specificData["fabric_version_latest"] = fabricVersionLatest
		specificData["dependencies"] = dependencies
		specificData["logo_file_type"] = logoFileType
		specificData["published"] = mod.get("status", 0) == 4
		specificData["is_bundle"] = isBundle
		specificData["bundle_category"] = bundleCategories.get(modName, "")
		specificData["curseforge_projectid"] = mod.get("id", -1)
		specificData["curseforge_legacy_fabric_projectid"] = fabricProjectId
		specificData["environment"] = environment

		modData[modName] = specificData
		print(fprefix + "Processed: " + modName)

		time.sleep(0.05)

	with open(dataPath + sep + "mod_data.json", 'w') as f:
		json.dump(modData, f, indent=2)

	with open(dataPath + sep + "mod_data.min.json", 'w') as f:
		json.dump(modData, f)

	print(fprefix + "Wrote mod data for " + str(len(modData)) + " mods.")
	print(fprefix + "Done!")

def fetchBundleCategories(fprefix):
	try:
		response = requests.get("https://data.serilum.com/json/bundles.json", timeout=15)
		return response.json()
	except Exception as e:
		print(fprefix + "Error fetching bundle categories: " + str(e))
		return {}

def saveLogo(fprefix, iconUrl, logoPath, slug):
	pngPath = logoPath + sep + slug + ".png"
	gifPath = logoPath + sep + slug + ".gif"

	if os.path.isfile(pngPath):
		return ".png"
	if os.path.isfile(gifPath):
		return ".gif"

	if iconUrl == "":
		print(fprefix + slug + " has no Modrinth icon.")
		return ".png"

	try:
		response = requests.get(iconUrl, timeout=15)
		image = Image.open(BytesIO(response.content))

		if iconUrl.lower().endswith(".gif") and getattr(image, "is_animated", False):
			frames = []
			for frame in ImageSequence.Iterator(image):
				newFrame = frame.copy()
				newFrame.thumbnail((100, 100), Image.Resampling.LANCZOS)
				frames.append(newFrame)

			frames[0].save(gifPath, save_all=True, append_images=frames[1:], **image.info)
			return ".gif"

		resized = image.convert("RGBA").resize((100, 100))
		resized.save(pngPath)
		return ".png"

	except Exception as e:
		print(fprefix + "Error saving logo for " + slug + ": " + str(e))
		return ".png"

def simplifyEnvironment(environment):
	if not environment:
		return "both"

	value = environment[0]

	if value in ("client_and_server", "client_or_server", "client_or_server_prefers_both"):
		return "both"
	if value.startswith("client_only"):
		return "client"
	if value.startswith("server_only"):
		return "server"
	if value == "singleplayer_only":
		return "client"

	hasClient = "client" in value
	hasServer = "server" in value
	if hasClient and hasServer:
		return "both"
	if hasClient:
		return "client"
	if hasServer:
		return "server"

	return "both"

def getLoaderVersions(moddata):
	loaderVersions = { "forge" : set(), "fabric" : set(), "neoforge" : set() }

	if moddata is None or "latestFilesIndexes" not in moddata:
		return loaderVersions

	for entry in moddata["latestFilesIndexes"]:
		loaderKey = loaderIds.get(entry.get("modLoader"))
		if loaderKey is None:
			continue

		gameVersion = entry.get("gameVersion", "")
		if not gameVersion.replace(".", "").isdigit():
			continue

		loaderVersions[loaderKey].add(majorVersion(gameVersion))

	return loaderVersions

def getLatestFullVersions(moddata):
	latest = {}

	if moddata is None or "latestFilesIndexes" not in moddata:
		return latest

	for entry in moddata["latestFilesIndexes"]:
		gameVersion = entry.get("gameVersion", "")
		if not gameVersion.replace(".", "").isdigit():
			continue

		major = majorVersion(gameVersion)
		if major not in latest or compareVersions(gameVersion, latest[major]) > 0:
			latest[major] = gameVersion

	return latest

def majorVersion(gameVersion):
	spl = gameVersion.split(".")
	if len(spl) >= 2:
		return spl[0] + "." + spl[1]
	return gameVersion

def compareVersions(a, b):
	pa = [int(x) if x.isdigit() else 0 for x in a.split(".")]
	pb = [int(x) if x.isdigit() else 0 for x in b.split(".")]

	for i in range(max(len(pa), len(pb))):
		da = pa[i] if i < len(pa) else 0
		db = pb[i] if i < len(pb) else 0
		if da != db:
			return -1 if da < db else 1

	return 0

def sortVersionsDesc(versions):
	def versionKey(version):
		return [int(part) if part.isdigit() else 0 for part in version.split(".")]

	return sorted(versions, key=versionKey, reverse=True)

def naturalSort(items):
	def naturalKey(value):
		return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', value.lower())]

	return sorted(items, key=naturalKey)

if __name__ == "__main__":
	main("")
