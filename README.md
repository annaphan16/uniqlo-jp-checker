# 🦊 Uniqlo JP Checker - Camoufox Version

Công cụ check tài khoản Uniqlo JP sử dụng Camoufox (anti-detect browser) để tránh bị phát hiện bot.

## ✨ Tính năng

- ✅ Sử dụng Camoufox - anti-detect browser với fingerprint randomization
- ✅ Tự động detect timezone/locale từ proxy IP
- ✅ Hỗ trợ multi-threading để check nhiều tài khoản đồng thời
- ✅ Hỗ trợ proxy với authentication
- ✅ Tự động retry khi gặp lỗi network/browser crash
- ✅ Lấy thông tin chi tiết: Orders, Addresses, Cards
- ✅ Giao diện console với màu sắc, status bar, terminal title
- ✅ Lưu kết quả vào file HITS.txt và failed.txt

## 📋 Yêu cầu

- Python 3.8+
- Camoufox
- Playwright
- Colorama

## 🚀 Cài đặt

### Bước 1: Cài đặt dependencies

```bash
cd camou-ver
pip install -r requirements.txt
```

### Bước 2: Cài đặt Playwright browsers

```bash
playwright install firefox
```

**Lưu ý:** Camoufox sử dụng Firefox engine, nên chỉ cần cài Firefox.

## ⚙️ Cấu hình

### 1. File acc.txt

Tạo file `acc.txt` với format:

```
email:password
```

Ví dụ:

```
test@example.com:password123
user@gmail.com:mypassword
```

### 2. File proxy.txt

Tạo file `proxy.txt` với format:

```
ip:port:username:password
```

Ví dụ:

```
123.45.67.89:8080:myuser:mypass123
98.76.54.32:3128:proxyuser:secretpass
```

**Lưu ý:**
- Mỗi dòng là một proxy
- Dòng bắt đầu bằng `#` sẽ bị bỏ qua (comment)
- Dòng trống sẽ bị bỏ qua
- Proxy sẽ được rotate tự động cho mỗi tài khoản

### 3. File config.json

Chỉnh sửa `config.json` để tùy chỉnh:

```json
{
    "threads": 2,                    // Số luồng chạy đồng thời
    "retry": 5,                      // Số lần retry khi lỗi
    "use_proxy": true,               // Bật/tắt proxy
    "camoufox_headless": false,      // Chạy ẩn browser (true) hoặc hiện (false)
    "debug": true,                   // Bật debug logs
    "acc_file": "acc.txt",
    "proxy_file": "proxy.txt",
    "hits_file": "HITS.txt",
    "failed_file": "failed.txt"
}
```

## 📖 Sử dụng

### Chạy checker

```bash
cd camou-ver
python uniqlo_jp_checker_camoufox.py
```

### Quy trình hoạt động

1. **Tool load config và danh sách tài khoản**
   ```
   ✅ Loaded 10 accounts from acc.txt
   ✅ Loaded 5 proxies from proxy.txt
   ```

2. **Bắt đầu check từng tài khoản**
   ```
   🦊 Login with Camoufox...
   Step 1: Loading wishlist (will redirect to login)...
   Step 2: Filling login form...
   Step 3: Clicking login...
   Step 4: Checking login result...
   ```

3. **Kết quả được hiển thị và lưu file**
   - ✅ **HIT**: Lưu vào `HITS.txt` với thông tin đầy đủ
   - ❌ **FAILED**: Lưu vào `failed.txt`

4. **Dừng tool**
   - Nhấn `Ctrl+C` để dừng
   - Tool sẽ cleanup và đóng tất cả browsers

## 🎯 Tính năng nâng cao

### Anti-detect Features của Camoufox

Camoufox tự động randomize các fingerprints sau để tránh bị phát hiện:

- ✅ Canvas fingerprint
- ✅ WebGL fingerprint
- ✅ Audio context fingerprint
- ✅ Font fingerprinting
- ✅ Screen resolution
- ✅ Timezone (tự động từ proxy IP với `geoip=True`)
- ✅ Locale/Language (tự động từ proxy IP)
- ✅ User-Agent randomization
- ✅ WebRTC IP leak protection
- ✅ Hardware concurrency
- ✅ Battery API
- ✅ Media devices

