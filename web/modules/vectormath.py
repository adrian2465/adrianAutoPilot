
def moving_average_vector(average_vector, val_vector, window_size):
    rc_vector = [0, 0, 0]
    for i in range(0, 3):
        rc_vector[i] = (val_vector[i] + average_vector[i] * (window_size - 1)) / window_size
    return rc_vector


def moving_average_scalar(average, val, window_size):
    return (val + average * (window_size - 1)) / window_size


def subtr(x, y):
    return x - y


def mult(x, y):
    return x * y


def vector_from_data(data, offset, conversion_factor, c_short_fn):
    return [c_short_fn(data[0 + offset], data[1 + offset]) * conversion_factor,
            c_short_fn(data[2 + offset], data[3 + offset]) * conversion_factor,
            c_short_fn(data[4 + offset], data[5 + offset]) * conversion_factor]

# vop = vector operation. fun defines the operation.
def v_op(fun, vector1, vector2):
    if len(vector1) != len(vector2):
        raise Exception(f"{vector1} and {vector2} are not the same length")
    result_vector = [0] * len(vector1)
    for i, d in enumerate(vector1):
        result_vector[i] = fun(d, vector2[i])
    return result_vector

