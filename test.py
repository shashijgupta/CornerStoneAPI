def calculate(S):
    length = len(S)

    # Return 0 if the string length exceeds 100
    if length > 100:
        return 0

    # Array to track presence of two-digit numbers
    count = [0] * 100

    # Extract two-digit numbers from the string
    for i in range(length - 1):
        num = int(S[i : i + 2])  # Take two consecutive characters as a number
        print(num)
        count[num] = 1  # Mark the number as present

    # Sum up the count array to get the number of unique two-digit numbers
    return sum(count)


# Example usage
S = "0010203040506070809112131415161718192232425262728293343536373839445464748495565758596676869778798890"
result = calculate(S)
print("Number of unique two-digit numbers:", result)
