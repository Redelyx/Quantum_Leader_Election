def greatest_power_of_two(n):
    if n < 1:
        return None  # Error: n should be a positive integer
    power = 1
    while n >= 2:
        n //= 2
        power *= 2
    return power

def is_power_of_two(n):
    return (n & (n-1) == 0) and n != 0