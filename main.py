import threading
import json
import time
import uuid
from loguru import logger
from websocket import WebSocketApp
from urllib.parse import urlparse, unquote
from pyfiglet import Figlet
from colorama import init, Fore, Style

# Initialize colorama
init()

# Function to print the introduction banner
def print_intro():
    # Print in blue color
    print(Fore.BLUE, end='')
    try:
        f = Figlet(font='starwars')  # Ensure 'starwars' font is installed
        print(f.renderText("Grass 🍀 V3"))
    except Exception as e:
        logger.error(f"Error rendering figlet font: {e}")
        print("Grass 🍀 V3")  # Fallback if figlet fails
    print(Style.RESET_ALL)

    # Print other lines with colors
    print(Fore.GREEN + "📡 Grass V3 B0T" + Style.RESET_ALL)   # Green color for the description  
    print(Fore.CYAN + "👨‍💻 Created by: Cipher" + Style.RESET_ALL)  # Cyan color for the creator
    print(Fore.MAGENTA + "🔧 Initiating Grass Season2 B0T..." + Style.RESET_ALL)  # Magenta color for the upgrade message

    # Print the box with following links
    print("════════════════════════════════════════════════════════════") 
    print("║       Follow us for updates and support:                 ║")
    print("║                                                          ║")
    print("║     Twitter:                                             ║")
    print("║     https://twitter.com/cipher_airdrop                   ║")
    print("║                                                          ║")
    print("║     Telegram:                                            ║")
    print("║     - https://t.me/+tFmYJSANTD81MzE1                     ║")
    print("╚════════════════════════════════════════════════════════════")

# Call the introduction function
print_intro()

# Define custom headers
custom_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def connect_to_wss(proxy_url, user_id):
    while True:
        device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, proxy_url + user_id))
        logger.info(f"Device ID: {device_id} for User ID: {user_id}")

        ws_url = "wss://proxy.wynd.network:4650/"

        headers = custom_headers.copy()

        # Parse the proxy URL
        parsed_proxy = urlparse(proxy_url)
        proxy_scheme = parsed_proxy.scheme.lower()
        proxy_host = parsed_proxy.hostname
        proxy_port = parsed_proxy.port
        proxy_username = unquote(parsed_proxy.username) if parsed_proxy.username else None
        proxy_password = unquote(parsed_proxy.password) if parsed_proxy.password else None

        # Determine the proxy type
        if proxy_scheme in ('http', 'https'):
            proxy_type = 'http'
        elif proxy_scheme == 'socks5':
            proxy_type = 'socks5'
        else:
            logger.error(f"[User {user_id}] Unsupported proxy scheme: {proxy_scheme}")
            return

        # Set up proxy authentication if credentials are provided
        proxy_auth = (proxy_username, proxy_password) if proxy_username and proxy_password else None

        def on_message(ws, message):
            logger.info(f"[User {user_id}] Received message: {message}")
            try:
                message = json.loads(message)
                if message.get("action") == "AUTH":
                    auth_response = {
                        "id": message["id"],
                        "origin_action": "AUTH",
                        "result": {
                            "browser_id": device_id,
                            "user_id": user_id,
                            "user_agent": headers['User-Agent'],
                            "timestamp": int(time.time()),
                            "device_type": "extension",
                            "version": "2.5.0"
                        }
                    }
                    ws.send(json.dumps(auth_response))

                elif message.get("action") == "PONG":
                    pong_response = {"id": message["id"], "origin_action": "PONG"}
                    ws.send(json.dumps(pong_response))
            except json.JSONDecodeError:
                logger.error(f"[User {user_id}] Failed to decode JSON message: {message}")
            except Exception as e:
                logger.error(f"[User {user_id}] Exception in on_message: {str(e)}")

        def on_error(ws, error):
            logger.error(f"[User {user_id}] Error with proxy {proxy_url}: {str(error)}")

        def on_close(ws, close_status_code, close_msg):
            logger.info(f"[User {user_id}] WebSocket closed with code {close_status_code}, message: {close_msg}")

        def on_open(ws):
            logger.info(f"[User {user_id}] WebSocket connection opened")

            def run():
                while True:
                    send_message = json.dumps(
                        {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}}
                    )
                    try:
                        ws.send(send_message)
                    except Exception as e:
                        logger.error(f"[User {user_id}] Exception in PING thread: {str(e)}")
                        break
                    time.sleep(20)

            threading.Thread(target=run, daemon=True).start()

        # Create the WebSocketApp instance
        ws = WebSocketApp(
            ws_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        try:
            # Run the WebSocketApp with proxy settings
            ws.run_forever(
                http_proxy_host=proxy_host,
                http_proxy_port=proxy_port,
                http_proxy_auth=proxy_auth,
                proxy_type=proxy_type,
                sslopt={"cert_reqs": 0}
            )
        except Exception as e:
            logger.error(f"[User {user_id}] Exception during run_forever: {str(e)}")

        logger.info(f"[User {user_id}] Attempting to reconnect to proxy {proxy_url} in 5 seconds...")
        time.sleep(5)

def main():
    num_accounts = int(input("How many accounts will you use? "))

    user_ids = []
    for i in range(num_accounts):
        user_id = input(f"Enter User ID for account {i + 1}: ")
        user_ids.append(user_id)

    # Read proxies from 'proxies.txt'
    try:
        with open('proxies.txt', 'r') as f:
            proxy_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("proxies.txt file not found.")
        return

    # Check if we have enough proxies
    required_proxies = num_accounts * 10
    if len(proxy_list) < required_proxies:
        logger.error(f"Not enough proxies. Required: {required_proxies}, Available: {len(proxy_list)}")
        return

    threads = []
    proxy_index = 0
    for user_id in user_ids:
        # Assign 10 proxies to this user
        user_proxies = proxy_list[proxy_index:proxy_index + 10]
        proxy_index += 10

        for proxy in user_proxies:
            t = threading.Thread(target=connect_to_wss, args=(proxy, user_id))
            t.start()
            threads.append(t)

    for t in threads:
        t.join()

if __name__ == '__main__':
    main()
