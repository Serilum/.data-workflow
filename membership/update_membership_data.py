# -*- coding: utf-8 -*-
#!/usr/bin/env python
# from bs4 							import BeautifulSoup
from datetime						import datetime
from pytz 							import timezone
import json
import requests
import patreon
import re
import os
import sys

sep = os.path.sep

def main(mainpath):
	fprefix = " [Update Membership Data] "

	print("\n" + fprefix + "Starting to receive Github Sponsors and Patreons.\n")

	rootpath = "." + sep + "membership" # For production
	if os.environ['IS_PRODUCTION'] == "false":
		rootpath = mainpath + sep + "membership" # For dev

	previousmembers = {}
	try:
		with open(rootpath + sep + "data" + sep + "members.json") as memberfile:
			previousmembers = json.load(memberfile)
	except:
		previousmembers["github"] = []
		previousmembers["patreon"] = []


	githubsponsors = []
	patrons = []

	githubresult = queryGithub()
	if 'data' in githubresult:
		ghdata = githubresult['data']
		if 'organization' in ghdata:
			ghuser = ghdata['organization']
			if 'sponsors' in ghuser:
				ghsponsors = ghuser['sponsors']
				if 'nodes' in ghsponsors:
					ghnodes = ghsponsors['nodes']
					for ghnode in ghnodes:
						if 'login' in ghnode:
							ghlogin = ghnode['login']
							githubsponsors.append(ghlogin)


	patreonresult = queryPatreon()
	for presult in patreonresult:
		patrons.append(presult.strip())


	githubsponsors = naturalsort(githubsponsors)
	patrons = naturalsort(patrons)

	print(fprefix + "Received membership data from GitHub and Patreon.")

	dataout = {}
	dataout["github"] = githubsponsors
	dataout["patreon"] = patrons

	combinedlist = naturalsort(githubsponsors + patrons)

	newmembers = []
	combinedspecific = {}
	for member in combinedlist:
		if member in githubsponsors:
			combinedspecific[member] = "Github Sponsors"
			if member not in previousmembers["github"]:
				newmembers.append([member, "github"])
		elif member in patrons:
			combinedspecific[member] = "Patreon"
			if member not in previousmembers["patreon"]:
				newmembers.append([member, "patreon"])

	print(fprefix + "Checking if the feed page needs to be updated.")
	if len(newmembers) > 0:
		ymd = datetime.now(timezone('Europe/Amsterdam')).strftime("%Y%m%d")
		
		feed = {}
		with open(rootpath + sep + "data" + sep + "feed.json") as feedfile:
			feed = json.load(feedfile)

		if not ymd in feed["keys"]:
			feed["keys"].append(ymd)
			feed["entries"][ymd] = []

		feed["keys"] = naturalsort(feed["keys"])

		for newmember in newmembers:
			subelement = {}
			subelement["name"] = newmember[0]
			subelement["platform"] = newmember[1]

			feed["entries"][ymd].append(subelement)

		with open(rootpath + sep + "data" + sep + "feed.json", "w") as feedfile:
			json.dump(feed, feedfile, indent=4, sort_keys=True)

		print(fprefix + "Updated feed.json file.")
		

	dataout["combined"] = combinedlist
	dataout["combined_specific"] = combinedspecific

	with open(rootpath + sep + "data" + sep + "members.json", "w") as memberfile:
		memberfile.write(json.dumps(dataout, indent=4))

	print("\n" + fprefix + "Finished receiving Github Sponsors and Patreons.")
	return

def queryGithub():
	githubheaders = {"Authorization": "bearer " + os.environ['GH_SERILUM_DATA_WORKFLOW_API']}
	githubquery = """
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

	request = requests.post('https://api.github.com/graphql', json={'query': githubquery}, headers=githubheaders)
	
	# print("GitHub API response:", request.json())
	
	if request.status_code == 200:
		return request.json()

	return {}

def queryPatreon():
	api_client = patreon.API(os.environ['PATREON_API'])
	campaign_id = api_client.fetch_campaign().data()[0].id()
	cursor = None
	names = []
	while True:
		pledges_response = api_client.fetch_page_of_pledges(
			campaign_id,
			25,
			cursor=cursor,
		)
		getPatreonNames(pledges_response.data(), pledges_response, names)
		cursor = api_client.extract_cursor(pledges_response)
		if not cursor:
			break

	return names

def getPatreonNames(all_pledges, pledges_response, names):
	for pledge in all_pledges:
		patron_id = pledge.relationship('patron').id()
		patron = pledges_response.find_resource_by_type_and_id('user', patron_id)
		names.append(patron.attribute('full_name'))
		
	return

def naturalsort(l): 
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanum_key)

if __name__ == "__main__":
	main("")