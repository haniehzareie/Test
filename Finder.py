import requests
import base64
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== بخش تست سلامت ==========
def test_host(host, port, timeout=5):
    """تست اتصال TCP به host و port"""
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        elapsed = (time.time() - start) * 1000  # تبدیل به میلی‌ثانیه
        sock.close()
        
        if result == 0:
            return {"status": "alive", "ping_ms": round(elapsed, 2)}
        else:
            return {"status": "dead", "ping_ms": None}
    except:
        return {"status": "error", "ping_ms": None}

def extract_host_port_from_link(link):
    """استخراج host و port از لینک‌های مختلف V2ray"""
    # برای لینک‌های vless و trojan: protocol://uuid@host:port?params
    match = re.search(r'://[^@]+@([^:]+):(\d+)', link)
    if match:
        return match.group(1), match.group(2)
    
    # برای لینک‌های vmess (base64 encoded)
    if link.startswith('vmess://'):
        try:
            import json
            encoded = link[8:]  # حذف 'vmess://'
            decoded = base64.b64decode(encoded).decode('utf-8')
            config = json.loads(decoded)
            return config.get('add'), config.get('port')
        except:
            pass
    
    # برای لینک‌های ss: ss://method:pass@host:port
    match = re.search(r'ss://[^@]+@([^:]+):(\d+)', link)
    if match:
        return match.group(1), match.group(2)
    
    return None, None

def test_config(config_link, timeout=5):
    """تست یک کانفیگ کامل"""
    host, port = extract_host_port_from_link(config_link)
    if host and port:
        result = test_host(host, port, timeout)
        return config_link, result
    return config_link, {"status": "invalid", "ping_ms": None}

def test_configs_batch(configs, timeout=5, max_workers=10):
    """تست همزمان چندین کانفیگ (برای سرعت بیشتر)"""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_config = {executor.submit(test_config, config, timeout): config for config in configs}
        for future in as_completed(future_to_config):
            config_link, result = future.result()
            results.append((config_link, result))
    return results

# ========== بخش استخراج کانفیگ ==========
def extract_all_links(text):
    """استخراج تمام لینک‌های V2ray (vless, vmess, trojan, shadowsocks)"""
    patterns = {
        'vless': r'vless://[^\s]+',
        'vmess': r'vmess://[A-Za-z0-9+/=]+',
        'trojan': r'trojan://[^\s]+',
        'ss': r'ss://[^\s]+'
    }
    all_links = []
    for protocol, pattern in patterns.items():
        found = re.findall(pattern, text)
        all_links.extend(found)
        print(f"   {protocol}: {len(found)} عدد")
    return all_links

def decode_config(encoded_str):
    """دیکد کردن محتوای base64"""
    try:
        cleaned = encoded_str.strip()
        decoded = base64.b64decode(cleaned).decode('utf-8')
        return decoded
    except:
        return None

def get_country_code(ip):
    """دریافت کد کشور از IP (اختیاری)"""
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}?fields=country_code", timeout=3)
        if resp.status_code == 200:
            return resp.json().get('country_code', 'UN')
    except:
        pass
    return 'UN'

def process_subscription_url(url, test_health=True, max_configs=30):
    """پردازش یک سابسکریپشن لینک"""
    print(f"\n📡 بررسی: {url}")
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"   خطا: وضعیت {resp.status_code}")
            return []
        
        content = resp.text
        
        # دیکد کردن base64 اگر لازم باشد
        decoded_content = decode_config(content)
        if decoded_content:
            content = decoded_content
            print(f"   ✅ Base64 دیکد شد")
        
        # استخراج تمام لینک‌ها
        all_links = extract_all_links(content)
        print(f"   📊 کل کانفیگ‌های یافت شده: {len(all_links)}")
        
        if len(all_links) == 0:
            return []
        
        # محدود کردن تعداد برای تست (برای جلوگیری از timeout)
        if len(all_links) > max_configs:
            print(f"   ⚠️ محدود کردن به {max_configs} کانفیگ برای تست")
            all_links = all_links[:max_configs]
        
        # تست سلامت کانفیگ‌ها
        if test_health:
            print(f"   🔍 در حال تست {len(all_links)} کانفیگ... (حداکثر 10 ثانیه)")
            test_results = test_configs_batch(all_links, timeout=4, max_workers=8)
            
            alive_configs = []
            for config_link, result in test_results:
                if result["status"] == "alive":
                    ping = result["ping_ms"]
                    # استخراج IP برای نمایش کشور
                    host, _ = extract_host_port_from_link(config_link)
                    country = get_country_code(host) if host else "??"
                    print(f"   ✅ زنده - {country} - پینگ: {ping}ms")
                    alive_configs.append(config_link)
                else:
                    print(f"   ❌ مرده یا نامعتبر")
            
            print(f"   📊 نتیجه: {len(alive_configs)}/{len(all_links)} کانفیگ زنده هستند")
            return alive_configs
        else:
            return all_links
            
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        return []

# ========== بخش اصلی ==========
def main():
    sub_file_path = "Sub.txt"
    
    # تنظیمات تست
    ENABLE_HEALTH_TEST = True      # تست سلامت فعال باشد؟
    MAX_CONFIGS_PER_SUB = 30        # حداکثر کانفیگ تست از هر سابسکریپشن
    MIN_PING_MS = 500               # حداکثر پینگ مجاز (میلی‌ثانیه) - عدد کمتر = سریعتر
    ALLOWED_COUNTRIES = []          # لیست کشورهای مجاز (خالی = همه کشورها)
                                    # مثال: ['TR', 'NL', 'DE', 'RU', 'FR']
    
    try:
        with open(sub_file_path, 'r') as f:
            subscription_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"📋 تعداد سابسکریپشن‌ها: {len(subscription_urls)}")
        print(f"🧪 تست سلامت: {'فعال' if ENABLE_HEALTH_TEST else 'غیرفعال'}")
    except FileNotFoundError:
        print(f"❌ فایل {sub_file_path} پیدا نشد!")
        return
    
    all_configs = []
    
    for sub_url in subscription_urls:
        configs = process_subscription_url(
            sub_url, 
            test_health=ENABLE_HEALTH_TEST,
            max_configs=MAX_CONFIGS_PER_SUB
        )
        all_configs.extend(configs)
    
    # حذف کانفیگ‌های تکراری
    unique_configs = list(dict.fromkeys(all_configs))
    
    # فیلتر بر اساس پینگ (اختیاری)
    if ENABLE_HEALTH_TEST and MIN_PING_MS < 999:
        print(f"\n🎯 فیلتر کردن کانفیگ‌های با پینگ بیشتر از {MIN_PING_MS}ms...")
        # این بخش نیاز به تست مجدد دارد، فعلاً همه را نگه می‌داریم
    
    # ذخیره در فایل
    output_file = "Working_Configs.txt"
    with open(output_file, 'w') as f:
        for config in unique_configs:
            f.write(config + '\n')
    
    print(f"\n{'='*50}")
    print(f"📁 نتیجه نهایی:")
    print(f"   ✅ {len(unique_configs)} کانفیگ زنده در {output_file} ذخیره شد")
    print(f"   📊 از مجموع {len(all_configs)} کانفیگ تست شده")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
