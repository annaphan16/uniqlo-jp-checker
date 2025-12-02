# 🚀 Quick Start Guide - Uniqlo JP Checker (Camoufox)

## Cài đặt nhanh (3 bước)

### 1️⃣ Cài đặt dependencies

```bash
cd camou-ver

# Bước 1: Cài Python packages
pip install -r requirements.txt

# Bước 2: Cài Firefox browser (BẮT BUỘC!)
playwright install firefox
```

**⚠️ LƯU Ý:** Phải cài Firefox browser trước khi chạy tool, nếu không sẽ bị lỗi!

### 2️⃣ Cấu hình files

**File `acc.txt`** - Thêm tài khoản cần check:
```
email1@example.com:password1
email2@example.com:password2
```

**File `proxy.txt`** - Thêm proxy (tùy chọn):
```
123.45.67.89:8080:username:password
98.76.54.32:3128:username:password
```

### 3️⃣ Chạy tool

```bash
python uniqlo_jp_checker_camoufox.py
```

---

## ⚙️ Config nhanh

Mở `config.json` và chỉnh:

```json
{
    "threads": 2,              // Số luồng (2-3 cho máy 8GB RAM)
    "camoufox_headless": false, // false = hiện browser, true = ẩn
    "use_proxy": true,         // true = dùng proxy, false = không
    "debug": true              // true = hiện logs, false = ẩn
}
```

---

## 📊 Kết quả

- ✅ **HITS** → Lưu vào `HITS.txt`
- ❌ **FAILED** → Lưu vào `failed.txt`
- 📝 **LOGS** → Lưu vào `checker.log`

---

## 🆘 Lỗi thường gặp

### "Chưa cài camoufox" hoặc "Chưa cài playwright"
```bash
pip install camoufox playwright
```

### "Browser failed to launch" hoặc "Firefox browser is NOT installed"
```bash
# Cài Firefox browser (BẮT BUỘC!)
playwright install firefox

# Hoặc cài lại force nếu bị lỗi
playwright install --force firefox
```

### "NotInstalledGeoIPExtra"
Lỗi này đã được fix trong code. Nếu vẫn gặp, update lại:
```bash
cd camou-ver
git pull  # hoặc tải lại code mới
```

### Proxy timeout
- Thử proxy khác
- Hoặc tắt proxy: `"use_proxy": false` trong config.json

---

## 💡 Tips

1. **Chạy lần đầu**: Để `debug: true` để xem logs
2. **Chạy nhiều acc**: Tăng `threads` nhưng cẩn thận RAM
3. **Proxy chậm**: Giảm số threads hoặc đổi proxy
4. **Muốn nhanh**: Bật `headless: true` (nhưng dễ bị phát hiện hơn)

---

**Chúc bạn check thành công! 🦊**

