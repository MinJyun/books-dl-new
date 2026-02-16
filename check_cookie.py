
import json
import requests
from books_dl.api import API

def check_cookie():
    # 1. Load cookies
    print("載入 Cookie...")
    api = API('test_id')
    
    # 2. Check basic login status
    print(f"Cookie 數量: {len(api.session.cookies)}")
    print(f"CmsToken: {api.session.cookies.get('CmsToken')}")
    print(f"DownloadToken: {api.session.cookies.get('DownloadToken')}")
    
    try:
        print("\n嘗試存取購物車頁面...")
        resp = api.session.get(API.CART_URL, allow_redirects=False)
        print(f"Status Code: {resp.status_code}")
        print(f"Location: {resp.headers.get('Location')}")
        
        if resp.status_code == 200:
            if 'logout' in resp.text.lower() or '登出' in resp.text:
                print("✅ 狀態：已登入！")
            else:
                print("❌ 狀態：未登入 (找不到登出連結)")
        elif resp.status_code in (302, 303):
            if 'login' in resp.headers.get('Location', '').lower():
                print("❌ 狀態：未登入 (被導向登入頁)")
            else:
                print(f"⚠️ 狀態：未知導向 ({resp.headers.get('Location')})")
        else:
             print(f"⚠️ 狀態：異常 ({resp.status_code})")

    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    check_cookie()
