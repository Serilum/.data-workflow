# -*- coding: utf-8 -*-
#!/usr/bin/env python
from pathlib 						import Path
import html
import json
import os
import re
import sys

sep = os.path.sep

def main(mainPath):
	fprefix = " [Generate Member Badges] "

	print("\n" + fprefix + "Starting the member badge generation.")

	rootPath = "." + sep + "membership"
	if os.environ['IS_PRODUCTION'] == "false": # For dev
		rootPath = mainPath + sep + "membership"

	dataPath = rootPath + sep + "data"
	templatePath = rootPath + sep + "templates"
	outPath = dataPath + sep + "member-badges"
	Path(outPath).mkdir(parents=True, exist_ok=True)

	try:
		with open(dataPath + sep + "members.json") as memberFile:
			members = json.load(memberFile)
	except Exception:
		print(fprefix + "Could not read members.json. Ignoring.")
		return

	combined = members.get("combined", [])
	specific = members.get("combined_specific", {})

	if len(combined) == 0:
		print(fprefix + "No members found. Ignoring.")
		return

	count = 0
	for name in combined:
		platform = slugify(specific.get(name, ""))
		templateFile = templatePath + sep + "member-" + platform + ".svg"
		if not os.path.isfile(templateFile):
			print(fprefix + "No template for " + name + " (" + platform + "). Skipping.")
			continue

		with open(templateFile, 'r') as templateSvgFile:
			svg = templateSvgFile.read()

		padRight = readPadRight(svg)
		textStart, fontSize = readTextMetrics(svg)

		textWidth = measureText(name, fontSize)
		total = round(textStart - 1 + textWidth + padRight)
		viewBoxWidth = total + 6
		svgWidth = round(viewBoxWidth * 10 / 7)

		svg = svg.replace("%W%", str(svgWidth))
		svg = svg.replace("%VB%", str(viewBoxWidth))
		svg = svg.replace("%TOTAL2%", str(total - 2))
		svg = svg.replace("%TOTAL%", str(total))
		svg = svg.replace("%TEXTLEN%", str(textWidth))
		svg = svg.replace("%ARIA%", html.escape(name + " (" + specific.get(name, "") + ")"))
		svg = svg.replace("%NAME%", html.escape(name))

		with open(outPath + sep + slugify(name) + ".svg", 'w', encoding="utf-8") as badgeFile:
			badgeFile.write(svg)

		count += 1
		print(fprefix + "Wrote " + slugify(name) + ".svg.")

	print("\n" + fprefix + "Done. Generated " + str(count) + " member badges.")
	return

def measureText(name, fontSize):
	width = 0
	for c in name:
		if c in "MWmw":
			width += 0.95
		elif c in "iIljt.,'":
			width += 0.38
		elif c.isupper():
			width += 0.72
		elif c == " ":
			width += 0.35
		else:
			width += 0.64
	return max(round(width * fontSize), 1)

def readPadRight(template):
	return float(re.search(r'pad-right=([\d.]+)', template).group(1))

def readTextMetrics(template):
	match = re.search(r'<text x="([\d.]+)"[^>]*font-size="(\d+)"[^>]*>%NAME%', template)
	return float(match.group(1)), int(match.group(2))

def slugify(name):
	slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
	return slug or "member"

if __name__ == "__main__":
	main("")
