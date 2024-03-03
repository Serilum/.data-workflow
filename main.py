# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "badges"))
import generate_badges
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "issue-tracker"))
import process_feature_requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "membership"))
import update_membership_data

def main():
    fprefix = " [Main] "
    print("\n" + fprefix + "Starting the Python automated workflow.")

    rootpath = os.path.dirname(sys.argv[0])

    # Process GitHub Sponsors and Patreon members:
    update_membership_data.main(rootpath)

    # Generate project description badges:
    generate_badges.main(rootpath)

    if os.environ['IS_PRODUCTION'] == "true":
        # Process the requests from the .issue-tracker repo on GitHub:
        process_feature_requests.main(rootpath)

    return

if __name__ == "__main__":
    main()