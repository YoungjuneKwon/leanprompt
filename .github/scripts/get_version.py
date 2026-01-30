#!/usr/bin/env python3
import re
import sys

with open("setup.py", "r") as f:
    content = f.read()

match = re.search(r'version=[\'"]([^\'"]+)[\'"]', content)
if match:
    version = match.group(1)
    print(f"VERSION={version}")
    print(f"Version found: {version}")
    sys.exit(0)
else:
    print("Version not found in setup.py", file=sys.stderr)
    sys.exit(1)
