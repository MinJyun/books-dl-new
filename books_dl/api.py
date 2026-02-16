import requests
import json
import time
from dataclasses import dataclass
from . import utils

@dataclass
class BookInfo:
    book_uni_id: str
    download_link: str
    download_token: str
    size: int
    encrypt_type: str

class API:
    """Books.com.tw Ebook API Client (Web Reader Mimic)"""
    
    # Constants
    COOKIE_FILE = 'cookie.json'
    # User provided Device ID from browser localStorage
    KNOWN_DEVICE_ID = 'FD4A9B66-683C-4A3C-81A0-DE2F9A3492AA'
    
    # API Endpoints
    CART_URL = 'https://db.books.com.tw/shopping/cart_list.php'
    BOOK_DL_URL = 'https://appapi-ebook.books.com.tw/V1.7/CMSAPIApp/BookDownLoadURL'
    DEVICE_REG_URL = 'https://appapi-ebook.books.com.tw/V1.7/CMSAPIApp/DeviceReg'
    
    def __init__(self, book_id: str):
        self.book_id = book_id
        self.session = requests.Session()
        self.session.headers.update(self._default_headers())
        self.book_info = None
        self._load_cookies()

    def _default_headers(self) -> dict:
        # Mimic Web Reader Headers
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://viewer-ebook.books.com.tw',
            'Referer': 'https://viewer-ebook.books.com.tw/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
    
    def fetch(self, path: str) -> bytes:
        """Fetch a file from the book content."""
        if not self.book_info:
            self.book_info = self._fetch_book_info()
        
        # Ensure path doesn't start with slash
        if path.startswith('/'):
            path = path[1:]
        
        # Fix: avoid double-slash by stripping trailing slash from download_link
        base_url = self.book_info.download_link.rstrip('/')
        url = f"{base_url}/{path}"

        content = self.download_file(url)
        
        # Decrypt if enc01
        if self.book_info.encrypt_type == 'enc01':
            # Get tokens to try: Cookie Token (preferred for cached content) and API Token
            tokens_to_try = []
            




            # 1. Cookie Token(s)
            # Handle multiple cookies with same name safely
            for cookie in self.session.cookies:
                if cookie.name == 'DownloadToken':
                    try:
                        print(f"DEBUG: Found DownloadToken cookie. Type: {type(cookie)}")
                        print(f"DEBUG: Cookie value type: {type(cookie.value)}")
                        print(f"DEBUG: Cookie value repr: {repr(cookie.value)}")
                        
                        val = str(cookie.value)
                        if val.startswith('"') and val.endswith('"'):
                            val = val[1:-1]
                        if val not in tokens_to_try:
                            tokens_to_try.append(val)
                    except Exception as e:
                        print(f"DEBUG: Error processing cookie: {e}")
                        import traceback
                        traceback.print_exc()



            
            # 2. API Token

            api_token = self.book_info.download_token
            if api_token and api_token not in tokens_to_try:
                tokens_to_try.append(api_token)
            
            last_error = None
            for token in tokens_to_try:
                try:
                    key = utils.generate_key(url, token)
                    decrypted = utils.decode_xor(key, content)
                    
                    # Validate decryption
                    if self._validate_decryption(path, decrypted):
                        # print(f"Decryption successful  for {path} using token: {token[:10]}...")
                        return decrypted
                except Exception as e:
                    last_error = e
            
            print(f"解密失敗 ({path}). Tried {len(tokens_to_try)} tokens. Last error: {last_error}")
            # print(f"Tokens tried: {[t[:10] for t in tokens_to_try]}")
            return content
        
        return content

    def _validate_decryption(self, path: str, content: bytes) -> bool:
        """Validate if decrypted content looks correct based on file extension."""
        path_lower = path.lower()
        
        # Text/XML files
        if path_lower.endswith(('.xml', '.xhtml', '.html', '.opf', '.ncx', '.css', '.js', '.json')):
            # XML should start with <



            if path_lower.endswith(('.xml', '.opf', '.ncx', '.xhtml', '.html')):
                # Check for < but ignore whitespace/BOM
                # SAFETY: Ensure content is bytes
                if not isinstance(content, (bytes, bytearray)):
                    try:
                        content = bytes(content)
                    except Exception:
                        return False
                
                ct_clean = content.strip()
                # Remove BOM if present
                if ct_clean.startswith(b'\xef\xbb\xbf'):
                    ct_clean = ct_clean[3:]
                
                if not ct_clean.startswith(b'<'):
                    return False



            
            # Should be valid UTF-8
            try:
                content.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
                
        # Images
        elif path_lower.endswith('.jpg') or path_lower.endswith('.jpeg'):
            return content.startswith(b'\xff\xd8')
        elif path_lower.endswith('.png'):
            return content.startswith(b'\x89PNG\r\n\x1a\n')
        elif path_lower.endswith('.gif'):
            return content.startswith(b'GIF8')
            
        # Fonts
        elif path_lower.endswith('.woff'):
            return content.startswith(b'wOFF')
        elif path_lower.endswith('.woff2'):
            return content.startswith(b'wOF2')
            
        # Default: assume valid if we didn't fail specific checks
        # Maybe check for high entropy or garbage? 
        # But random binary files passed as 'enc01' might just rely on key.
        return True

        
        return content

    def _load_cookies(self) -> None:
        """Load cookies from file. Supports both cookie.txt (raw string) and cookie.json."""
        COOKIE_TXT_FILE = 'cookie.txt'
        
        # Check if cookie.txt has a valid cookie string
        try:
            with open(COOKIE_TXT_FILE, 'r') as f:
                cookie_str = f.read().strip()
            
            # Skip if it's just a comment or empty
            if cookie_str and not cookie_str.startswith('#'):
                print(f"偵測到 {COOKIE_TXT_FILE}，正在轉換...")
                cookies = self._parse_cookie_string(cookie_str)
                
                if cookies:
                    # Save to cookie.json
                    with open(self.COOKIE_FILE, 'w') as f:
                        json.dump(cookies, f, indent=2)
                    print(f"  已將 Cookie 儲存至 {self.COOKIE_FILE}")
                    
                    # Clear cookie.txt after successful conversion
                    with open(COOKIE_TXT_FILE, 'w') as f:
                        f.write("# Cookie 已轉換至 cookie.json\n# 如需更新，請貼上新的 Cookie 字串\n")
                    
                    # Load into session
                    for name, value in cookies.items():
                        self.session.cookies.set(name, value)
                    
                    # Inject device_id into cookies
                    print(f"  注入 device_id: {self.KNOWN_DEVICE_ID}")
                    self.session.cookies.set('device_id', self.KNOWN_DEVICE_ID)
                    return
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"  讀取 {COOKIE_TXT_FILE} 時發生錯誤: {e}")
        
        # Fallback: load from cookie.json
        try:
            with open(self.COOKIE_FILE, 'r') as f:
                cookies = json.load(f)
                # Clean up quotes if present in loaded json
                dirty = False
                for name, value in list(cookies.items()):
                    if isinstance(value, str) and len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                        cookies[name] = value
                        dirty = True
                    self.session.cookies.set(name, value)
                
                # Inject device_id
                self.session.cookies.set('device_id', self.KNOWN_DEVICE_ID)
                
                # If we fixed any quotes, save back to file
                if dirty:
                    print("自動修復 cookie.json 中的格式問題...")
                    with open(self.COOKIE_FILE, 'w') as f:
                        json.dump(cookies, f, indent=2)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _parse_cookie_string(self, cookie_str: str) -> dict:
        cookies = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                # Strip quotes from value if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                cookies[name] = value
        return cookies

    def _save_cookies(self) -> None:
        """Save current session cookies to file."""
        cookies = self.session.cookies.get_dict()
        with open(self.COOKIE_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)

    def login(self) -> None:
        """Check login status, raise error if not logged in."""
        if self._is_logged_in():
            print("已登入（使用儲存的 Cookie）")
            # print cookie length for debug
            print(f"Cookie 數量: {len(self.session.cookies)}")
            return
            
        print("\n❌ 登入驗證失敗！")
        print("目前的 Cookie 已失效或無法使用。")
        print(f"請重新登入博客來，並將新的 Cookie 貼上覆蓋 `{self.COOKIE_FILE}` 的內容。")
        raise RuntimeError("Cookie 失效，請更新 cookie.json")

    def _is_logged_in(self) -> bool:
        """Check if currently logged in by checking if we can access cart."""
        try:
            resp = self.session.get(self.CART_URL, allow_redirects=False)
            
            # If redirected to login page, we're not logged in
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get('Location', '')
                if 'login' in location.lower():
                    return False
            
            # Check if response contains login form or redirect
            if resp.status_code == 200:
                content = resp.text.lower()
                # If the page contains logout link, we're logged in
                if 'logout' in content or '登出' in content:
                    return True
                # If it contains login form, we're not logged in
                if 'login_id' in content or '會員登入' in content:
                    return False
                    
            # If cookie is valid, we usually get 200 on cart
            return True
        except Exception:
            return False

    def get_book_info(self) -> BookInfo:
        """Public method to get book info."""
        return self._fetch_book_info()

    def _fetch_book_info(self) -> BookInfo:
        """Fetch book download information."""
        print("嘗試取得書籍資訊...")
        
        # Add timestamp and device_id to URL
        url = f"{self.BOOK_DL_URL}?book_uni_id={self.book_id}&t={int(time.time())}&device_id={self.KNOWN_DEVICE_ID}"
        
        try:
            resp = self._get(url)
            data = resp.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"API 回傳非 JSON 格式: {resp.text[:100]}")
        
        # Debug: show API response
        print(f"API 回應: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if 'error_code' in data:
            error_msg = data.get('error_message', 'Unknown error')
            if 'Device not Existed' in error_msg or 'id_err_203' in data.get('error_code', ''):
                print("\n❌ 錯誤: 裝置驗證失敗 (Device not Existed)")
                print("這通常表示您的 Cookie 已過期，或 Device ID 不匹配。")
                print("請嘗試：")
                print("1. 在瀏覽器重新整理 Web Reader 頁面")
                print("2. 重新匯出 cookie.txt 到專案目錄")
                print(f"3. 確保 localStorage.device_id 為: {self.KNOWN_DEVICE_ID}")
                raise RuntimeError(f"裝置驗證失敗: {error_msg}")
            
            if 'error_code' in data and data['error_code'] != '000':
                 raise RuntimeError(f"API 錯誤: {data}")
        
        if not data.get('download_link'):
            raise RuntimeError(f"無法取得下載連結。API 回應: {data}")
        
        return BookInfo(
            book_uni_id=data.get('book_uni_id', ''),
            download_link=data.get('download_link', ''),
            download_token=data.get('download_token', ''),
            size=data.get('size', 0),
            encrypt_type=data.get('encrypt_type', '')
        )

    def _register_web_device(self) -> bool:
        """Register as a Web Reader device using known device_id."""
        
        # Use user provided device_id
        device_id = self.KNOWN_DEVICE_ID
        
        # Add device_id to URL as well
        url = f"{self.DEVICE_REG_URL}?device_id={device_id}"
        
        # Web Reader Registration Payload
        # Validated via test_device_reg.py
        payload = {
            'device_id': device_id,
            'device_model': 'web',
            'device_vendor': 'Google Inc.',
            'device_type': 'web',
            'device_os': 'Mac OS X',
            'os_version': '10.15.7',
            'app_version': 'BROWSER',
            'language': 'zh-TW',
            'country': 'TW',
            'screen_width': '1920',
            'screen_height': '1080',
            'screen_dpi': '72',
            'screen_resolution': '1920x1080',
            'os_type': 'WEB'
        }
        
        try:
            print(f"傳送 Web 裝置註冊請求 (ID: {device_id})...")
            # Use a FRESH session (requests.post) to avoid cookie poisoning
            # The current session's cookies (like invalid CmsToken) might be causing "Device not Existed"
            resp = requests.post(url, data=payload, headers=self._default_headers())
            data = resp.json()
            print(f"Web DeviceReg 回應: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('error_code') == '000' or data.get('success'):
                # Extract CmsToken
                cms_token = data.get('CmsToken') or data.get('cms_token')
                if cms_token:
                    print(f"取得新的 CmsToken: {cms_token[:10]}...")
                    self.session.cookies.set('CmsToken', cms_token)
                
                # Update cookies file
                self._save_cookies()
                return True
            return False
        except Exception as e:
            print(f"Web DeviceReg 失敗: {e}")
            return False
    
    def _get(self, url: str, allow_redirects: bool = True) -> requests.Response:
        resp = self.session.get(url, allow_redirects=allow_redirects)
        if resp.status_code >= 400:
            filename = url.split('/')[-1].split('?')[0]
            raise RuntimeError(f"取得 `{filename}` 失敗。Status: {resp.status_code}")
        self._save_cookies()
        return resp

    def _post(self, url: str, data: dict = None, allow_redirects: bool = True) -> requests.Response:
        resp = self.session.post(url, data=data, allow_redirects=allow_redirects)
        if resp.status_code >= 400:
            filename = url.split('/')[-1].split('?')[0]
            raise RuntimeError(f"POST `{filename}` 失敗。Status: {resp.status_code}")
        self._save_cookies()
        return resp
        
    def download_file(self, url: str) -> bytes:
        """Download file content."""
        # Use session to keep cookies
        print(f"下載檔案: {url}")
        try:
            resp = self._get(url)
            content = resp.content
            # Debug: print first 100 bytes if it looks like an error (small size or not xml)
            if len(content) < 500 or b'error' in content.lower() or b'html' in content.lower():
                print(f"檔案內容預覽 (前 200 bytes): {content[:200]}")
            return content
        except Exception as e:
            print(f"下載失敗: {e}")
            raise
