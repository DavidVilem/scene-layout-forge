import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_example import main
if __name__=='__main__':main('bunker-spine')
