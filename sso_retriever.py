# sso_manager.py
import requests
import json
import random

# The endpoint used by the Habbo Flash/Air client to generate a login ticket.
API_URL = "https://www.habbo.com/api/client/clientnative/url"

# Standard headers to mimic a legitimate browser request.
# NOTE: Origin and Referer are set to .com.tr here. Change this if targeting .com, .es, .br, etc.
BASE_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'origin': 'https://www.habbo.com.tr',
    'referer': 'https://www.habbo.com.tr/',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-habbo-fingerprint': 'j' # Often required by Habbo's WAF
}

# A rotation of modern User-Agents to reduce the chance of fingerprinting blocking.
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
]

def get_sso_ticket(cookie_input: list | dict, proxy_url: str = None) -> str | None:
    """
    Interacts with the Habbo Web API to generate a Single Sign-On (SSO) ticket.
    This ticket is used by the Python client to authenticate via TCP.

    Args:
        cookie_input (list | dict): 
            Either a list of cookie dictionaries [{'name': '...', 'value': '...'}, ...] 
            OR a dictionary containing a "cookies" key.
        proxy_url (str, optional): 
            The full proxy URL to use for this request. 
            Examples: 
                - "http://user:pass@1.2.3.4:8080"
                - "socks5://127.0.0.1:9050" (Tor)
            If None, the request is made directly (System IP).

    Returns:
        str: The extracted SSO ticket (e.g., "300-47b8..."), or None if failed.
    """

    # 1. Input Normalization
    # Sometimes the bot framework passes the whole account object, sometimes just the list.
    cookie_list = []
    if isinstance(cookie_input, dict):
        cookie_list = cookie_input.get("cookies", [])
    elif isinstance(cookie_input, list):
        cookie_list = cookie_input
    else:
        print("❌ [SSO] Error: Invalid cookie input format.")
        return None

    # 2. Extract Required Cookies
    # Habbo requires 'session.id' and 'browser_token' to authorize the API call.
    required_cookies = {}
    for cookie_obj in cookie_list:
        if not isinstance(cookie_obj, dict): continue
        
        name = cookie_obj.get("name")
        value = cookie_obj.get("value")
        
        if name == "session.id":
            required_cookies["session.id"] = value
        elif name == "browser_token":
            required_cookies["browser_token"] = value
    
    if "session.id" not in required_cookies or "browser_token" not in required_cookies:
        print("❌ [SSO] Error: Missing 'session.id' or 'browser_token' in cookies.")
        return None

    # 3. Proxy Configuration
    proxies = None
    if proxy_url and isinstance(proxy_url, str) and len(proxy_url) > 0:
        # Requests library handles http/socks schemas automatically
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

    # 4. Header Setup
    current_headers = BASE_HEADERS.copy()
    current_headers['user-agent'] = random.choice(USER_AGENTS)

    # 5. Execute Request
    try:
        if proxies:
            print(f"🌍 [SSO] Requesting ticket via Proxy...")
        else:
            print(f"🌍 [SSO] Requesting ticket via Direct Connection...")

        response = requests.post(
            API_URL, 
            headers=current_headers, 
            cookies=required_cookies, 
            proxies=proxies,
            timeout=15  # Timeout prevents hanging if proxy is dead
        )
        response.raise_for_status() # Raises Error for 403, 404, 500 etc.

        # 6. Parse JSON Response
        ticket_data = response.json()
        raw_ticket = ticket_data.get('ticket')
        
        if not raw_ticket:
            print("❌ [SSO] Error: Response did not contain a 'ticket' field.")
            return None

        # 7. Format Ticket
        # The web API returns a format like "UUID.ActualTicket".
        # The TCP client only needs the part AFTER the dot.
        parts = raw_ticket.split('.', 1)
        if len(parts) == 2:
            return parts[1]
        else:
            # Fallback: In rare cases, if no dot exists, return the whole thing
            print(f"⚠️ [SSO] Warning: Unusual ticket format: {raw_ticket}")
            return raw_ticket

    except requests.exceptions.ProxyError:
        print(f"❌ [SSO] Proxy Error: Could not connect to {proxy_url}")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ [SSO] HTTP Error {response.status_code}: {http_err}")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ [SSO] Timeout: Connection took too long.")
        return None
    except Exception as err:
        print(f"❌ [SSO] Unexpected Error: {err}")
        return None