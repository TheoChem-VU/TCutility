from TCutility import ensure_list


def molecule(molstring: str, mode: str = 'html') -> str:
	'''
	Parse and return a string containing a molecular formula that will show up properly in LaTeX or HTML.

	Args:
		molstring: the string that contains the molecular formula to be parsed. It can be either single molecule or a reaction. Molecules should be separated by '+' or '->'.
		mode: the formatter to convert the string to. Should be 'html' or 'latex'.

	Returns:
		A string that is formatted to be rendered nicely in either HTML or LaTeX.
	'''
	if mode == 'latex':
		ret = molstring
		for num in '0123456789':
			ret = ret.replace(num, f'_{num}')
		for sign in '+-':
			ret = ret.replace(sign, f'^{sign}')
		return ret

	if mode == 'html':
		ret = molstring
		# to take care of plus-signs used to denote reactions we have to first split 
		# the molstring into its parts.
		for part in ret.split():
			# if part is only a plus-sign we skip this part. This is only true when the plus-sign
			# is used to denote a reaction
			if part in ['+', '->']:
				continue

			# parse the part
			partret = part
			# numbers should be subscript
			for num in '0123456789':
				partret = partret.replace(num, f'<sub>{num}</sub>')

			# signs should be superscript
			for sign in '+-':
				# negative charges should be denoted by em dash and not a normal dash
				partret = partret.replace(sign, f'<sup>{sign.replace("-", "—")}</sup>')

			# replace the part in the original string
			ret = ret.replace(part, partret)
		return ret


if __name__ == '__main__':
	print(molecule('F- + CH3Cl', 'html'))
