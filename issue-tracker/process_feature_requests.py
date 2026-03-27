# -*- coding: utf-8 -*-
#!/usr/bin/env python
from datetime import datetime
import json
import os
import requests

sep = os.path.sep

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($cursor: String) {
  repository(owner: "Serilum", name: ".issue-tracker") {
    issues(first: 100, after: $cursor, states: CLOSED, labels: ["Feature Request"], orderBy: {field: CREATED_AT, direction: DESC}) {
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

# Map GraphQL reaction names to PyGithub-style names (keeps output identical)
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


def fetch_all_issues(token):
	headers = {"Authorization": "bearer " + token}
	all_issues = []
	cursor = None

	while True:
		variables = {"cursor": cursor}
		resp = requests.post(GRAPHQL_URL, json={"query": QUERY, "variables": variables}, headers=headers)

		if resp.status_code != 200:
			print("  GraphQL request failed:", resp.status_code, resp.text)
			break

		data = resp.json()
		if "errors" in data:
			print("  GraphQL errors:", data["errors"])
			break

		issues_data = data["data"]["repository"]["issues"]
		all_issues.extend(issues_data["nodes"])

		page_info = issues_data["pageInfo"]
		if not page_info["hasNextPage"]:
			break

		cursor = page_info["endCursor"]
		print("  Fetched", len(all_issues), "issues so far...")

	return all_issues


def process_issue(issue):
	if issue["stateReason"] != "NOT_PLANNED":
		return None

	number = issue["number"]
	db_id = issue["databaseId"]
	title = issue["title"]
	openedby = issue["author"]["login"] if issue["author"] else "ghost"

	try:
		creationdate = issue["createdAt"].split("T")[0]
	except Exception:
		creationdate = ""

	# Labels
	modname = ""
	labels = []
	for label_node in issue["labels"]["nodes"]:
		name = label_node["name"]
		if name not in labels:
			labels.append(name)
		if "Mod: " in name:
			modname = name.replace("Mod: ", "").strip()

	data_field = "standalone-feature" if len(labels) == 1 else "mod-feature"

	# Reactions on the issue itself
	reacted_users = []
	reactions = {}

	for r in issue["reactions"]["nodes"]:
		rc = REACTION_MAP.get(r["content"], r["content"])
		reactions[rc] = reactions.get(rc, 0) + 1

		if rc != "-1" and rc != "confused":
			username = r["user"]["login"] if r["user"] else "ghost"
			if username not in reacted_users:
				reacted_users.append(username)

	# Comments and their reactions
	commented_users = []
	total_comment_count = 0
	user_comment_count = 0

	for comment in issue["comments"]["nodes"]:
		total_comment_count += 1

		# Comment reactions
		for cr in comment["reactions"]["nodes"]:
			rc = REACTION_MAP.get(cr["content"], cr["content"])
			reactions[rc] = reactions.get(rc, 0) + 1

			if rc != "-1" and rc != "confused":
				username = cr["user"]["login"] if cr["user"] else "ghost"
				if username not in reacted_users:
					reacted_users.append(username)

		comment_user = comment["author"]["login"] if comment["author"] else "ghost"
		if comment_user == "ricksouth":
			continue

		if comment_user not in commented_users:
			commented_users.append(comment_user)
			user_comment_count += 1

	# Add issue creator to comment count as +1
	if openedby not in commented_users:
		commented_users.append(openedby)
		total_comment_count += 1
		user_comment_count += 1

	# Add issue creator to reaction count as +1
	if openedby not in reacted_users:
		reacted_users.append(openedby)

	reaction_count = len(reacted_users)

	return {
		"data_field": data_field,
		"number": number,
		"entry": {
			"id": db_id,
			"number": number,
			"title": title,
			"opened_by": openedby,
			"creation_date": creationdate,
			"labels": labels,
			"mod_name": modname,
			"reactions": reactions,
			"reaction_count": reaction_count,
			"total_comment_count": total_comment_count,
			"user_comment_count": user_comment_count,
		},
	}


def main(mainpath):
	fprefix = " [Process Feature Requests] "
	print("\n" + fprefix + "Starting.\n")

	rootpath = "." + sep + "issue-tracker"
	if os.environ["IS_PRODUCTION"] == "false":
		rootpath = mainpath + sep + "issue-tracker"

	token = os.environ["GH_SERILUM_DATA_WORKFLOW_API"]

	# Fetch everything in a few paginated GraphQL calls
	print(fprefix + "Fetching issues via GraphQL...")
	all_issues = fetch_all_issues(token)
	print(fprefix + "Fetched " + str(len(all_issues)) + " total closed feature requests.")

	output = {"data": {"mod-feature": {}, "standalone-feature": {}}}
	issues_sorted_reaction_count = {}

	for issue in all_issues:
		result = process_issue(issue)
		if result is None:
			continue

		number = result["number"]
		print(fprefix + "Processing issue #" + str(number))

		output["data"][result["data_field"]][number] = result["entry"]
		issues_sorted_reaction_count[number] = result["entry"]["reaction_count"]

	# Sort by reaction count descending
	output["issues_sorted_reaction_count"] = list(
		reversed(sorted(issues_sorted_reaction_count.items(), key=lambda x: x[1]))
	)

	last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
	print(fprefix + "Last updated output:", last_updated)
	output["last_updated"] = last_updated

	json_output_path = rootpath + sep + "data" + sep + "feature-request-data.json"
	print(fprefix + "Writing output to: " + json_output_path)

	with open(json_output_path, "w") as f:
		f.write(json.dumps(output, indent=2))

	with open(json_output_path.replace(".json", ".min.json"), "w") as f:
		f.write(json.dumps(output))

	print("\n" + fprefix + "Finished.")


if __name__ == "__main__":
	main("")
