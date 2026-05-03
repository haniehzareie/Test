def extract_all_from_sub():
    try:
        # خوندن فایل Sub.txt
        with open("Sub.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # گرفتن همه خطوط غیرخالی
        all_configs = []
        for line in lines:
            line = line.strip()
            if line:  # اگه خط خالی نباشه
                all_configs.append(line)
        
        # نوشتن توی configonline.txt
        with open("configonline.txt", "w", encoding="utf-8") as f:
            f.write("# ========== ALL CONFIGS FROM Sub.txt ==========\n")
            f.write(f"# Total: {len(all_configs)} configs\n")
            f.write("# =============================================\n\n")
            
            for i, config in enumerate(all_configs, 1):
                f.write(f"{i}. {config}\n")
        
        print(f"✅ Done! {len(all_configs)} configs copied to configonline.txt")
        return True
        
    except FileNotFoundError:
        print("❌ ERROR: Sub.txt not found!")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    extract_all_from_sub()