### Thông tin được lấy từ tài khoản HIT

Khi tài khoản login thành công, tool sẽ lấy:

1. **Orders (Đơn hàng)**
   - Tổng số đơn hàng
   - Đơn hàng gần nhất: ngày đặt, trạng thái, số tiền, số items

2. **Addresses (Địa chỉ)**
   - Danh sách địa chỉ giao hàng
   - Thông tin: tên, địa chỉ, mã bưu điện, số điện thoại

3. **Cards (Thẻ thanh toán)**
   - Danh sách thẻ đã lưu
   - Thông tin: loại thẻ (VISA/MC/JCB), số thẻ (masked), ngày hết hạn

### Retry Logic

Tool tự động retry khi gặp lỗi:

- **Browser crash**: Retry với cùng proxy
- **Network timeout**: Retry với timeout tăng dần
- **Proxy error**: Chuyển sang proxy khác
- **Max retries**: 5 lần (có thể config trong `config.json`)

## 🔧 Tùy chỉnh

### Chạy headless mode (ẩn browser)

Sửa trong `config.json`:

```json
{
    "camoufox_headless": true
}
```

**Lưu ý:** Headless mode giúp tiết kiệm tài nguyên nhưng có thể dễ bị phát hiện hơn.

### Tăng số luồng (threads)

Sửa trong `config.json`:

```json
{
    "threads": 5
}
```

**Cảnh báo:** Mỗi browser instance tiêu tốn ~300-500MB RAM. Đảm bảo hệ thống có đủ tài nguyên.

### Tắt debug logs

Sửa trong `config.json`:

```json
{
    "debug": false
}
```

## 📝 Ví dụ Output

### Ví dụ 1: Tài khoản HIT

```
🦊 Login with Camoufox...
Step 1: Loading wishlist (will redirect to login)...
✅ Login page fully loaded in 3.2s
Step 2: Filling login form...
✅ Form filled successfully
Step 3: Clicking login...
Step 4: Checking login result...
✅ Login successful! Redirected to member page
Step 5: Fetching account info...
  ✓ Orders fetched
  ✓ Addresses fetched
  ✓ Cards fetched
📦 Orders: 5
📍 Addresses: 2
💳 Cards: 1
✅ HIT - Login successful

[HITS.txt]
test@example.com:password123 | SUCCESS | Orders:5|Latest:2024-01-15-配送済み-¥8900(3items) | Addresses:2|山田,太郎,東京都渋谷区...,03-1234-5678 | Cards:1|VISA,************1234,0427
```

### Ví dụ 2: Tài khoản FAILED

```
🦊 Login with Camoufox...
Step 1: Loading wishlist (will redirect to login)...
✅ Login page fully loaded in 2.8s
Step 2: Filling login form...
✅ Form filled successfully
Step 3: Clicking login...
Step 4: Checking login result...
❌ Error found: メールアドレスまたはパスワードが正しくありません
❌ Login failed: メールアドレスまたはパスワードが正しくありません

[failed.txt]
wrong@example.com:wrongpass | Login failed: メールアドレスまたはパスワードが正しくありません
```

## ⚠️ Lưu ý quan trọng

1. **Tài nguyên hệ thống**:
   - Mỗi browser instance tiêu tốn ~300-500MB RAM
   - Đảm bảo hệ thống có đủ RAM khi chạy nhiều threads
   - Khuyến nghị: 2-3 threads cho máy 8GB RAM

2. **Proxy quality**:
   - Sử dụng proxy chất lượng cao, tốc độ ổn định
   - Proxy chậm có thể gây timeout
   - Nên dùng proxy residential thay vì datacenter

3. **Rate limiting**:
   - Không check quá nhiều tài khoản cùng lúc
   - Thêm delay giữa các lần check (config trong `config.json`)
   - Tránh bị Uniqlo block IP/proxy

