#!/bin/bash

# Loop through all Python files
for file in *.py; do
  echo "Generating docs for $file..."

  # Ask Gemini CLI to generate the documentation and print it to stdout
  gemini -p "Generate a Markdown documentation summary for @$file. Print the
  result to standard output." > "${file%.py}.md"
done