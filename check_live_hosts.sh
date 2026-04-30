#!/bin/bash

INPUT_FILE="./test_output/subdomains.txt"
OUTPUT_FILE="./test_output/live-hosts.txt"

# Create output directory if it doesn't exist
mkdir -p ./test_output

# Clear output file
> "$OUTPUT_FILE"

echo "Testing subdomains..."

while read -r subdomain; do
    # Skip empty lines
    if [[ -z "$subdomain" ]]; then
        continue
    fi
    
    # Test with curl, get headers for status code
    response=$(curl -s -I "https://$subdomain" 2>/dev/null)
    if [[ $? -eq 6 ]]; then
        echo "$subdomain - DNS_FAILED - Could not resolve host" >> "$OUTPUT_FILE"
        echo "DNS Failed: $subdomain"
        continue
    fi
    
    status_code=$(echo "$response" | head -1 | awk '{print $2}')
    if [[ -z "$status_code" ]]; then
        status_code="FAILED"
    fi
    
    # Get title if response is successful
    if [[ "$status_code" == "200" ]]; then
        title=$(curl -s "https://$subdomain" 2>/dev/null | grep -o '<title>.*</title>' | sed 's/<title>//' | sed 's/<\/title>//')
        if [[ -z "$title" ]]; then
            title="No title found"
        fi
    else
        title="N/A"
    fi
    
    echo "$subdomain - $status_code - $title" >> "$OUTPUT_FILE"
    echo "Tested: $subdomain - $status_code"
done < "$INPUT_FILE"

echo "Results saved to $OUTPUT_FILE"
echo ""
echo "=== Live Hosts Report ==="
cat "$OUTPUT_FILE"