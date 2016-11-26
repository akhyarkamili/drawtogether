import shapes

def isNear(p1, p2):
    # check if two points are near each other
    # uses pythagorean theorem
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    if dx**2 + dy**2 < 8:
        return True
    return False

def adjust(end_pos, start_pos):
    if end_pos[1] < start_pos[1]:
        if end_pos[0] < start_pos[0]:
            start_pos, end_pos = end_pos, start_pos
        else:
            temp = end_pos
            end_pos = end_pos[0], start_pos[1]
            start_pos = start_pos[0], temp[1]
    else:
        if end_pos[0] < start_pos[0]:
            temp = end_pos
            end_pos = start_pos[0], end_pos[1]
            start_pos = temp[0], start_pos[1]
    return end_pos, start_pos

def listPush(l, obj):
    l = [obj] + l