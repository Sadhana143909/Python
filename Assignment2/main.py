
def redesigned(n):
    if n <= 1:
        return 1

    a = 1
    b = 1

    for i in range(2, n + 1):
        c = a + b
        a = b
        b = c

    return b


for n in [10, 20, 25, 30, 1000]:
    print("Steps:", n)

    if n <= 30:
        print("Original:", original(n))

    print("Redesigned:", redesigned(n))
    print()
