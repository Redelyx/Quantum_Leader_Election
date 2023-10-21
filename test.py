def greatest_power_of_2(n):
    if n < 1:
        return None  # Error: n should be a positive integer
    power = 1
    while n >= 2:
        n //= 2
        power *= 2
    return power

# Example usage:
n = 21
result = greatest_power_of_2(n)
print(f"The greatest power of 2 smaller than {n} is {result}")