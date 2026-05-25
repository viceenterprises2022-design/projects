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