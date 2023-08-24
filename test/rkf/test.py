from yutility import log
import os
from TCutility import rkf
from pprint import pprint
from yviewer import viewer
import matplotlib.pyplot as plt


for calc_dir in os.listdir():
    if calc_dir == '.DS_Store':
        continue
    if not os.path.isdir(calc_dir):
        continue

    try: 
        info = rkf.read(calc_dir)
        pprint(info)
    except AssertionError:
        pass

    log.log()
