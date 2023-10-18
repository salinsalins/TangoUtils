import numpy


def smooth(self, array, n):
    m = int(len(array) / n)
    k = int(len(array) % n)
    if m > 0:
        sa = array[:m * n].reshape(m, n).mean(axis=1)
        if k > 0:
            sb = numpy.zeros(m + 1)
            sb[:-1] = sa
            sb[-1] = sa[-k:].mean()
            return sb
    else:
        sa = array.mean()
    return sa
