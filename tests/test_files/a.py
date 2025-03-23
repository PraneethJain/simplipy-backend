def f(x, y):
    global z
    z = x * y + 10
    return z + 3


i = 0
while i < 10:
    y = f(i, i**2)
    z = 10 + y
    i = i + 1
    if i == 5:
        i = i + 2
        continue
    else:
        pass

    if not i:
        break
    else:
        i = i + 1
    continue
