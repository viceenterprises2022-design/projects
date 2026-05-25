

## 3.Python Programming/1_Input function.pdfPDF.md

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

## 3.Python Programming/2_Boolean Values.pdfPDF.md

---
source: 2_Boolean Values.pdfPDF.pdf
type: pdf
---

Boolean Values
Boolean values represent one of two possible states: True or False.
They are commonly used in decision-making and conditions in programs.
True
False
Boolean values are often the result of comparisons or conditions.
Example:
x = 10
y = 5
print(x > y)   # True
print(x == y)  # False
Using Boolean values in variables:
is_logged_in = True
has_permission = False
Using Boolean values in if statements:
is_raining = True
if is_raining:
print("Take an umbrella.")
Example:
is_even = False
if is_even:
print("The number is even.")
else:
print("The number is odd.")

## 3.Python Programming/3_Operators - Comparison Operators.pdfPDF.md

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

## 3.Python Programming/4_Operators - Logical Operators.pdfPDF.md

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

## 3.Python Programming/5_Control Structures-if-elif-else.pdfPDF.md

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

## Unit - 1 - Web Design/External CSS Notes.pdfPDF.md

---
source: External CSS Notes.pdfPDF.pdf
type: pdf
---

What is External CSS?
External CSS means writing your style rules in a separate file (with the .css extension) and
linking it to your HTML file using the <link> tag.
It helps to:
•  Keep HTML clean and readable
•  Reuse the same styles across multiple pages
•  Change the design of an entire website easily by editing one file
Structure of External CSS
External CSS is created in two parts:
1.  A CSS file — saved with .css extension (e.g., style.css)
2.  An HTML file — linked to the CSS file
Example
HTML File – index.html
<!DOCTYPE html>
<html>
<head>
<title>My Web Page</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>Welcome to My Website</h1>
<p>This page is styled using external CSS.</p>
</body>
</html>
CSS File – style.css
body {
background-color: #f9f9f9;
font-family: Arial, sans-serif;
text-align: center;
}
h1 {
color: darkblue;
}
p {
color: #333333;
font-size: 18px;
}
Linking CSS to HTML
The <link> tag connects the external stylesheet to the HTML page.
It must be placed inside the <head> section.
Syntax:
<link rel="stylesheet" href="style.css">
Explanation:
•
•
rel="stylesheet" — defines the relationship (it is a stylesheet).
href="style.css" — tells the browser where to find the CSS file.
o
If the CSS file is in a folder, write the path (e.g., href="css/style.css").
Syntax of CSS Rules
Same as internal CSS:
selector {
property: value;
}
Example:
h1 {
color: red;
text-align: center;
}
Advantages of External CSS
1.  Reusable — one CSS file can style many pages.
2.  Efficient — easier to maintain and update; change one file to affect the whole site.
3.  Clean HTML — keeps content separate from design.
4.  Faster loading — once the CSS file is downloaded, browsers cache it.
5.  Consistent design — ensures uniform style across all pages.
Disadvantages of External CSS
1.  Dependent on file link — if the CSS file path is wrong or missing, the page will
appear unstyled.
2.  Needs an extra HTTP request — browser must load one more file (minor delay on
first load).
3.  Harder for beginners — requires managing multiple files.

## Unit - 1 - Web Design/HTML Notes - Part 1.docx.md

---
source: HTML Notes - Part 1.docx.docx
type: docx
---

