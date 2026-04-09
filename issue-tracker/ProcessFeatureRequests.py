# -*- coding: utf-8 -*-
#!/usr/bin/env python
from datetime import datetime
import json
import os
import requests

sep = os.path.sep

QUERY = """
query($cursor: String) {
  repository(owner: "Serilum", name: ".issue-tracker") {
    issues(first: 25, after: $cursor, states: CLOSED, labels: ["Feature Request"], orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        databaseId
        number
        title
        createdAt
        stateReason
        author { login }
        labels(first: 10) {
          nodes { name }
        }
        reactions(first: 100) {
          nodes {
            content
            user { login }
          }
        }
        comments(first: 100) {
          nodes {
            author { login }
            reactions(first: 100) {
              nodes {
                content
                user { login }
              }
            }
          }
        }
      }
    }
  }
}
"""

REACTION_MAP = {
	"THUMBS_UP": "+1",
	"THUMBS_DOWN": "-1",
	"LAUGH": "laugh",
	"HOORAY": "hooray",
	"CONFUSED": "confused",
	"HEART": "heart",
	"ROCKET": "rocket",
	"EYES": "eyes",
}


def fetchAllIssues(token):
	headers = {"Authorization": "bearer " + token}
	allIssues = []
	cursor = None

	while True:
		variables = {"cursor": cursor}
		resp = requests.post("https://api.github.com/graphql", json={"query": QUERY, "variables": variables}, headers=headers)

		if resp.status_code != 200:
			print("  GraphQL request failed:", resp.status_code, resp.text)
			break

		data = resp.json()
		if "errors" in data:
			print("  GraphQL errors:", data["errors"])
			break

		issuesData = data["data"]["repository"]["issues"]
		allIssues.extend(issuesData["nodes"])

		pageInfo = issuesData["pageInfo"]
		if not pageInfo["hasNextPage"]:
			break

		cursor = pageInfo["endCursor"]
		print("  Fetched", len(allIssues), "issues so far.")

	return allIssues


def processIssue(issue):
	if issue["stateReason"] != "NOT_PLANNED":
		return None

	number = issue["number"]
	dbId = issue["databaseId"]
	title = issue["title"]
	openedBy = issue["author"]["login"] if issue["author"] else "ghost"

	try:
		creationDate = issue["createdAt"].split("T")[0]
	except Exception:
		creationDate = ""

	modName = ""
	labels = []
	for labelNode in issue["labels"]["nodes"]:
		name = labelNode["name"]
		if name not in labels:
			labels.append(name)
		if "Mod: " in name:
			modName = name.replace("Mod: ", "").strip()

	dataField = "standalone-feature" if len(labels) == 1 else "mod-feature"

	reactedUsers = []
	reactions = {}

	for r in issue["reactions"]["nodes"]:
		rc = REACTION_MAP.get(r["content"], r["content"])
		reactions[rc] = reactions.get(rc, 0) + 1

		if rc != "-1" and rc != "confused":
			username = r["user"]["login"] if r["user"] else "ghost"
			if username not in reactedUsers:
				reactedUsers.append(username)

	commentedUsers = []
	totalCommentCount = 0
	userCommentCount = 0

	for comment in issue["comments"]["nodes"]:
		totalCommentCount += 1

		for cr in comment["reactions"]["nodes"]:
			rc = REACTION_MAP.get(cr["content"], cr["content"])
			reactions[rc] = reactions.get(rc, 0) + 1

			if rc != "-1" and rc != "confused":
				username = cr["user"]["login"] if cr["user"] else "ghost"
				if username not in reactedUsers:
					reactedUsers.append(username)

		commentUser = comment["author"]["login"] if comment["author"] else "ghost"
		if commentUser == "ricksouth":
			continue

		if commentUser not in commentedUsers:
			commentedUsers.append(commentUser)
			userCommentCount += 1

	if openedBy not in commentedUsers:
		commentedUsers.append(openedBy)
		totalCommentCount += 1
		userCommentCount += 1

	if openedBy not in reactedUsers:
		reactedUsers.append(openedBy)

	reactionCount = len(reactedUsers)

	return {
		"data_field": dataField,
		"number": number,
		"entry": {
			"id": dbId,
			"number": number,
			"title": title,
			"opened_by": openedBy,
			"creation_date": creationDate,
			"labels": labels,
			"mod_name": modName,
			"reactions": reactions,
			"reaction_count": reactionCount,
			"total_comment_count": totalCommentCount,
			"user_comment_count": userCommentCount,
		},
	}


def main(mainPath):
	fprefix = " [Process Feature Requests] "
	print("\n" + fprefix + "Starting.\n")

	rootPath = "." + sep + "issue-tracker"
	if os.environ["IS_PRODUCTION"] == "false":
		rootPath = mainPath + sep + "issue-tracker"

	token = os.environ["GH_SERILUM_ORG_ACCESS_TOKEN"]

	print(fprefix + "Fetching issues via GraphQL.")
	allIssues = fetchAllIssues(token)
	print(fprefix + "Fetched " + str(len(allIssues)) + " total closed feature requests.")

	output = {"data": {"mod-feature": {}, "standalone-feature": {}}}
	issuesSortedReactionCount = {}

	for issue in allIssues:
		result = processIssue(issue)
		if result is None:
			continue

		number = result["number"]
		print(fprefix + "Processing issue #" + str(number))

		output["data"][result["data_field"]][number] = result["entry"]
		issuesSortedReactionCount[number] = result["entry"]["reaction_count"]

	output["issues_sorted_reaction_count"] = list(
		reversed(sorted(issuesSortedReactionCount.items(), key=lambda x: x[1]))
	)

	lastUpdated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
	print(fprefix + "Last updated output:", lastUpdated)
	output["last_updated"] = lastUpdated

	jsonOutputPath = rootPath + sep + "data" + sep + "feature-request-data.json"
	print(fprefix + "Writing output to: " + jsonOutputPath)

	with open(jsonOutputPath, "w") as f:
		f.write(json.dumps(output, indent=2))

	with open(jsonOutputPath.replace(".json", ".min.json"), "w") as f:
		f.write(json.dumps(output))

	print("\n" + fprefix + "Finished.")


if __name__ == "__main__":
	main("")
