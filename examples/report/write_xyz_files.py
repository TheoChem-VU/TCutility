from tcutility.report import SI
from tcutility._report.formatters import xyz


if __name__ == '__main__':
    with SI('test') as si:
        si.add_xyz('/Users/yumanhordijk/PhD/Projects/RadicalAdditionBenchmark/data/abinitio_opt/RC_C2H2_NH2/PREOPT', 'RC_C2H2')

    # print(xyz.Default().write('/Users/yumanhordijk/PhD/Projects/RadicalAdditionBenchmark/data/abinitio_opt/RC_C2H2_NH2/PREOPT'))
