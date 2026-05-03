import requests
import re
import base64
import logging
import sys

# تنظیم لاگ برای دیباگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# آدرس فایل Sub.txt خودت
SUB_URL = "https://raw.githubusercontent.com/haniehzareie/Test/main/Sub.txt"
OUTPUT_FILE = "Confingonline.txt"

# پروتکل‌های V2Ray که باید پیدا بشن
PROTOCOLS = [
    "vmess://", "vless://", "trojan://", "ss://", "ssr://",
    "tuic://", "hysteria2://", "hysteria://", "hy2://"
]

def try_decode_base64(text):
    """تلاش برای decode base64 - خیلی از لینک‌ها base64 هستن"""
    try:
        # حذف کاراکترهای اضافی
        text = text.strip()
        # اضافه کردن padding اگر لازم باشه
        missing_padding = len(text) % 4
        if missing_padding:
            text += '=' * (4 - missing_padding)
        decoded = base64.b64decode(text).decode('utf-8', errors='ignore')
        return decoded
    except:
        return text

def extract_from_text(text):
    """استخراج کانفیگ‌ها از متن"""
    found = set()
    
    # اول کل متن رو امتحان میکنیم
    for proto in PROTOCOLS:
        pattern = proto + r'[^\s\"\'<>]+'
        matches = re.findall(pattern, text)
        found.update(matches)
    
    # اگه چیزی پیدا نشد، شاید base64 باشه
    if not found:
        decoded = try_decode_base64(text)
        if decoded != text:
            for proto in PROTOCOLS:
                pattern = proto + r'[^\s\"\'<>]+'
                matches = re.findall(pattern, decoded)
                found.update(matches)
    
    return found

def main():
    logging.info("="*50)
    logging.info("شروع جمع‌آوری کانفیگ‌های V2Ray")
    
    # 1. خوندن Sub.txt
    try:
        resp = requests.get(SUB_URL, timeout=30)
        resp.raise_for_status()
        links = [line.strip() for line in resp.text.splitlines() if line.strip().startswith('http')]
        logging.info(f"✅ {len(links)} لینک از Sub.txt دریافت شد")
    except Exception as e:
        logging.error(f"❌ خطا در دریافت Sub.txt: {e}")
        return
    
    all_configs = set()
    
    # 2. پردازش تک‌تک لینک‌ها
    for idx, url in enumerate(links, 1):
        logging.info(f"\n📡 [{idx}/{len(links)}] {url[:80]}")
        try:
            # با allow_redirects=True ریدایرکت‌ها رو دنبال کن
            r = requests.get(url, timeout=60, allow_redirects=True, 
                           headers={'User-Agent': 'Mozilla/5.0'})
            
            if r.status_code == 200:
                configs = extract_from_text(r.text)
                if configs:
                    logging.info(f"   ✅ {len(configs)} کانفیگ پیدا شد")
                    all_configs.update(configs)
                else:
                    logging.warning(f"   ⚠️ کانفیگی پیدا نشد - ۱۰۰ کاراکتر اول: {r.text[:100]}")
            else:
                logging.warning(f"   ⚠️ HTTP {r.status_code}")
        except requests.exceptions.Timeout:
            logging.error(f"   ❌ Timeout")
        except requests.exceptions.ConnectionError:
            logging.error(f"   ❌ خطای اتصال")
        except Exception as e:
            logging.error(f"   ❌ خطا: {e}")
    
    # 3. ذخیره نتیجه
    logging.info(f"\n{'='*50}")
    logging.info(f"📊 مجموع کانفیگ‌های یکتا: {len(all_configs)}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        if all_configs:
            for config in sorted(all_configs):
                f.write(config + '\n')
            logging.info(f"✅ ذخیره شد در {OUTPUT_FILE}")
        else:
            f.write("# هیچ کانفیگی یافت نشد\n")
            logging.warning("⚠️ فایل خالی ذخیره شد")

if __name__ == "__main__":
    main()
