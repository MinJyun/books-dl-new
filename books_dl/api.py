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


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


class API:
    COOKIE_FILE = 'cookie.json'
    BOOK_DL_URL = 'https://appapi-ebook.books.com.tw/V1.7/CMSAPIApp/BookDownLoadURL'

    def __init__(self, book_id: str):
        self.book_id = book_id
        self.session = requests.Session()
        self.session.headers.update(self._default_headers())
        self.book_info = None
        self._load_cookies()

    def _default_headers(self) -> dict:
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

    @property
    def device_id(self) -> str:
        return self.session.cookies.get('device_id', '')

    def fetch(self, path: str) -> bytes:
        if not self.book_info:
            self.book_info = self._fetch_book_info()

        path = path.lstrip('/')
        url = f"{self.book_info.download_link.rstrip('/')}/{path}"
        content = self._download(url)

        if self.book_info.encrypt_type != 'enc01':
            return content

        tokens_to_try = []
        for cookie in self.session.cookies:
            if cookie.name == 'DownloadToken':
                val = _strip_quotes(str(cookie.value))
                if val not in tokens_to_try:
                    tokens_to_try.append(val)
        api_token = self.book_info.download_token
        if api_token and api_token not in tokens_to_try:
            tokens_to_try.append(api_token)

        last_error = None
        for token in tokens_to_try:
            try:
                key = utils.generate_key(url, token)
                decrypted = utils.decode_xor(key, content)
                if self._validate_decryption(path, decrypted):
                    return decrypted
            except Exception as e:
                last_error = e

        print(f"解密失敗 ({path}). Tried {len(tokens_to_try)} tokens. Last error: {last_error}")
        return content

    def _validate_decryption(self, path: str, content: bytes) -> bool:
        path_lower = path.lower()

        if path_lower.endswith(('.xml', '.xhtml', '.html', '.opf', '.ncx', '.css', '.js', '.json')):
            if path_lower.endswith(('.xml', '.opf', '.ncx', '.xhtml', '.html')):
                if not isinstance(content, (bytes, bytearray)):
                    try:
                        content = bytes(content)
                    except Exception:
                        return False
                ct_clean = content.strip()
                if ct_clean.startswith(b'\xef\xbb\xbf'):
                    ct_clean = ct_clean[3:]
                if not ct_clean.startswith(b'<'):
                    return False
            try:
                content.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False

        elif path_lower.endswith(('.jpg', '.jpeg')):
            return content.startswith(b'\xff\xd8')
        elif path_lower.endswith('.png'):
            return content.startswith(b'\x89PNG\r\n\x1a\n')
        elif path_lower.endswith('.gif'):
            return content.startswith(b'GIF8')
        elif path_lower.endswith('.woff'):
            return content.startswith(b'wOFF')
        elif path_lower.endswith('.woff2'):
            return content.startswith(b'wOF2')

        return True

    def _load_cookies(self) -> None:
        COOKIE_TXT_FILE = 'cookie.txt'
        try:
            with open(COOKIE_TXT_FILE) as f:
                cookie_str = f.read().strip()
            cookie_str = '\n'.join(
                line for line in cookie_str.splitlines()
                if not line.strip().startswith('#')
            ).strip()
            if cookie_str:
                print(f"偵測到 {COOKIE_TXT_FILE}，正在轉換...")
                cookies = self._parse_cookie_string(cookie_str)
                if cookies:
                    # Preserve device_id from existing cookie.json since it's not a browser cookie
                    if 'device_id' not in cookies:
                        try:
                            with open(self.COOKIE_FILE) as f:
                                old = json.load(f)
                            if 'device_id' in old:
                                cookies['device_id'] = old['device_id']
                        except (FileNotFoundError, json.JSONDecodeError):
                            pass
                    with open(self.COOKIE_FILE, 'w') as f:
                        json.dump(cookies, f, indent=2)
                    print(f"  已將 Cookie 儲存至 {self.COOKIE_FILE}")
                    with open(COOKIE_TXT_FILE, 'w') as f:
                        f.write("# Cookie 已轉換至 cookie.json\n# 如需更新，請貼上新的 Cookie 字串\n")
                    for name, value in cookies.items():
                        self.session.cookies.set(name, value)
                    return
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"  讀取 {COOKIE_TXT_FILE} 時發生錯誤: {e}")

        try:
            with open(self.COOKIE_FILE) as f:
                cookies = json.load(f)
            dirty = False
            for name, value in list(cookies.items()):
                if isinstance(value, str):
                    stripped = _strip_quotes(value)
                    if stripped != value:
                        cookies[name] = stripped
                        value = stripped
                        dirty = True
                self.session.cookies.set(name, value)
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
                cookies[name] = _strip_quotes(value)
        return cookies

    def _save_cookies(self) -> None:
        cookies = self.session.cookies.get_dict()
        with open(self.COOKIE_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)

    def _fetch_book_info(self) -> BookInfo:
        print("嘗試取得書籍資訊...")
        if not self.device_id:
            raise RuntimeError(
                "找不到 device_id。請確認 cookie.json 中有 device_id 欄位，"
                "或從瀏覽器 localStorage 取得後手動加入。"
            )
        url = f"{self.BOOK_DL_URL}?book_uni_id={self.book_id}&t={int(time.time())}&device_id={self.device_id}"
        try:
            resp = self._get(url)
            data = resp.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"API 回傳非 JSON 格式: {resp.text[:100]}")

        print(f"API 回應: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if 'error_code' in data:
            error_msg = data.get('error_message', 'Unknown error')
            if 'Device not Existed' in error_msg or data.get('error_code') == 'id_err_203':
                print("\n❌ 裝置驗證失敗 (Device not Existed)")
                print("請嘗試：")
                print("1. 在瀏覽器重新整理 Web Reader 頁面")
                print("2. 重新匯出 cookie.txt 到專案目錄")
                print(f"3. 確認 localStorage.device_id 為: {self.device_id}")
                raise RuntimeError(f"裝置驗證失敗: {error_msg}")
            if data['error_code'] != '000':
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

    def _get(self, url: str, allow_redirects: bool = True) -> requests.Response:
        resp = self.session.get(url, allow_redirects=allow_redirects)
        if resp.status_code >= 400:
            filename = url.split('/')[-1].split('?')[0]
            raise RuntimeError(f"取得 `{filename}` 失敗。Status: {resp.status_code}")
        if resp.cookies:
            self._save_cookies()
        return resp

    def _download(self, url: str) -> bytes:
        print(f"下載檔案: {url}")
        try:
            resp = self._get(url)
            content = resp.content
            preview = content[:512].lower()
            if len(content) < 500 or b'error' in preview or b'html' in preview:
                print(f"檔案內容預覽 (前 200 bytes): {content[:200]}")
            return content
        except Exception as e:
            print(f"下載失敗: {e}")
            raise