4. **Legal compliance**:
   - Chỉ check tài khoản của bạn hoặc có sự cho phép
   - Tuân thủ Terms of Service của Uniqlo
   - Tool chỉ dùng cho mục đích hợp pháp

5. **Bảo mật**:
   - Không chia sẻ file `acc.txt` và `HITS.txt`
   - Lưu trữ an toàn thông tin tài khoản
   - Xóa logs sau khi sử dụng nếu cần

## 🐛 Troubleshooting

### Lỗi: "Chưa cài đặt camoufox"

```bash
pip install camoufox playwright
playwright install firefox
```

### Lỗi: "Browser failed to launch"

**Nguyên nhân:** Chưa cài Playwright browsers hoặc thiếu dependencies

**Giải pháp:**
```bash
playwright install firefox
# Hoặc cài lại force
playwright install --force firefox
```

### Lỗi: "Timeout" khi load trang

**Nguyên nhân:** Proxy chậm hoặc network không ổn định

**Giải pháp:**
- Thử proxy khác
- Tăng timeout trong code (mặc định 180s)
- Kiểm tra kết nối internet

### Proxy không hoạt động

**Nguyên nhân:** Format sai hoặc proxy die

**Giải pháp:**
- Kiểm tra format: `ip:port:user:pass`
- Test proxy bằng tool khác trước
- Đảm bảo proxy hỗ trợ HTTP/HTTPS
- Thử proxy khác

### Lỗi: "Target closed" / "Browser crashed"

**Nguyên nhân:** Browser bị crash do thiếu RAM hoặc lỗi Camoufox

**Giải pháp:**
- Giảm số threads trong `config.json`
- Đóng các ứng dụng khác để giải phóng RAM
- Update Camoufox: `pip install --upgrade camoufox`

### Không lấy được thông tin Orders/Addresses/Cards

**Nguyên nhân:** API bị block hoặc session hết hạn

**Giải pháp:**
- Đây là lỗi từ Uniqlo, không phải tool
- Thông tin cơ bản vẫn được lưu (HIT/FAILED)
- Thử lại sau hoặc login thủ công để kiểm tra

## 📊 So sánh với Playwright thông thường

| Tính năng | Playwright | Camoufox |
|-----------|-----------|----------|
| Anti-detect | ❌ Cần config thủ công | ✅ Tự động |
| Fingerprint randomization | ❌ Không có | ✅ Có sẵn |
| GeoIP detection | ❌ Không có | ✅ Tự động từ proxy |
| WebRTC leak protection | ⚠️ Cần config | ✅ Tự động |
| Tốc độ | ⚡ Nhanh hơn | 🐢 Chậm hơn ~10-20% |
| Tài nguyên | 💾 Ít hơn | 💾 Nhiều hơn ~20% |
| Khả năng bypass bot detection | ⚠️ Trung bình | ✅ Cao |

**Kết luận:** Camoufox phù hợp cho các tác vụ cần tránh bị phát hiện bot, còn Playwright thông thường phù hợp cho tốc độ.

## 📚 Tài liệu tham khảo

- [Camoufox Documentation](https://camoufox.com/docs)
- [Camoufox GitHub](https://github.com/daijro/camoufox)
- [Playwright Documentation](https://playwright.dev/python/)
- [Uniqlo JP](https://www.uniqlo.com/jp/)

## 🔄 Changelog

### Version 1.0 (Camoufox)
- ✅ Chuyển từ Playwright sang Camoufox
- ✅ Thêm anti-detect features tự động
- ✅ Tự động detect timezone/locale từ proxy
- ✅ Cải thiện bypass bot detection

## 📄 License

MIT License - Tự do sử dụng cho mục đích cá nhân và thương mại.

**Disclaimer:** Tool chỉ dùng cho mục đích học tập và nghiên cứu. Người dùng tự chịu trách nhiệm về việc sử dụng tool.

---

**Made with 🦊 and ❤️ for Uniqlo enthusiasts**