Unit – I                                                      Web Design                                           Grade - 7
HTML
HTML – Hypertext Markup Language.
It describes the structure of a webpage.
To create a webpage, you must create files written in HTML and place them on a webserver. Then any browser can retrieve your webpages on the internet from any device. Device such as PC, laptop, mobile and tablet.
The HTML tells the browser what it needs to display your page.
If you have done your job well your pages will even display well on any device and will work well with speech browsers and screen magnifiers for the visually impaired.
Structure of HTML All HTML information begins with open angle bracket < and end with a closing > angle bracket.
Structure of HTML
Creating webpages using HTML in a Notepad/TextEdit
Windows OS
Press windows logo key
Type Notepad in the Windows search bar to find
Open Notepad.
Enter your HTML Code to Notepad
Click File > Save as > filename.html > Encoding: UTF-8 > Save. (Example - myfirst.html)
Note - Use .html or .htm for file extension. Don't save the file with a .txt extension.
Mac OS
Find TextEdit in app folder
Open TextEdit
Click File > New
Click Format > Make Plain Text.
Enter your HTML Code to TextEdit
Click File > Save, type a filename. html (Example - myfirst.html), then click Save
When prompted about the extension to use, click Use .html
Opening HTML File to display the webpage
Open the saved HTML file in your favorite browser (double click on the file, or right-click - and choose "Open with")
Note – Browser is an interpreter for HTML. It reads the HTML code and interprets them
Editing HTML file to make changes
Right click on the file > Open with > Notepad
HTML Headings
Headers are used to give a heading to a topic, sub-topic, before writing some content in an HTML document.
There are 6 headers - <h1> <h2> <h3> <h4> <h5> <h6>
H1 is the biggest and h6 is the smallest header.
Example
Formatting Tags
Output

## Unit - 1 - Web Design/HTML Notes - Part 2.docx.md

---
source: HTML Notes - Part 2.docx.docx
type: docx
---

Grade 7                                              Unit – I Notes                                                  (Part 2)
Lists
HTML lists allow web developers to group a set of related items in lists.
There ate two types of lists
Ordered List
Unordered  List
Ordered List
An ordered list starts with the <ol> tag.
Each list item starts with the <li> tag.
The list items will be marked with numbers.
Unordered  List
An unordered list starts with the <ul> tag.
Each list item starts with the <li> tag.
The list items will be marked with bullets (small black circles).
Table
HTML tables allow us to arrange data into rows and columns.
<table> tag defines a table.
To define a table caption, use <caption> tag.
A table in HTML consists of table cells inside rows and columns.
Each table row starts with a <tr> and ends with a </tr> tag.
To include headings in table columns we can use the table header tag <th>.
<td> and a </td> tag is used to define table data or table cell.
We can adjust the border, space between the cells, and space between cells and content. It can be done using the following table attributes.
cellpadding is used to define the space between the cell edges and the cell content.
cellspacing is used to define the space between each cell.
border is used to define the width of the table's border.
Example –
<table border = "2" cellpadding = "10" cellspacing = "10"
Images
Images can be used to improve the appearance of a web page.
<img> tag is used to embed or insert an image on a web page.
<img> tag is empty, which means - it contains attributes only, and does not have a closing tag.
<img> tag has two attributes:
src - Specifies the path to the image
alt - Specifies an alternate text for the image
Syntax –
<img src="path" alt="alternatetext">
Video
<video> element is used to show a video on a web page.
Attributes of <video>
controls attribute -  adds video controls, like play, pause, and volume.
width and height attributes - used to adjust the dimensions of the video on the web page.
autoplay attribute – to start a video automatically.
<source> element allows you to specify alternative video files which the browser may choose from and to recognize the format.
HTML Links - Hyperlinks
HTML links are called hyperlinks.
You can click on a link and jump to another document or web page.
The HTML <a> tag defines a hyperlink.
Syntax -
<a href="url">link text</a>
href attribute - indicates the link's destination.
link text - the part that will be visible to the reader.
By clicking on the link text, the specified URL in href will be opened.
CSS
Cascading Style Sheets (CSS) is a markup language responsible for how your web pages will look like.
It controls the colors, fonts, and layouts of your website elements.
This style sheet language also allows you to add effects or animations to your website.
Without CSS, your website will appear as a plain HTML page.
There are 3 types of style sheets -
Inline
Internal
External
Inline
Used to style a specific HTML element.
Add the style attribute to each HTML tag.
This CSS type is not recommended, as each HTML tag needs to be styled individually. Managing your website may become too hard if you only use inline CSS.
However, inline CSS in HTML can be useful in some situations. For example, if you need to apply styles for a single element only, then inline can be used.
Advantages of Inline CSS:
Easy to insert CSS rules into an HTML page. That’s why this method is useful for testing or previewing the changes, and performing quick fixes to your website.
You don’t need to create and upload a separate document as in the external style.
Disadvantages of Inline CSS:
Adding CSS rules to every HTML element is time-consuming and makes your HTML structure messy.
Styling multiple elements can affect your page’s size and download time.
Internal CSS
Internal CSS requires you to add <style> tag in the <head> section of your HTML document.
This CSS style is an effective method of styling a single page.
However, using this style for multiple pages is time-consuming as you need to put CSS rules on every page of your website.
Steps to use internal CSS:
Open your HTML page and locate <head> opening tag.
Put <style> right after the <head> tag
Add CSS rules on a new line
Type the closing tag </style>
Advantage
We will add the CSS code within the same HTML file, you don’t need to upload multiple files and use them multiple times.
Disadvantage
Adding the code to the HTML document can increase the page’s size and loading time
External CSS
With external CSS, we’ll link our web pages to an external .css file, which can be created by any text editor.
This CSS type is a more efficient method, especially for styling a large website. By editing one .css file, you can change your entire site at once.
Steps to use external CSS:
Create a new  file with .css extension file in a text editor, and add the style rules.
I saved it as style.css
In the <head> section of your HTML file, add a reference to your external .css file right after <title> tag:
<link rel="stylesheet" type="text/css" href="filename.css" />
Advantages:
Since the CSS code is in a separate document, your HTML files will have a cleaner structure and are smaller in size.
You can use the same .css file for multiple pages.
Disadvantages
Your pages may not be linked correctly until the external CSS is loaded.
Uploading or linking to multiple CSS files can increase your site’s download time.

