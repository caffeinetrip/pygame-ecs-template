import pygame

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

def clip(surf, rect):
    if type(rect) == tuple:
        rect = pygame.Rect(*rect)
    surf.set_clip(rect)
    image = surf.subsurface(surf.get_clip()).copy()
    surf.set_clip(None)
    return image

def blit_center_rot(dest, src, pos, rot=0):
    img = pygame.transform.rotate(src, rot)
    dest.blit(img, (pos[0] - img.get_width() // 2, pos[1] - img.get_height() // 2))

def palette_swap(surf, colors):
    colorkey = surf.get_colorkey()
    surf = surf.copy()
    for from_color, to_color in colors.items():
        surf.set_colorkey(from_color)
        if len(to_color) <= 3:
            dest = pygame.Surface(surf.get_size())
        else:
            dest = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        dest.fill(to_color)
        dest.blit(surf, (0, 0))
        surf = dest
    surf.set_colorkey(colorkey)
    return surf