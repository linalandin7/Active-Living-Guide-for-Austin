"""One command runs every test:  python3 tests/run_all.py   (needs: pip install -r requirements-dev.txt)"""
import pathlib
import sys
import unittest

here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
suite = unittest.defaultTestLoader.discover(str(here), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