## Unit - 1 - Web Design/Inline CSS SDL.docx.md

---
source: Inline CSS SDL.docx.docx
type: docx
---

Inline CSS
What is CSS?
CSS stands for Cascading Style Sheets.
It is used to control the look and layout of a webpage.
While HTML provides structure and content, CSS adds color, design, and style.
Example:
HTML → the skeleton
CSS → the clothes and makeup that make it look nice
What is Inline CSS?
Inline CSS means writing CSS directly inside an HTML tag using the style attribute.
This style applies only to that specific HTML element, not to the rest of the page.
Syntax of Inline CSS
<tagname style="property:value;">
content
</tagname>
tagname – HTML tag like <p>, <h1>, <div>, etc.
style – attribute used to add CSS directly inside the tag.
property – the style you want to change (like color, background-color).
value – the setting for that property (like red, 20px).
Example 1:
<p style="color: blue;">This is a blue paragraph.</p>
Explanation:
The tag <p> is a paragraph.
The style attribute sets color: blue;, so the text becomes blue.
Only this paragraph will appear blue — other <p> elements won’t.
Example 2: Multiple Properties
<h1 style="color: white; background-color: green; text-align: center;">
Welcome to My Website!
</h1>
Explanation:
color: white; → text color
background-color: green; → background color of heading
text-align: center; → centers the heading text
You can write multiple CSS properties in one style attribute — just separate them with semicolons (;).
Example 3: Inline CSS for Images
<img src="flower.jpg" style="width: 200px; height: 150px; border: 3px solid black;">
This makes the image 200px wide, 150px tall, and adds a black border.
Example 4: Inline CSS for Links
<a href="https://example.com" style="color: red; text-decoration: none;">
Visit Example </a>
This makes the link text red and removes the underline.
When to Use Inline CSS
Use Inline CSS when:
You want to style only one element quickly.
You are testing or debugging styles.
You don’t need to reuse the same style elsewhere.
Key Points About Inline CSS
Advantages of Inline CSS
Quick and simple — you can apply style directly without creating separate CSS blocks.
Useful for single changes or testing new styles.
No need for <style> or external files.
Overrides styles from internal or external CSS (has highest priority).
Disadvantages of Inline CSS
Not reusable – You have to repeat the same style for every element.
Makes HTML messy – Mixing content (HTML) with style (CSS) reduces clarity.
Hard to maintain – If you want to change color later, you must edit every tag.
Slower for big projects – Many repeated styles increase page size.
No separation of design and structure – breaks the best practice of web design.

