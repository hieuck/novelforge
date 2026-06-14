import sys, pathlib
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent / 'apps' / 'engine'
sys.path.insert(0, str(ENGINE_DIR))
