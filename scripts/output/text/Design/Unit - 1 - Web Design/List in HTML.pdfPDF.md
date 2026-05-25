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