## Unit - 1 - Web Design/Internal CSS notes.pdfPDF.md

---
source: Internal CSS notes.pdfPDF.pdf
type: pdf
---

CSS NOTES — INTERNAL CSS
1. What is CSS?
CSS (Cascading Style Sheets) is used to style and control the appearance of a webpage.
It allows designers to change colors, fonts, spacing, borders, layouts, and more — making
websites look attractive and consistent.
2. Types of CSS
Type
Inline CSS
Internal
CSS
External
CSS
Where It Is Written
Inside a specific HTML tag using the
style attribute
Inside the <style> tag in the <head>
section of the HTML document
In a separate .css file linked with
<link> tag
Applies To
Best For
One single
element
One webpage  Styling one page
Quick, small
changes
Multiple
webpages
only
Large websites
(reusable styles)
3. What is Internal CSS?
Internal CSS means writing all your CSS styles within the HTML file itself, but not
directly inside tags.
It goes inside a <style> element, which is placed between the <head> and </head> tags.
It affects only that specific HTML page — not others.
Structure of Internal CSS
<!DOCTYPE html>
<html>
<head>
<title>Internal CSS Example</title>
<style>
/* CSS rules are written here */
body {
background-color: #f2f2f2;
font-family: Arial, sans-serif;
}
h1 {
color: darkblue;
text-align: center;
}
p {
color: #333333;
font-size: 18px;
}
</style>
</head>
<body>
<h1>Welcome to My Website</h1>
<p>This page is styled using internal CSS.</p>
</body>
</html>
4. Syntax of Internal CSS
Each CSS rule follows this structure:
selector {
property: value;
}
Explanation:
•  Selector: The HTML element you want to style (e.g., h1, p, body)
•  Property: The type of style you want to apply (e.g., color, font-size, background-
color)
•  Value: The setting for that property (e.g., blue, 20px, center)
Example:
h1 {
color: blue;
text-align: center;
}
5.Advantages of Internal CSS
1.  Easy to manage – all styles are in one place within the same file.
2.  Useful for single-page websites – styles don’t need a separate file.
3.  Faster to test – no need to open or link external files.
4.  Overrides external CSS – has higher priority when both exist.
6. Disadvantages of Internal CSS
1.  Not reusable – styles apply only to one page.
2.  Increases file size – HTML file becomes longer.
3.  Slower loading for large sites – not efficient for multiple pages.
4.  Harder to maintain – changes must be made in every page separately.
7. Internal vs Inline vs External CSS
Feature
Location
Affects
Ease of
Editing
Reusability
Speed
Inline CSS
Inside element (style
attribute)
One element
Hard (repeated code)
Internal CSS
Inside <style> in
<head>
One webpage
Medium
None
Fast for small changes
One page only
Fine for one page
External CSS
Separate .css file
Whole website
Easy
Across pages
Best for large
sites
8. CSS Comments
Comments help explain your CSS code.
They are ignored by the browser.
Syntax:
/* This is a CSS comment */
Example:
h1 {
color: blue; /* Heading color */
}
9. Common Properties Used in Internal CSS
Property
Purpose
Changes text color
Changes size of text
Sets font style
color
font-size
font-family
background-color  Changes background
text-align
border
margin
padding
width / height
Aligns text
Adds border
Adds space outside element  margin: 10px;
padding: 15px;
Adds space inside element
width: 200px; height: 100px;
Sets size of an element
Example
color: red;
font-size: 20px;
font-family: Verdana;
background-color: lightblue;
text-align: center;
border: 2px solid black;

## Unit - 1 - Web Design/List in HTML.pdfPDF.md

---
source: List in HTML.pdfPDF.pdf
type: pdf
---

