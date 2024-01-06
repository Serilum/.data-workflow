# -*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "issue-tracker"))
import process_feature_requests

def main():
    fprefix = " [Main] "
    print("\n" + fprefix + "Starting the Python automated workflow.")

    rootpath = os.path.dirname(sys.argv[0])

    process_feature_requests.main(rootpath)

    return

if __name__ == "__main__":
    main()