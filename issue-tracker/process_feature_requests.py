# -*- coding: utf-8 -*-
#!/usr/bin/env python
from github						import Auth, Github
from datetime					import datetime
import json
import os
import sys

sep = os.path.sep

def main(mainpath):
	fprefix = " [Process Feature Requests] "

	print("\n" + fprefix + "Starting.\n")

	output = { "data" : { "mod-feature" : {}, "standalone-feature" : {}}}
	issues_sorted_reaction_count = {}

	# rootpath = mainpath + sep + "issue-tracker" # For dev
	rootpath = "." + sep + "issue-tracker" # For production

	gh_serilum = Github(auth=Auth.Token(os.environ["GH_SERILUM_DATA_WORKFLOW_API"]))
	serilum_org = gh_serilum.get_organization("Serilum")

	issue_tracker_repo = serilum_org.get_repo(".issue-tracker")
	
	feature_requests = issue_tracker_repo.get_issues(state="closed", labels=["Feature Request"])
	for fr in feature_requests:
		if fr.state_reason != "not_planned": # Means, not implemented.
			continue

		# General Information
		id = int(fr.id)
		number = int(fr.number)
		title = fr.title
		openedby = fr.user.login
		creationdate = str(fr.created_at).split(" ")[0]
		# url = fr.html_url

		print(fprefix + "Processing issue #" + str(number))

		# Labels
		labels = []

		raw_labels = fr.get_labels()
		for raw_label in raw_labels:
			label = raw_label.name
			if not label in labels:
				labels.append(label)



		# Determine if issue is a mod or standalone feature
		data_field = "mod-feature"
		if len(labels) == 1:
			data_field = "standalone-feature"


		# Reactions
		reacted_users = []
		reactions = {}

		raw_reactions = fr.get_reactions()
		if raw_reactions.totalCount > 0:
			for raw_reaction in raw_reactions:
				rc = raw_reaction.content

				if not rc in reactions:
					reactions[rc] = 1
				else:
					reactions[rc] += 1

				if rc != "-1" and rc != "confused":
					username = raw_reaction.user.login

					if not username in reacted_users:
						reacted_users.append(username)

		if not openedby in reacted_users: # Add issue creator to reaction count as +1
			reacted_users.append(openedby)

		reaction_count = len(reacted_users)

		# Issue Comments
		commented_users = []

		total_comment_count = 0
		user_comment_count = 0
		for raw_comment in fr.get_comments():
			total_comment_count += 1

			issue_comment_user = raw_comment.user.login
			if issue_comment_user == "ricksouth":
				continue

			if not issue_comment_user in commented_users:
				commented_users.append(issue_comment_user)
				user_comment_count += 1

		if not openedby in commented_users: # Add issue creator post to comment count as +1
			commented_users.append(openedby)
			total_comment_count += 1
			user_comment_count += 1


		# Information Overview
		# print("ID:", id)
		# print("Number:", number)
		# print("Title:", title)
		# print("Opened by:", openedby)
		# print("Creation date:", creationdate)
		# print("URL:", url)
		# print("Labels:", labels)
		# print("Reaction count:", reaction_count)
		# print("Reactions:", reactions)
		# print("Total comment count:", total_comment_count)
		# print("User comment count:", user_comment_count)


		# Add to issues_sorted_reaction_count dictionary
		issues_sorted_reaction_count[number] = reaction_count


		# Creating data entry in output
		data = { "id" : id,
				 "number" : number,
				 "title" : title,
				 "opened_by" : openedby,
				 "creation_date" : creationdate,
				 "labels" : labels,
				 "reactions" : reactions,
				 "reaction_count" : reaction_count,
				 "total_comment_count" : total_comment_count,
				 "user_comment_count" : user_comment_count
			   }

		output["data"][data_field][number] = data


	# Sort issues_sorted_reaction_count
	output["issues_sorted_reaction_count"] = list(reversed(sorted(issues_sorted_reaction_count.items(), key=lambda x:x[1])))


	# Add last_updated to output
	last_updated = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

	print(fprefix + "Last updated output:", last_updated)
	output["last_updated"] = last_updated


	# Write output to file
	json_output_path = rootpath + sep + "data" + sep + "feature-request-data.json"

	print(fprefix + "Writing output to: " + json_output_path)
	with open(json_output_path, "w") as datafile:
		datafile.write(json.dumps(output))

	print("\n" + fprefix + "Finished.")
	return


if __name__ == "__main__":
	main()