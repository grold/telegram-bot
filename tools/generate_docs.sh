#!/bin/bash

# Loop through all Python files
for file in *.py; do
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating docs for $file..."

  # Ask Gemini CLI to generate the documentation and print it to stdout
  gemini -m gemini-2.5-flash-lite -p "Generate a Markdown documentation summary for @$file. Print the result to standard output." > "${file%.py}.md"
  
  sleep 5
done