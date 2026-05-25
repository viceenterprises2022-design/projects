---
source: 4_Operators - Logical Operators.pdfPDF.pdf
type: pdf
---

Operators
Logical Operators
Use logical operators to check multiple conditions at once or to choose between conditions.
# And Operator
and_expression = x and y
# Or Operator
or_expression = x or y
# Not Operator
not_expression = not x
And Operator
The and operator returns True only if both conditions are True.
x = 10
print(x > 5 and x < 15)   # True
print(x > 5 and x < 8)    # False
Or Operator
The or operator returns True if at least one condition is True.
x = 3
print(x > 5 or x < 10)   # True
print(x > 5 or x == 2)   # False
Not Operator
The not operator reverses the Boolean value.
print(not True)   # False
print(not False)  # True
is_logged_in = True
print(not is_logged_in)   # False
Using logical operators in if statements:
age = 18
if age >= 18 and age <= 60:
print("Eligible to work")
marks = 45
if marks < 40 or marks == 40:
print("Needs improvement")
Combining multiple conditions:
x = 5
y = 10
z = 15
if x < y and (y < z or x == 5):
print("Condition is True")
Order of operations:
Python evaluates logical operators in this order:
1.  not
2.  and
3.  or
You can use parentheses to control the order:
result = not (True and False)   # True