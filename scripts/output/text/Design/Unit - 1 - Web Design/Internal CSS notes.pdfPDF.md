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