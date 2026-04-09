# -*- coding: utf-8 -*-
#!/usr/bin/env python
from datetime						import datetime
from pytz 							import timezone
import json
import requests
import patreon
import re
import os
import sys

sep = os.path.sep

def main(mainPath):
	fprefix = " [Update Membership Data] "

	print("\n" + fprefix + "Starting to receive Github Sponsors and Patreons.\n")

	rootPath = "." + sep + "membership" # For production
	if os.environ['IS_PRODUCTION'] == "false":
		rootPath = mainPath + sep + "membership" # For dev

	previousMembers = {}
	try:
		with open(rootPath + sep + "data" + sep + "members.json") as memberFile:
			previousMembers = json.load(memberFile)
	except:
		previousMembers["github"] = []
		previousMembers["patreon"] = []


	githubSponsors = []
	patrons = []

	githubResult = queryGithub()
	if 'data' in githubResult:
		ghData = githubResult['data']
		if 'organization' in ghData:
			ghUser = ghData['organization']
			if 'sponsors' in ghUser:
				ghSponsorData = ghUser['sponsors']
				if 'nodes' in ghSponsorData:
					ghNodes = ghSponsorData['nodes']
					for ghNode in ghNodes:
						if 'login' in ghNode:
							ghLogin = ghNode['login']
							githubSponsors.append(ghLogin)


	patreonResult = queryPatreon()
	for pResult in patreonResult:
		patrons.append(pResult.strip())


	githubSponsors = naturalsort(githubSponsors)
	patrons = naturalsort(patrons)

	print(fprefix + "Received membership data from GitHub and Patreon.")

	dataOut = {"github": githubSponsors, "patreon": patrons}

	combinedList = naturalsort(githubSponsors + patrons)

	newMembers = []
	combinedSpecific = {}
	for member in combinedList:
		if member in githubSponsors:
			combinedSpecific[member] = "Github Sponsors"
			if member not in previousMembers["github"]:
				newMembers.append([member, "github"])
		elif member in patrons:
			combinedSpecific[member] = "Patreon"
			if member not in previousMembers["patreon"]:
				newMembers.append([member, "patreon"])

	print(fprefix + "Checking if the feed page needs to be updated.")
	if len(newMembers) > 0:
		ymd = datetime.now(timezone('Europe/Amsterdam')).strftime("%Y%m%d")
		
		feed = {}
		with open(rootPath + sep + "data" + sep + "feed.json") as feedFile:
			feed = json.load(feedFile)

		if not ymd in feed["keys"]:
			feed["keys"].append(ymd)
			feed["entries"][ymd] = []

		feed["keys"] = naturalsort(feed["keys"])

		for newMember in newMembers:
			subelement = {"name": newMember[0], "platform": newMember[1]}

			feed["entries"][ymd].append(subelement)

		with open(rootPath + sep + "data" + sep + "feed.json", "w") as feedFile:
			json.dump(feed, feedFile, indent=4, sort_keys=True)

		with open(rootPath + sep + "data" + sep + "feed.min.json", "w") as feedFile:
			json.dump(feed, feedFile, sort_keys=True)

		print(fprefix + "Updated feed.json file.")
		

	dataOut["combined"] = combinedList
	dataOut["combined_specific"] = combinedSpecific

	with open(rootPath + sep + "data" + sep + "members.json", "w") as memberFile:
		memberFile.write(json.dumps(dataOut, indent=4))

	with open(rootPath + sep + "data" + sep + "members.min.json", "w") as memberFile:
		memberFile.write(json.dumps(dataOut))

	print("\n" + fprefix + "Finished receiving Github Sponsors and Patreons.")
	return

def queryGithub():
	githubHeaders = {"Authorization": "bearer " + os.environ['GH_SERILUM_ORG_ACCESS_TOKEN']}
	githubQuery = """
	{  
		organization(login: "serilum") {
			... on Sponsorable {
				sponsors(first: 100) {
					totalCount
					nodes {
						... on User {
							login
						}
						... on Organization {
							login
						}
					}
				}
			}
		}
	}"""

	request = requests.post('https://api.github.com/graphql', json={'query': githubQuery}, headers=githubHeaders)
	
	# print("GitHub API response:", request.json())
	
	if request.status_code == 200:
		return request.json()

	return {}

def queryPatreon():
	apiClient = patreon.API(os.environ['PATREON_SERILUM_API_KEY'])
	campaignId = apiClient.fetch_campaign().data()[0].id()
	cursor = None
	names = []
	while True:
		pledgesResponse = apiClient.fetch_page_of_pledges(
			campaignId,
			25,
			cursor=cursor,
		)
		getPatreonNames(pledgesResponse.data(), pledgesResponse, names)
		cursor = apiClient.extract_cursor(pledgesResponse)
		if not cursor:
			break

	return names

def getPatreonNames(allPledges, pledgesResponse, names):
	for pledge in allPledges:
		patronId = pledge.relationship('patron').id()
		patron = pledgesResponse.find_resource_by_type_and_id('user', patronId)
		names.append(patron.attribute('full_name'))
		
	return

def naturalsort(l): 
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanumKey = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanumKey)

if __name__ == "__main__":
	main("")