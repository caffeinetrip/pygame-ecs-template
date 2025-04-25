def smooth_approach(current, target, slowness=10, min_speed=0.1):
    if current == target:
        return current

    diff = target - current
    movement = diff / slowness

    if abs(movement) < min_speed and diff != 0:
        movement = min_speed if diff > 0 else -min_speed

    if abs(movement) > abs(diff):
        return target

    return current + movement