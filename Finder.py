import requests
import base64
import re

print("🚀 اسکریپت شروع شد")

def extract_all_links(text):
    """استخراج تمام لینک‌های V2ray"""
    patterns = {
        'vless': r'vless://[^\s]+',
        'vmess': r'vmess://[A-Za-z0-9+/=]+',
        'trojan': r'trojan://[^\s]+',
        'ss': r'ss://[^\s]+'
    }
    links = []
    for protocol, pattern in patterns.items():
        found = re.findall(pattern, text)
        links.extend(found)
        if found:
            print(f"   🔍 {protocol}: {len(found)} عدد")
    return links

def test_single_url(url):
    """تست یک لینک سابسکریپشن"""
    print(f"\n📡 بررسی: {url}")
    try:
        resp = requests.get(url, timeout=20)
        print(f"   وضعیت: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"   ❌ خطا: دسترسی غیرمجاز یا لینک مرده")
            return []
        
        content = resp.text
        print(f"   طول محتوا: {len(content)} کاراکتر")
        
        # تلاش برای دیکد base64
        try:
            decoded = base64.b64decode(content.strip()).decode('utf-8')
            content = decoded
            print(f"   ✅ محتوا Base64 بود و دیکد شد")
        except:
            print(f"   ℹ️ محتوا Base64 نیست یا نیازی به دیکد ندارد")
        
        # استخراج لینک‌ها
        links = extract_all_links(content)
        print(f"   📊 مجموع کانفیگ‌های این سابسکریپشن: {len(links)}")
        
        # نمایش نمونه
        if links:
            print(f"   نمونه: {links[0][:80]}...")
        
        return links
        
    except Exception as e:
        print(f"   ❌ خطای غیرمنتظره: {str(e)}")
        return []

def main():
    # خواندن Sub.txt
    try:
        with open("Sub.txt", 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"📋 تعداد سابسکریپشن‌های بارگذاری شده: {len(urls)}")
    except FileNotFoundError:
        print("❌ فایل Sub.txt پیدا نشد!")
        return
    
    all_configs = []
    
    for url in urls:
        configs = test_single_url(url)
        all_configs.extend(configs)
    
    # حذف تکراری‌ها
    unique_configs = list(dict.fromkeys(all_configs))
    
    # ذخیره نتایج
    output_file = "Germany_vless.txt"
    with open(output_file, 'w') as f:
        for config in unique_configs:
            f.write(config + '\n')
    
    print(f"\n✅ کار تمام شد!")
    print(f"📊 مجموع کانفیگ‌های منحصربفرد: {len(unique_configs)}")
    print(f"💾 ذخیره شده در: {output_file}")

if __name__ == "__main__":
    main()
