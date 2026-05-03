import requests
import re
import os
import base64
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUB_FILE_URL = "https://raw.githubusercontent.com/haniehzareie/Test/main/Sub.txt"
OUTPUT_FILE = "Confingonline.txt"

# پروتکل‌های معتبر
VALID_PROTOCOLS = [
    "vmess://", "vless://", "trojan://", "ss://", "ssr://",
    "tuic://", "hysteria2://", "hysteria://", "wg://", "hy2://"
]

def is_base64(s):
    """تشخیص اینکه رشته base64 هست یا نه"""
    try:
        decoded = base64.b64decode(s, validate=True)
        return True
    except:
        return False

def extract_configs_from_text(text):
    """استخراج کانفیگ‌ها از متن خام، با پشتیبانی از base64"""
    configs = set()
    lines = text.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # اگر خودش مستقیم کانفیگ باشه
        if any(line.startswith(proto) for proto in VALID_PROTOCOLS):
            configs.add(line)
            continue
        
        # اگر base64 باشه، decode کن و دوباره بررسی کن
        try:
            decoded_bytes = base64.b64decode(line)
            decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
            # حالا توی متن decode شده دنبال کانفیگ بگرد
            found = re.findall(r'(?:vmess|vless|trojan|ss|ssr|tuic|hysteria2?|hy2|wg)://[^\s]+', decoded_str)
            for c in found:
                configs.add(c)
        except:
            pass
    
    return configs

def fetch_configs():
    logging.info("=" * 60)
    logging.info("شروع فرآیند جمع‌آوری کانفیگ‌ها...")
    
    # 1. دریافت لینک‌های Sub
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; ConfigBot/1.0)'}
    try:
        response = requests.get(SUB_FILE_URL, timeout=30, headers=headers)
        response.raise_for_status()
        sub_links = [line.strip() for line in response.text.splitlines() if line.strip() and line.startswith('http')]
        logging.info(f"✅ {len(sub_links)} لینک معتبر از Sub.txt دریافت شد:")
        for i, link in enumerate(sub_links, 1):
            logging.info(f"   {i}. {link}")
    except Exception as e:
        logging.error(f"❌ خطا در دریافت Sub.txt: {e}")
        return

    all_configs = set()
    failed_links = []
    empty_links = []

    # 2. بررسی تک‌تک لینک‌ها
    for idx, url in enumerate(sub_links, 1):
        logging.info(f"\n📡 [{idx}/{len(sub_links)}] بررسی: {url[:80]}...")
        try:
            resp = requests.get(url, timeout=60, allow_redirects=True, headers=headers)
            
            if resp.status_code != 200:
                logging.warning(f"   ⚠️ پاسخ HTTP {resp.status_code} - رد شد")
                failed_links.append((url, f"HTTP {resp.status_code}"))
                continue
            
            content = resp.text
            if not content or len(content.strip()) < 5:
                logging.warning(f"   ⚠️ محتوای خالی - رد شد")
                empty_links.append(url)
                continue
            
            # استخراج کانفیگ‌ها
            configs = extract_configs_from_text(content)
            
            if configs:
                logging.info(f"   ✅ {len(configs)} کانفیگ معتبر استخراج شد")
                all_configs.update(configs)
            else:
                logging.warning(f"   ⚠️ هیچ کانفیگی پیدا نشد (اولین ۱۰۰ کاراکتر: {content[:100]})")
                empty_links.append(url)
                
            time.sleep(0.5)  # فاصله بین درخواست‌ها برای جلوگیری از rate limit
            
        except requests.exceptions.Timeout:
            logging.error(f"   ❌ Timeout - رد شد")
            failed_links.append((url, "Timeout"))
        except requests.exceptions.SSLError:
            logging.error(f"   ❌ خطای SSL - رد شد")
            failed_links.append((url, "SSL Error"))
        except requests.exceptions.ConnectionError:
            logging.error(f"   ❌ خطای اتصال - رد شد")
            failed_links.append((url, "Connection Error"))
        except Exception as e:
            logging.error(f"   ❌ خطا: {type(e).__name__}: {str(e)[:100]}")
            failed_links.append((url, str(e)[:100]))

    # 3. گزارش نهایی
    logging.info("\n" + "=" * 60)
    logging.info("📊 گزارش نهایی:")
    logging.info(f"   • کل لینک‌ها: {len(sub_links)}")
    logging.info(f"   • لینک‌های موفق: {len(sub_links) - len(failed_links)}")
    logging.info(f"   • لینک‌های ناموفق: {len(failed_links)}")
    logging.info(f"   • لینک‌های خالی: {len(empty_links)}")
    logging.info(f"   • مجموع کانفیگ‌های یکتا: {len(all_configs)}")
    
    if failed_links:
        logging.info("\n   لینک‌های ناموفق:")
        for link, reason in failed_links:
            logging.info(f"   - {link[:80]} ({reason})")

    # 4. ذخیره‌سازی
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            if all_configs:
                for config in sorted(all_configs):
                    f.write(config + "\n")
                logging.info(f"\n✅ فایل {OUTPUT_FILE} با {len(all_configs)} کانفیگ ذخیره شد.")
            else:
                f.write("# هیچ کانفیگ فعالی یافت نشد\n")
                logging.warning(f"\n⚠️ فایل {OUTPUT_FILE} خالی ذخیره شد (هیچ کانفیگی پیدا نشد).")
    except Exception as e:
        logging.error(f"❌ خطا در نوشتن فایل: {e}")

if __name__ == "__main__":
    fetch_configs()
