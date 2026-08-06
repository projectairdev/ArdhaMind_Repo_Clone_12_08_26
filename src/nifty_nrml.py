#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nifty_tomorrow import main

if __name__ == "__main__":
    main()
