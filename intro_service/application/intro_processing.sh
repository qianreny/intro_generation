#!/bin/bash

# Define the path to the Python script in the root folder
trans_file="intro_service.py"  # Replace with the actual filename
# Terminate news service process
pkill -f "$trans_file"

# Define the log directory
log_directory="log"

# Create the log directory if it doesn't exist
mkdir -p "$log_directory"

# Set default values
default_language_model="gpt"
default_limit=10
default_country=1
default_ago=100

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --country=*)
            country="${1#*=}"
            ;;
        --limit=*)
            limit="${1#*=}"
            ;;
        --language_model=*)
            language_model="${1#*=}"
            ;;
        --ago=*)
            ago="${1#*=}"
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
    shift
done

# Set values or use defaults
language_model="${language_model:-$default_language_model}"
limit="${limit:-$default_limit}"
country="${country:-$default_country}"
ago="${ago:-$default_ago}"
region="${region:-$default_region}"

echo "Language Model: $language_model"
echo "Limit: $limit"
echo "Country: $country"
echo "Ago: $ago"

# Check if the Python script file exists
if [ -f "$trans_file" ]; then
    # Generate a log file name with the current date and time
    log_file="$log_directory/run_log_$(date +\%Y_\%m_\%d_\|\%H_\%M_\%S).txt"

    # Run the Python script and discard the output
    temp_file=$(mktemp)
    python3 "$trans_file" --language_model="$language_model" --limit="$limit" --country="$country" --ago="$ago" > "$temp_file" 2>&1 &
    rm "$temp_file"

    # Delete log files older than 30 days
    find . -name 'run_log*' -type f -mtime +30 -exec rm {} \;
    if command -v savelog > /dev/null; then
      echo "savelog is available."
      savelog -l -c 14 "$log_directory/"*.log
    else
      echo "savelog is not available."
    fi
else
    echo "Python script file not found: $trans_file"
fi