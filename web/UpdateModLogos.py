# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
from PIL 						import Image, ImageSequence
from io 						import BytesIO
import requests
import subprocess
import json
import time
import re
import os
import sys

sep = os.path.sep

skipMods = ["OP Permission Fallback"]

logoTargets = [64, 128, 256, 512]

def main(mainPath):
	fprefix = " [Update Mod Logos] "

	print("\n" + fprefix + "Starting the logo generation.")

	webPath = "." + sep + "web"
	apiDataPath = "." + sep + "api" + sep + "data"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		webPath = mainPath + sep + "web"
		apiDataPath = mainPath + sep + "api" + sep + "data"

	logoPath = webPath + sep + "logo"
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

	mainByName = {}
	for mod in curseForgeMods:
		slug = mod.get("slug", "")
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

	print(fprefix + "Processing " + str(len(mainByName)) + " logos.")

	for modName in naturalSort(list(mainByName.keys())):
		mod = mainByName[modName]
		slug = mod.get("slug", "")

		mrProject = mrByName.get(modName)
		iconUrl = mod.get("logo", "") or ""
		if iconUrl == "" and mrProject is not None:
			iconUrl = mrProject.get("icon_url", "") or ""

		saveLogo(fprefix, iconUrl, logoPath, slug)

		time.sleep(0.05)

	print(fprefix + "Done!")

def saveLogo(fprefix, iconUrl, logoPath, slug):
	existing = findExistingLogo(logoPath, slug)
	if existing is not None:
		return existing

	if iconUrl == "":
		print(fprefix + slug + " has no icon.")
		return ".png", []

	try:
		response = requests.get(iconUrl, timeout=15)
		image = Image.open(BytesIO(response.content))
	except Exception as e:
		print(fprefix + "Error fetching logo for " + slug + ": " + str(e))
		return ".png", []

	isAnimated = iconUrl.lower().endswith(".gif") and getattr(image, "is_animated", False)
	fileType = ".gif" if isAnimated else ".png"

	for size in logoTargets:
		sizeFolder = logoPath + sep + str(size)
		Path(sizeFolder).mkdir(parents=True, exist_ok=True)
		outPath = sizeFolder + sep + slug + fileType

		try:
			if isAnimated:
				frames = []
				for frame in ImageSequence.Iterator(image):
					newFrame = frame.copy().convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
					frames.append(newFrame)

				frames[0].save(outPath, save_all=True, append_images=frames[1:], **image.info)
			else:
				resized = image.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
				resized.save(outPath)
				compressLogo(outPath)

		except Exception as e:
			print(fprefix + "Error saving logo for " + slug + " at " + str(size) + ": " + str(e))

	return fileType, list(logoTargets)

def findExistingLogo(logoPath, slug):
	if not os.path.isdir(logoPath):
		return None

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

	if not sizes:
		return None

	return fileType, sorted(sizes)

def compressLogo(pngPath):
	try:
		subprocess.run(["pngquant", "--force", "--skip-if-larger", "--quality=65-90", "--output", pngPath, pngPath], check=False)
	except FileNotFoundError:
		pass

def naturalSort(items):
	def naturalKey(value):
		return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', value.lower())]

	return sorted(items, key=naturalKey)

if __name__ == "__main__":
	main("")
