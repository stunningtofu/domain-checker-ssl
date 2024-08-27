import os
import sys
import subprocess
from datetime import datetime, timedelta

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Ensure required environment variables are set
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
MESSAGE_ID = os.getenv('MESSAGE_ID')

required_env_vars = ['BOT_TOKEN', 'CHAT_ID', 'MESSAGE_ID']
for var in required_env_vars:
    if not os.getenv(var):
        print(f"{var} environment variable is required but not set. Aborting.")
        sys.exit(1)

# Constants
DAYS_THRESHOLD = 7

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'reply_to_message_id': MESSAGE_ID
    }
    subprocess.run(['curl', '-s', '-X', 'POST', url, '-d', f'chat_id={CHAT_ID}', '-d', f'text={message}', '-d', f'reply_to_message_id={MESSAGE_ID}'])

def check_ssl_expiry(domain):
    try:
        result = subprocess.run(['openssl', 's_client', '-servername', domain, '-connect', f'{domain}:443'], capture_output=True, text=True, input='Q')
        output = result.stdout
        start = output.find('notAfter=') + len('notAfter=')
        end = output.find('\n', start)
        exp_date_str = output[start:end].strip()
        exp_date = datetime.strptime(exp_date_str, '%b %d %H:%M:%S %Y %Z')
        
        current_date = datetime.utcnow()
        diff_days = (exp_date - current_date).days
        
        if diff_days <= DAYS_THRESHOLD:
            message = f"The SSL certificate for {domain} expires in {diff_days} days."
            print(message)
            send_telegram_message(message)
        else:
            print(f"The SSL certificate for {domain} is still alive.")
    except Exception as e:
        print(f"Error checking SSL certificate for {domain}: {e}")

# Ensure required commands are available
def command_exists(command):
    return subprocess.call(['which', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

if not command_exists('openssl'):
    print("openssl is required but it's not installed. Aborting.")
    sys.exit(1)

if not command_exists('curl'):
    print("curl is required but it's not installed. Aborting.")
    sys.exit(1)

# Read domains from the domains file
if os.path.isfile('domains'):
    with open('domains', 'r') as file:
        domains = [line.strip() for line in file if line.strip()]
else:
    print("domains file not found!")
    sys.exit(1)

for domain in domains:
    check_ssl_expiry(domain)