from yutility import log
import os
from TCutility.rkf import info as rkf_info
from TCutility.rkf import adf as rkf_adf


for calc_dir in os.listdir():
    if calc_dir == '.DS_Store':
        continue
    if not os.path.isdir(calc_dir):
        continue

    info = rkf_info.get_calc_info(calc_dir)
    log.log(info)
    try:
        log.log(rkf_adf.get_calc_settings(info))
    except:
        pass
    # if info.status.success:
    #     log.log('The job succeeded')
    # else:
    #     log.log(f'The job did not succeed')
    # log.log(info)
    log.log()
