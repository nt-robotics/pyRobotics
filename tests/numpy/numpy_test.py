
import numpy as np

a = np.arange(32).reshape(2, 4, -1)

print(a)

print("")
print("")
print("")

print(a[:, ..., 1:3])


