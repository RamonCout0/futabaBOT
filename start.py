#!/usr/bin/env python3
"""
start.py  ·  Ponto de entrada compatível com ShardCloud
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import asyncio, os, sys, logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, os.path.dirname(__file__))

from futaba import main
asyncio.run(main())
