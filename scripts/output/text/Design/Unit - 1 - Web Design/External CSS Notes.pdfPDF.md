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