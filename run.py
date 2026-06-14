# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
import FetchApiData
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "badges"))
import GenerateBadges
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "issue-tracker"))
import ProcessFeatureRequests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "membership"))
import UpdateMembershipData
import GenerateMemberBadges
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "versions"))
import UpdateLatestModVersions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "web"))
import UpdateModLogos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mods"))
import UpdateModData
import UpdateModDescriptions

def main():
    fprefix = " [Main] "
    print("\n" + fprefix + "Starting the Python automated workflow.")

    rootPath = os.path.dirname(sys.argv[0])

    # Fetch all API data first:
    FetchApiData.main(rootPath)

    # Process GitHub Sponsors and Patreon members:
    UpdateMembershipData.main(rootPath)

    # Generate the per-member supporter badges:
    GenerateMemberBadges.main(rootPath)

    # Generate project description badges:
    GenerateBadges.main(rootPath)

    # Update latest mod versions
    UpdateLatestModVersions.main(rootPath)

    # Save the mod logos
    UpdateModLogos.main(rootPath)

    # Generate the website mod data
    UpdateModData.main(rootPath)

    # Save the full mod descriptions
    UpdateModDescriptions.main(rootPath)

    if os.environ['IS_PRODUCTION'] == "true":
        # Process the requests from the .issue-tracker repo on GitHub:
        ProcessFeatureRequests.main(rootPath)

    return

if __name__ == "__main__":
    main()
