from yutility import log
import os
from TCutility.rkf import info as rkf_info

for calc_dir in os.listdir():
    if calc_dir == '.DS_Store':
        continue
    if not os.path.isdir(calc_dir):
        continue

    log.log(rkf_info.get_calc_info(calc_dir))
    log.log()
