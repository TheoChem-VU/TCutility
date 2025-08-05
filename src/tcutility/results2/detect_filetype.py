from scm import plams
import os


def _is_unicode_file(path: str) -> bool:
	# try to open the file first
	try:
		with open(path) as file:
			file.readlines()
	except UnicodeDecodeError:
		return False
	return True


def _is_float(s: str) -> bool:
	try:
		float(s)
		return True
	except ValueError:
		return False


def _detect_coord_path(path: str) -> str:
	'''
	Detect if a file is a coord file.
	'''
	if not _is_unicode_file(path):
		return

	with open(path) as file:
		lines = file.readlines()

	lines = [line.strip() for line in lines if line.strip()]

	# first line must be $coord
	# and final line must be $end
	if lines[0] != '$coord':
		return

	if lines[-1] != '$end':
		return

	# check next n_atoms lines except second line which is for comments
	body = lines[1:-2]

	# check if the body matches xyz
	for line in body:
		if line.startswith('$'):
			continue
		parts = line.split()
		if not parts[3].isalpha():
			return
		if not all(_is_float(part) for part in parts[:3]):
			return

	return 'coord'


def _detect_xyz_path(path: str) -> str:
	'''
	Detect if a file is an xyz file.
	'''
	if not _is_unicode_file(path):
		return

	with open(path) as file:
		lines = file.readlines()

	# first line must be an integer
	first_line = lines[0].strip()
	if not first_line.isnumeric():
		return
	n_atoms = int(first_line)

	# check next n_atoms lines except second line which is for comments
	body = lines[2:n_atoms+2]
	# check if the body matches xyz
	for line in body:
		parts = line.split()
		# first part is element
		if len(parts[0]) > 2:
			return
		if not parts[0].isalpha():
			return

		# next three parts are floats
		if not all(_is_float(part) for part in parts[1:4]):
			return

	return 'xyz'


def _detect_AMS_path(path: str) -> str:
	'''
	Detect if the file originates from an AMS calculation.
	'''
	# check if file is an rkf file
	try:
		reader = plams.KFReader(path, autodetect=False)
		if ('General', 'program') in reader:
			program = reader.read('General', 'program').lower()
			return f'{program}_rkf'
		if ('General', 'file-ident') in reader:
			ident = reader.read('General', 'file-ident').lower()
			if ident == 'tape21':
				return 't21'

	except (plams.core.errors.FileError, IndexError):
		pass

	except OSError:
		return

	if not _is_unicode_file(path):
		return

	# check text files
	with open(path) as file:
		lines = file.readlines()
		# check for output file
		if any('Amsterdam Modeling Suite' in line for line in lines):
			if any('ADF 20' in line for line in lines):
				return 'adf_out'

		# and check for logfile
		if any('ADF 20' in line and 'RunTime: ' in line for line in lines):
			return 'adf_log'


def _detect_CREST_path(path: str) -> str:
	'''
	Detect if the file originates from a CREST calculation.
	'''
	# check for conformer and rotamer directories
	if not _is_unicode_file(path):
		return

	# check text files
	with open(path) as file:
		lines = file.readlines()
		# check for output file
		if any('|  Conformer-Rotamer Ensemble Sampling Tool  |' in line for line in lines):
			return 'crest_out'


def detect(path: str) -> str:
	if os.path.isdir(path):
		return 'directory'

	for detect_func in [
						_detect_xyz_path,
						_detect_coord_path,
						_detect_AMS_path,
						_detect_CREST_path,
						]:
		typ = detect_func(path)
		if typ is not None:
			return typ


def detect_program(path: str) -> str:
	typ = detect(path)
	if typ.startswith('adf_') or typ == 't21':
		return 'adf'



if __name__ == '__main__':
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2019/TransitionState/DielsAlder.results/Diene.t21'))
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2022/DonorAcceptor/NH3BH3.results/ams.rkf'))
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2022/DonorAcceptor/NH3BH3.results/adf.rkf'))
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2022/DonorAcceptor/NH3BH3.NH3.out'))
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2019/TransitionState/DielsAlder.out'))
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2022/DonorAcceptor/NH3BH3.NH3.logfile'))
	print(detect('/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/calculations/PyOrb_testing_2019/TransitionState/DielsAlder.logfile'))


	base = '/Users/yumanhordijk/PhD/Programs/TheoCheM/PyFMO/examples/bonding_antibonding/homolytic'
	for root, dirs, files in os.walk(base):
		for file in files:
			p = os.path.join(root, file)
			print(str(detect(p)).ljust(10), './' + os.path.relpath(p, base))

	print()
	base = '/Users/yumanhordijk/PhD/Programs/TheoCheM/TCutility/examples/job/calculations/Pentane/CREST'
	for root, dirs, files in os.walk(base):
		for file in files:
			p = os.path.join(root, file)
			# print(p)
			print(str(detect(p)).ljust(10), './' + os.path.relpath(p, base))
