# -*- coding: utf-8 -*-
#!/usr/bin/env python
from datetime						import datetime
from pytz 							import timezone
import json
import requests
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


	patrons = []

	try:
		githubSponsors = queryGithub()
	except Exception as e:
		print(fprefix + "Unable to receive Github Sponsors, keeping the previous list. " + str(e))
		githubSponsors = list(previousMembers["github"])


	try:
		patreonResult = queryPatreon()
	except Exception as e:
		print(fprefix + "Unable to receive Patreon members, keeping the previous list. " + str(e))
		patreonResult = previousMembers["patreon"]

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

	request.raise_for_status()
	githubJson = request.json()
	if githubJson.get('errors'):
		raise Exception(str(githubJson['errors']))

	sponsorNodes = githubJson['data']['organization']['sponsors']['nodes']

	githubSponsors = []
	for sponsorNode in sponsorNodes:
		if 'login' in sponsorNode:
			githubSponsors.append(sponsorNode['login'])

	return githubSponsors

def queryPatreon():
	patreonApiUrl = "https://www.patreon.com/api/oauth2/v2/"
	patreonHeaders = {"Authorization": "Bearer " + os.environ['PATREON_SERILUM_API_KEY']}

	campaignRequest = requests.get(patreonApiUrl + "campaigns", headers=patreonHeaders)
	campaignRequest.raise_for_status()
	campaignId = campaignRequest.json()['data'][0]['id']

	names = []
	membersUrl = patreonApiUrl + "campaigns/" + campaignId + "/members"
	membersParams = {"fields[member]": "full_name,patron_status", "page[count]": 100}
	while membersUrl:
		membersRequest = requests.get(membersUrl, headers=patreonHeaders, params=membersParams)
		membersRequest.raise_for_status()
		membersJson = membersRequest.json()
		getPatreonNames(membersJson['data'], names)

		membersUrl = membersJson.get('links', {}).get('next')
		membersParams = None

	return names

def getPatreonNames(members, names):
	for member in members:
		memberAttributes = member['attributes']
		if memberAttributes.get('patron_status') != "active_patron":
			continue

		names.append(memberAttributes['full_name'])

	return

def naturalsort(l): 
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanumKey = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanumKey)

if __name__ == "__main__":
	main("")