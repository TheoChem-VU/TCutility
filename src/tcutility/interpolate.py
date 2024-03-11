import numpy as np


class Estimator:
	'''
	Initialize the ``Estimator`` with data ``X`` and ``Y``. 
	The estimator will use this data to make its estimates. 

	Args:
		X: the independent variable used to predict the values. The positions of points to be estimated will be based on these.
			``X`` should be of shape ``(N, n)`` with ``N`` datapoints and ``n`` dimensions. If the shape is ``(N)`` we assume ``n = 1``.
		Y: the dependent reference data used to calculate the new estimated values. Should be of shape ``(N)``.
	'''
	def __init__(self, X: np.ndarray, Y: np.ndarray):
		# make sure the input is at least 2D
		X = np.array(X)
		Y = np.array(Y)
		if len(X.shape) == 1:
			X = np.atleast_2d(X).T

		# we should sort the data by the x-values
		if X.shape[1] == 1:
			sorted_idx = np.argsort(X, axis=0).squeeze()
			X = X[sorted_idx, :]
			Y = Y[sorted_idx]

		# remove duplicated values for X values
		unique_idx = np.unique(X, return_index=True, axis=0)[1]

		X = X[unique_idx]
		Y = Y[unique_idx]

		self.X = X
		self.Y = Y

	def __call__(self, x: np.ndarray) -> np.ndarray:
		return self.predict(x)

	def predict(self, x: np.ndarray) -> np.ndarray:
		'''
		Make a prediction for values ``x`` based on the data used to initialize this class.
		This method should be overwritten for subclasses of ``Estimator``.

		.. note::
			The ``Estimator.__call__`` method redirects to this function.
		'''
		raise NotImplementedError()

	@property
	def ndim(self) -> int:
		return self.X.shape[1]


class Linear(Estimator):
	'''
	A linear estimator class for estimating 1D functions.
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.ndim != 1:
			raise Exception(f'{self.__class__.__qualname__} can only handle 1D data, not {self.ndim}D.')

	def predict(self, x: np.ndarray) -> np.ndarray:
		'''
		Make a prediction for values ``x`` based on the data used to initialize this class.
		
		For a linear interpolation we first obtain the x-values (:math:`(x_a, y_a) | x_a <= x` and :math:`(x_b, y_b) | x < x_b)`
		that encapsulate the requested x-values as well as the corresponding y-values.

		We first select the independent variables 
		
		We have that :math:`x_a <= x < x_b`. We then calculate the progress factor :math:`f = \\frac{x - x_a}{x_b - x_a}`. 
		Now we estimate the values as :math:`y = y_a + f(y_b - y_a)`.

		.. note::
			The ``Estimator.__call__`` method redirects to this function.
		'''

		# get the difference between the input and reference independent variables
		# a n x N matrix with N values to be estimated and n values in the reference
		diff = self.X.T - x

		# get the closest index to grab from the reference data
		# the closest one should be the value where the diff matrix becomes positive
		# we get this index by counting the number of diff elements larger than zero
		closest_idx = len(self.X) - np.count_nonzero(diff >= 0, axis=1) - 1
		# for extrapolation we have to clip the indices to fit within the reference
		# the lowest index should be 0 and the highest len - 2, as we have to have two references
		closest_idx = np.clip(closest_idx, 0, len(self.X) - 2)
		# do the interpolation here
		xa, xb = self.X[closest_idx], self.X[closest_idx + 1]
		ya, yb = self.Y[closest_idx], self.Y[closest_idx + 1]
		f = ((x - xa) / (xb - xa)).squeeze()
		y = ya + (yb - ya) * f
		# squeeze the result in case we inputted a single float instead of an array
		return y.squeeze()


class BiLinear(Estimator):
	'''
	A bi-linear estimator class for estimating 2D functions.
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.ndim != 2:
			raise Exception(f'{self.__class__.__qualname__} can only handle 2D data, not {self.ndim}D.')

	def predict(self, x: np.ndarray) -> np.ndarray:
		'''
		Make a prediction for values ``x`` based on the data used to initialize this class.
		
		For a linear interpolation we first obtain the x-values (:math:`(x_a, y_a) | x_a <= x` and :math:`(x_b, y_b) | x < x_b)`
		that encapsulate the requested x-values as well as the corresponding y-values.

		We first select the independent variables 
		
		We have that :math:`x_a <= x < x_b`. We then calculate the progress factor :math:`f = \\frac{x - x_a}{x_b - x_a}`. 
		Now we estimate the values as :math:`y = y_a + f(y_b - y_a)`.

		.. note::
			The ``Estimator.__call__`` method redirects to this function.
		'''
		x = np.atleast_2d(x)
		# get the difference between the input and reference independent variables
		# a n x N matrix with N values to be estimated and n values in the reference
		diff = self.X.T - x

		# get the closest index to grab from the reference data
		# the closest one should be the value where the diff matrix becomes positive
		# we get this index by counting the number of diff elements larger than zero
		closest_idx = len(self.X) - np.count_nonzero(diff >= 0, axis=1) - 1
		# for extrapolation we have to clip the indices to fit within the reference
		# the lowest index should be 0 and the highest len - 2, as we have to have two references
		closest_idx = np.clip(closest_idx, 0, len(self.X) - 2)
		# do the interpolation here
		xa, xb = self.X[closest_idx], self.X[closest_idx + 1]
		ya, yb = self.Y[closest_idx], self.Y[closest_idx + 1]
		f = ((x - xa) / (xb - xa)).squeeze()
		y = ya + (yb - ya) * f
		# squeeze the result in case we inputted a single float instead of an array
		return y.squeeze()


if __name__ == '__main__':
	import matplotlib.pyplot as plt

	# lerp = Linear([0, 1, 2, 3], [0, 1, 0, 1])
	# print(lerp.ndim)

	# x = np.linspace(-1, 4, 100)
	# # print(lerp(0))
	# plt.scatter(x, lerp(x))
	# plt.plot([0, 1, 2, 3], [0, 1, 0, 1])
	# plt.show()

	lerp = BiLinear([[0, 0], [0, 1], [1, 1], [1, 0]], [0, 1, 0, 1])
	lerp([0, 0])
