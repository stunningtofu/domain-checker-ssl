#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e
# Treat unset variables as an error
set -u

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    printf ".env file not found!\n"
    exit 1
fi

# Ensure required environment variables are set
if [ -z "${BOT_TOKEN:-}" ] || [ -z "${CHAT_ID:-}" ] || [ -z "${MESSAGE_ID:-}" ]; then
    printf "Required environment variables (BOT_TOKEN, CHAT_ID, MESSAGE_ID) are not set in .env file.\n"
    exit 1
fi

# Constants
DAYS_THRESHOLD=7

# Function to send a message via Telegram
send_telegram_message() {
    local message=$1
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        -d text="${message}" \
        -d reply_to_message_id="${MESSAGE_ID}"
}

# Function to check SSL certificate expiry
check_ssl_expiry() {
    local domain=$1
    local exp_date
    local exp_date_seconds
    local current_date_seconds
    local diff_days

    # Get the expiration date of the SSL certificate
    exp_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
    
    # Convert expiration date to seconds since epoch
    exp_date_seconds=$(date -d "$exp_date" +%s)
    
    # Get the current date in seconds since epoch
    current_date_seconds=$(date +%s)
    
    # Calculate the difference in days
    diff_days=$(( (exp_date_seconds - current_date_seconds) / 86400 ))
    
    # Check if the certificate expires in DAYS_THRESHOLD days or less
    if [ "$diff_days" -le "$DAYS_THRESHOLD" ]; then
        local message="The SSL certificate for $domain expires in $diff_days days."
        printf "%s\n" "$message"
        send_telegram_message "$message"
    else
        printf "The SSL certificate for %s is still alive.\n" "$domain"
    fi
}

# Ensure required commands are available
command -v openssl >/dev/null 2>&1 || { printf "openssl is required but it's not installed. Aborting.\n" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { printf "curl is required but it's not installed. Aborting.\n" >&2; exit 1; }

# Read domains from the domains file
if [ -f domains ]; then
    mapfile -t domains < domains
else
    printf "domains file not found!\n"
    exit 1
fi

for domain in "${domains[@]}"; do
    check_ssl_expiry "$domain"
done