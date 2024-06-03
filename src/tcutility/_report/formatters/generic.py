from tcutility import results

class DefaultFormatter:
	def __call__(self, *results: results.Result | str) -> str:
		return self.write(*results)

	def write(self, *results: results.Result | str) -> str:
		data = self._get_data(*results)
		return self._format(data)

	def _get_data(self, *results: results.Result | str):
		NotImplemented

	def _format(self, data: results.Result) -> str:
		NotImplemented
