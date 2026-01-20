"""
Methods for handling the form of transitions
"""

import math


def try_to_convert_into_straight_line(coords) -> list:
    number_of_points = len(coords) / 2
    if number_of_points == 2:
        return coords
    vector_list = _calculate_vectors_from_line_point_to_next_line_point(coords)
    cos_phi_list = _calculate_cos_phi_values_between_vectors(vector_list)
    eliminate_points = True
    for cos_phi in cos_phi_list:
        if cos_phi < 0.97:
            eliminate_points = False
    if eliminate_points:
        return [coords[0], coords[1], coords[-2], coords[-1]]
    else:
        return coords


def _calculate_vectors_from_line_point_to_next_line_point(coords) -> list:
    vector_list = []
    for i in range(len(coords) // 2 - 1):
        vector_from_point_to_point = _sub_vectors(
            coords[i * 2 + 2], coords[i * 2 + 3], coords[i * 2 + 0], coords[i * 2 + 1]
        )
        if vector_from_point_to_point != [0, 0]:
            vector_list.append(vector_from_point_to_point)
    return vector_list


def _calculate_cos_phi_values_between_vectors(vector_list) -> list:
    cos_phi_list = []
    for i in range(len(vector_list) - 1):
        product_vector1_vector2 = _calculate_scalar_product(
            vector_list[i][0], vector_list[i][1], vector_list[i + 1][0], vector_list[i + 1][1]
        )
        amount_vector1 = math.sqrt(
            _calculate_scalar_product(vector_list[i][0], vector_list[i][1], vector_list[i][0], vector_list[i][1])
        )
        amount_vector2 = math.sqrt(
            _calculate_scalar_product(
                vector_list[i + 1][0], vector_list[i + 1][1], vector_list[i + 1][0], vector_list[i + 1][1]
            )
        )
        cos_phi = product_vector1_vector2 / (amount_vector1 * amount_vector2)
        cos_phi_list.append(cos_phi)
    return cos_phi_list


def _sub_vectors(x1, y1, x2, y2) -> list:
    return [x1 - x2, y1 - y2]


def _calculate_scalar_product(x1, y1, x2, y2):
    return x1 * x2 + y1 * y2
