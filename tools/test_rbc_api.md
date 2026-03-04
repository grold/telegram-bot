# `test_rbc_api.py` Documentation Summary

This script is a diagnostic utility designed to verify connectivity and inspect the response structure of the RBC Quote API, specifically for the USDRUB ticker.

## Overview
The script performs a synchronous GET request to the RBC Quote API endpoint and prints detailed information about the response, including status codes, headers, and the payload content.

## Technical Details
- **Target URL**: `https://www.rbc.ru/quote/v2/publisher/ticker/item/USDRUB`
- **Dependencies**: `requests`
- **Timeout**: 10 seconds

### Key Functionality
1. **Browser Mimicry**: Uses custom headers (`User-Agent`, `Referer`, `Origin`) to bypass basic anti-bot filters.
2. **Response Validation**:
   - Checks the `Content-Type` header.
   - If the response is `application/json`, it pretty-prints the JSON object.
   - If the response is not JSON, it prints the first 500 characters of the raw text for debugging.
3. **Error Handling**: Includes a broad `try-except` block to capture and print connection errors or request timeouts.

## Usage
Run the script directly from the terminal:
```bash
python tools/test_rbc_api.py
```

## Purpose
Used primarily for debugging currency data retrieval logic and ensuring that the RBC API hasn't changed its response format or security requirements.
