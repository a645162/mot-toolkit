def liner_interpolate_position(
        start_pos: float,
        end_pos: float,
        index: int,
        total_count: int,
):
    value = start_pos + (end_pos - start_pos) * index / (total_count - 1)

    # Round to 2 decimal places
    value = round(value, 2)

    return value
