# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
import requests
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Constants

sep = os.path.sep

skipMods = ["OP Permission Fallback"]

modDataOverrides = {
	"Brand New Day": { "is_in_tenfold": True },
}

def main(mainPath):
	fprefix = " [Update Mod Data] "

	print("\n" + fprefix + "Starting the generation.")

	webPath = "." + sep + "web"
	dataPath = "." + sep + "mods" + sep + "data"
	apiDataPath = "." + sep + "api" + sep + "data"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		webPath = mainPath + sep + "web"
		dataPath = mainPath + sep + "mods" + sep + "data"
		apiDataPath = mainPath + sep + "api" + sep + "data"

	logoPath = webPath + sep + "logo"
	Path(dataPath).mkdir(parents=True, exist_ok=True)

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

	tveMods = []
	try:
		with open(apiDataPath + sep + "tve_mods.json", 'r') as f:
			tveMods = json.load(f)
	except Exception:
		print(fprefix + "Could not read The Vanilla Experience mod list. Continuing without it.")

	tenfoldMods = []
	try:
		with open(apiDataPath + sep + "tenfold_mods.json", 'r') as f:
			tenfoldMods = json.load(f)
	except Exception:
		print(fprefix + "Could not read the Tenfold mod list. Continuing without it.")

	translatedModIds = set()
	try:
		with open(apiDataPath + sep + "translations_en_us.json", 'r') as f:
			englishLang = json.load(f)

		commentPrefix = "_comment_modname_"
		for key in englishLang:
			if key.startswith(commentPrefix):
				translatedModIds.add(key[len(commentPrefix):])
		translatedModIds.discard("shared")
	except Exception:
		print(fprefix + "Could not read English translation keys. Continuing without it.")

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

	tveProjectIds = set()
	tveIncludedMods = []
	for tveMod in tveMods:
		modId = tveMod.get("id", 0)
		tveProjectIds.add(modId)
		tveIncludedMods.append({
			"name": tveMod.get("name", ""),
			"slug": tveMod.get("slug", ""),
			"curseforge_projectid": modId,
			"is_serilum": modId in cfById,
		})
	tveIncludedMods = sorted(tveIncludedMods, key = lambda m: m["name"].lower())

	tenfoldProjectIds = set()
	tenfoldIncludedMods = []
	for tenfoldMod in tenfoldMods:
		modId = tenfoldMod.get("id", 0)
		tenfoldProjectIds.add(modId)
		tenfoldIncludedMods.append({
			"name": tenfoldMod.get("name", ""),
			"slug": tenfoldMod.get("slug", ""),
			"curseforge_projectid": modId,
			"is_serilum": modId in cfById,
		})
	tenfoldIncludedMods = sorted(tenfoldIncludedMods, key = lambda m: m["name"].lower())

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
		environment = ""
		if mrProject is not None:
			environment = simplifyEnvironment(mrProject.get("environment", []))
		elif mod.get("status", 0) == 4:
			print(fprefix + "No Modrinth project matched '" + modName + "'; environment left undetermined.")

		logoFileType, logoSizes = getLogoInfo(logoPath, slug)

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
		specificData["logo_sizes"] = logoSizes
		specificData["published"] = mod.get("status", 0) == 4
		specificData["is_bundle"] = isBundle
		specificData["bundle_category"] = bundleCategories.get(modName.replace("[", "").replace("]", ""), "")
		specificData["curseforge_projectid"] = mod.get("id", -1)
		specificData["curseforge_legacy_fabric_projectid"] = fabricProjectId
		specificData["environment"] = environment
		specificData["project_type"] = Constants.projectTypes.get(mod.get("classId", 0), "other")
		specificData["is_in_tve"] = mod.get("id", 0) in tveProjectIds or fabricProjectId in tveProjectIds
		specificData["is_in_tenfold"] = mod.get("id", 0) in tenfoldProjectIds or fabricProjectId in tenfoldProjectIds
		specificData["has_translations"] = slug.replace("-", "") in translatedModIds

		if mod.get("id", 0) == Constants.tveProjectId:
			specificData["included_mods"] = tveIncludedMods

		if mod.get("id", 0) == Constants.tenfoldProjectId:
			specificData["included_mods"] = tenfoldIncludedMods

		specificData.update(modDataOverrides.get(modName, {}))

		modData[modName] = specificData
		print(fprefix + "Processed: " + modName)

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

def getLogoInfo(logoPath, slug):
	if not os.path.isdir(logoPath):
		return ".png", []

	sizes = []
	fileType = ".png"
	for entry in os.listdir(logoPath):
		folder = logoPath + sep + entry
		if not (entry.isdigit() and os.path.isdir(folder)):
			continue

		if os.path.isfile(folder + sep + slug + ".gif"):
			sizes.append(int(entry))
			fileType = ".gif"
		elif os.path.isfile(folder + sep + slug + ".png"):
			sizes.append(int(entry))

	return fileType, sorted(sizes)

def simplifyEnvironment(environment):
	if not environment:
		return ""

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

	return ""

def getLoaderVersions(moddata):
	loaderVersions = { "forge" : set(), "fabric" : set(), "neoforge" : set() }

	if moddata is None or "latestFilesIndexes" not in moddata:
		return loaderVersions

	for entry in moddata["latestFilesIndexes"]:
		loaderKey = Constants.loaderIds.get(entry.get("modLoader"))
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
