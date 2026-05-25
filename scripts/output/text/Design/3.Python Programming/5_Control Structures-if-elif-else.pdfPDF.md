---
source: 5_Control Structures-if-elif-else.pdfPDF.pdf
type: pdf
---

Control Structures
If/If Else Statments
We can tell the computer how to make decisions using if/else statements. Make sure
that all the code inside your if/else statement is indented one level!
If Statments
Use an if statement to instruct the computer to do something only when a condition is
true. If the condition is false, the command indented underneath will be skipped.
if BOOLEAN_EXPRESSION:
print("This executes if BOOLEAN_EXPRESSION evaluates to True")
# Example:
# The text will only print if the user enters a negative number
number = int(input("Enter a number: "))
if number < 0:
print(str(number) + " is negative!")
If/Else Statements
Use an if/else statement to force the computer to make a decision between multiple
conditions. If the first condition is false, the computer will skip to the next condition
until it finds one that is true. If no conditions are true, the commands inside the else
block will be performed.
if condition_1:
print("This executes if condition_1 evaluates to True")
elif condition_2:
print("This executes if condition_2 evaluates to True")
else:
print("This executes if no prior conditions evaluate to True")
# Example:
# This program will print that the color is secondary
color == "purple"
if color == "red" or color == "blue" or color == "yellow":
print("Primary color.")
elif color == "green" or color == "orange" or color == "purple":
print("Secondary color.")
else:
print("Not a primary or secondary color.")