---
source: 3_Operators - Comparison Operators.pdfPDF.pdf
type: pdf
---

Operators
Comparison Operators
Use comparison operators to compare values in order to make decisions in your code.
Comparison operators return Boolean values (True or False).
x == y      # is x equal to y
x != y      # is x not equal to y
x > y       # is x greater than y
x >= y      # is x greater than or equal to y
x < y       # is x less than y
x <= y      # is x less than or equal to y
Example:
x = 10
y = 5
print(x > y)    # True
print(x == y)   # False
print(x != y)   # True
Using comparison operators in if
statements:
x = 7
if x == 7:
print("x is equal to 7")
if x > 5:
print("x is greater than 5")
Example with user input:
num = int(input("Enter a number: "))
if num >= 10:
print("Number is 10 or more")
else:
print("Number is less than 10")
Example with multiple conditions:
a = 3
b = 8
if a < b:
print("a is smaller than b")
elif a == b:
print("a and b are equal")
else:
print("a is greater than b")