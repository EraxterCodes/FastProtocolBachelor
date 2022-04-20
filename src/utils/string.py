from ecpy.curves import Point


def utf8len(s):
    return len(s.encode('utf-8'))


def str_to_point(s, curve):
    temp_x, temp_y = s.split(",")

    x = int(temp_x[1:-1], base=16)
    y = int(temp_y[1:-1], base=16)

    return Point(x, y, curve)


def str_to_point2(s, curve):
    temp_x, temp_y = s.split(",")
    temp_x = temp_x.strip()
    temp_y = temp_y.strip()

    x = int(temp_x.strip("'"), base=16)
    y = int(temp_y.strip("'"), base=16)

    return Point(x, y, curve)


def unpack_commitment_and_x(self, array):
    for j in range(len(array)):
        temparray = array[j]

        index, temparray = temparray.split("-")

        temparray = temparray.split(";")
        temparray = temparray[:-1]
        afterstrip = []
        # if(self.id == str(1)):
        #     print(array)
        for x in temparray:
            afterstrip.append(x.strip("()'").replace(
                '(', '').replace(')', '')[1:])

        afterstripsquared = []
        for x in afterstrip:
            afterstripsquared.append(x.split("|"))
        # print(afterstripsquared[0][1])

        for i in range(len(afterstripsquared)):
            # print(i)
            # print(afterstripsquared[i][0])
            # print("checking ext_commitments[j] after this")
            self.commitments[int(index)].append(str_to_point2(
                afterstripsquared[i][0].strip("'"), self.pd.cp))  # [R][0=commitment | 1=BigX]
            # print(str_to_point2(afterstripsquared[i][0]))
            self.big_xs[int(index)].append(str_to_point2(
                afterstripsquared[i][1], self.pd.cp))  # [R][0=commitment | 1=BigX]
