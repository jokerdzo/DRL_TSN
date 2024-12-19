# 用于计算最大时隙（max_slot）的函数，求最大公约数
def gcd(numbers):
    if len(numbers) == 1:
        return numbers[0]
    else:
        a = numbers[0]
        b = gcd(numbers[1:])
        while b!= 0:
            a, b = b, a % b
        return a
