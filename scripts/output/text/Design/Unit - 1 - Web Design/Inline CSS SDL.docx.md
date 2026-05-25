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