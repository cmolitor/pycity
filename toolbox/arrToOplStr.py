__author__ = 'cmo'

def array2string(array):
    """
    Convert an array to a string in a specific format needed by OPLRUN;
    :param array: array to convert
    :return: string "[array[1] array[2] ....]
    """
    _string = "[" + format(array[0])
    for x in range(1, len(array)):
        _string += " " + format(array[x])
    _string += "]"
    return _string