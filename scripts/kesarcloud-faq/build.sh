#!/bin/bash
# KesarCloud FAQ PDF Compiler Script

HTML_FILE="/home/vreddy1/Desktop/Projects/scripts/kesarcloud-faq/faq.html"
PDF_FILE="/home/vreddy1/Desktop/Projects/scripts/kesarcloud-faq/faq.pdf"

echo "Compiling KesarCloud FAQ from HTML to PDF..."
if google-chrome-stable --headless --disable-gpu --print-to-pdf="$PDF_FILE" --no-sandbox "$HTML_FILE"; then
    echo "Success! PDF successfully compiled and saved to: $PDF_FILE"
    ls -lh "$PDF_FILE"
else
    echo "Error: Failed to compile PDF using google-chrome-stable."
    exit 1
fi
