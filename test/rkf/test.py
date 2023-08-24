from yutility import log
import os
from TCutility.rkf import info as rkf_info
from TCutility.rkf import adf as rkf_adf
from TCutility.rkf import cache
from pprint import pprint
from yviewer import viewer
import matplotlib.pyplot as plt


for calc_dir in os.listdir():
    if calc_dir == '.DS_Store':
        continue
    if not os.path.isdir(calc_dir):
        continue

    info = rkf_info.get_calc_info(calc_dir)
    # if 'history' in info.molecule:
    # viewer.show([info.molecule.input, info.molecule.output])
    # pprint(info)
    # if info.history:
    #     plt.plot(range(info.history.number_of_entries), info.history.energy)
    #     plt.show()
    try:
        calc_sett = rkf_adf.get_calc_settings(info)
        log.log(calc_sett.symmetry.labels)
    except:
        pass
    # if info.status.success:
    #     log.log('The job succeeded')
    # else:
    #     log.log(f'The job did not succeed')
    # log.log(info)
    log.log()
