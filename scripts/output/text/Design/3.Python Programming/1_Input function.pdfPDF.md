---
source: 1_Input function.pdfPDF.pdf
type: pdf
---

User Input
We can use input from the user to control how our program works.
# Ask the user for input and store it in a variable
name = input("What is your name? ")
The input() function always returns data as a string.
Example:
name = input("Enter your name: ")
print("Hello, " + name)
Taking numeric input:
If you want to use input as a number, convert it using int() or float().
num_one = int(input("Enter a number: "))
num_two = int(input("Enter another number: "))
num_three = float(input("Enter a decimal number: "))
Example:
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))
sum_nums = a + b
print("Sum is:", sum_nums)
Using input in conditions:
age = int(input("Enter your age: "))
if age >= 18:
print("You can vote")
else:
print("You cannot vote")
Example with strings:
color = input("Enter your favorite color: ")
if color == "blue":
print("Nice choice!")
else:
print("That's a good color too!")
Important Note:
num = input("Enter a number: ")
print(num + num)   # This joins strings, not addition
To perform addition, convert to int:
num = int(input("Enter a number: "))
print(num + num)   # This performs actual addition