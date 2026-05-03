import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_sub_file(url):
    """دریافت محتوای یک ساب لینک"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, timeout=15, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"⚠️ خطا {resp.status_code}: {url}")
            return None
    except Exception as e:
        print(f"❌ نتونست وصل شه {url}: {str(e)}")
        return None

def extract_v2ray_configs(text):
    """استخراج کانفینگ‌های v2ray از متن خام"""
    patterns = [
        r'(vless://[A-Za-z0-9+@:./?=#&%_-]+)',
        r'(vmess://[A-Za-z0-9+/=]+)',
        r'(trojan://[A-Za-z0-9+@:./?=#&%_-]+)',
        r'(ss://[A-Za-z0-9+@:./?=#&%_-]+)',
        r'(socks://[A-Za-z0-9+@:./?=#&%_-]+)',
        r'(http://[A-Za-z0-9+@:./?=#&%_-]+)'
    ]
    all_configs = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        all_configs.extend(found)
    return list(dict.fromkeys(all_configs))  # حذف تکراری‌ها

def process_sub_link(url):
    """پردازش یک ساب لینک و برگردوندن کانفینگ‌هاش"""
    content = fetch_sub_file(url)
    if content:
        configs = extract_v2ray_configs(content)
        print(f"✅ از {url[:50]}... : {len(configs)} تا کانفینگ")
        return configs
    return []

def main(sub_file_path='sub_links.txt', output_file_path='v2ray_configs.txt'):
    # خوندن لینک‌های ساب از فایل
    with open(sub_file_path, 'r', encoding='utf-8') as f:
        sub_links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"📡 {len(sub_links)} تا ساب لینک پیدا شد")
    
    # اجرا همزمان با ترد (برای سرعت بیشتر)
    all_configs = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_sub_link, url): url for url in sub_links}
        for future in as_completed(futures):
            all_configs.extend(future.result())
    
    # حذف نهایی تکراری‌ها
    unique_configs = list(dict.fromkeys(all_configs))
    
    # نوشتن خروجی
    with open(output_file_path, 'w', encoding='utf-8') as f:
        if unique_configs:
            f.write('\n'.join(unique_configs))
            print(f"\n🎉 {len(unique_configs)} تا کانفینگ منحصر‌به‌فرد توی {output_file_path} ذخیره شد")
        else:
            f.write("# هیچ کانفینگ معتبری پیدا نشد")
            print("\n❌ هیچ کانفینگی پیدا نشد")
    
    return unique_configs

if __name__ == "__main__":
    main()