What is a list in HTML?
A list groups related items so they are easy to read and understand. In web
pages lists are used for navigation menus, steps, feature lists, glossaries, and
more. HTML provides three semantic list types:
•  <ul> — unordered list (bulleted)
•  <ol> — ordered list (numbered)
•  <dl> — description list (definition/term pairs)
Using the correct list type improves structure, readability, and accessibility.
2. Unordered list (<ul>)
Use when the order of items does not matter (e.g., shopping list, features).
Basic syntax:
<ul>
<li>Milk</li>
<li>Bread</li>
<li>Eggs</li>
</ul>
Example (shopping list):
<ul>
<li>Apples</li>
<li>Bread</li>
<li>Butter</li>
</ul>
3. Ordered list (<ol>)
Use when sequence matters (steps, instructions, rankings).
Basic syntax:
<ol>
<li>Open the app</li>
<li>Enter username</li>
<li>Enter password</li>
<li>Click Login</li>
</ol>
Useful attributes:
•
type — style of marker ("1", "A", "a", "I", "i")
Example: <ol type="A"> produces A, B, C...
•  start — starting number (integer)
•
Example: <ol start="5">
reversed — shows list in reverse order
Example: <ol reversed>
Example:
<ol type="I" start="3">
<li>First step</li>
<li>Second step</li>
<li>Third step</li>
</ol>
4. Description list (<dl>)
Use for pairs like term + definition, question + answer, or label + value.
Syntax:
<dl>
<dt>HTML</dt>
<dd>HyperText Markup Language</dd>
<dt>CSS</dt>
<dd>Cascading Style Sheets</dd>
</dl>
Example (glossary):
<dl>
<dt>API</dt>
<dd>Application Programming Interface</dd>
<dt>UI</dt>
<dd>User Interface</dd>
</dl>
5. Nested lists
You can put a list inside an <li> to show subitems.
<ul>
<li>Fruits
<ul>
<li>Apples</li>
<li>Bananas</li>
</ul>
</li>
<li>Vegetables
<ul>
<li>Carrot</li>
<li>Spinach</li>
</ul>
</li>
</ul>

## Unit - 1 - Web Design/Unit 1 - Internet.pptx.md

---
source: Unit 1 - Internet.pptx.pptx
type: pptx
---

Unit I – Web Design
Content
Internet
Accessing the internet
Webpage
Website
URL
Internet
A global system of interconnected computers, using an Internet Protocol (IP) for communication and sharing information is called the Internet.
The Internet Protocol address is a numerical identification code assigned for any device connected to a network. It acts as an identification interface for Internet users.
To know your IP address on Windows
Click on Windows
Type cmd in the search box.
Type ipconfig and press enter
To know your IP address on Mac
Click on the Apple icon.
Select System Preferences.
Click Network.
accessing The Internet
Internet Service Provider (ISP) : It provides direct access for using the internet from your office or home, connected through landlines.
WiFi – Wireless Fidelity
Wi-Fi is a wireless networking technology, by which we can access networks or connect with other computers or mobile using a wireless medium.
In Wi-Fi, data are transferred over radio frequencies (100 kHz to 300 GHz) in a circular range
The range of WiFi depends on the router which provides the radio frequency: 2.4 GHz and 5 GHz.
Hotspot
A hotspot is a physical location where people can access the Internet using Wi-Fi.
Mobile hotspot: A mobile hotspot sometimes called a portable hotspot.
While a regular Wi-Fi hotspot is tied to a physical location, you can create a mobile hotspot by using your smartphone’s data connection to connect your laptop to the Internet.
G?
G – Generation
Generation of wireless phone technology
What is the difference between a website and a webpage?
Webpage is an individual document that is linked to a website.
Website is a collection of linked web pages and it consists of one or more webpages.
Example
https://www.myntra.com/feedback                        Webpage
https://www.myntra.com                                           Website
URL
Uniform Resource Locator
Specifies the location of a resource on the internet
Parts of URL
https://www.cowin.gov.in
HTTP – hyper text transfer protocol is used in transferring webpages in your computer.
Cowin – Domain Name or website name -  human-friendly text form of the IP address.
Gov.in – Type of organization