from Crypto.Util import number
from ecpy.curves import Point


def sample_from_field(p):
    return number.getRandomRange(1, p-1)


def sample_from_field_arr(amount: int, p):
    lst = [None]
    for i in range(amount):
        lst.append(sample_from_field(p))

    return lst


def concatenate_points(points):
    res_string = ""
    for point in points:
        if (type(point) == int):
            res_string += str(point)
        elif (type(point) == Point):
            res_string += f"{point.x}{point.y}"
        else:
            res_string += str(point)

    return res_string


def bit_to_int(bitlist):
    output = 0
    for bit in bitlist:
        output = (output << 1) | bit
    return output
