# 博客來電子書下載工具 (Python 版)

將博客來已購買的電子書下載為 EPUB 檔案，並可選擇轉換為 PDF。

## 安裝

```bash
# 安裝 Python 依賴
pip3 install -r requirements.txt

# (可選) 安裝 Calibre 以支援 EPUB 轉 PDF
# macOS: https://calibre-ebook.com/download_osx
# 或使用 Homebrew: brew install --cask calibre
```

## 使用方法

由於博客來閱讀器的機制限制，下載流程需要配合 Cookie 進行：

### 1. 取得 Cookie

1.  **開啟書籍**：在瀏覽器中開啟您想下載的電子書（進入閱讀頁面）。
2.  **複製 Cookie**：
    - 按 F12 開啟開發者工具 -> Network
    - 重新整理網頁，隨便點選一個請求（例如 `book.html` 或 XHR 請求）
    - 在右側 Headers 分頁找到 Request Headers
    - 複製 `Cookie:` 後面的全部內容

### 2. 更新 `cookie.txt`

1.  在專案目錄下找到 `cookie.txt` 檔案（若無則新建）。
2.  將複製的 Cookie 內容全部貼上並存檔。

### 3. 設定 Book ID 並執行

1.  **取得 Book ID**：
    - 觀察剛才閱讀頁面的網址，`book_uni_id=` 後面的字串即為 ID。
    - 例如：`E050181172_reflowable_normal`
2.  **修改 `main.py`**：
    - 將 `book_ids` 列表修改為該書的 ID。
3.  **執行下載**：
    - 執行 `python3 main.py`

程式啟動時會自動讀取 `cookie.txt` 並更新 `cookie.json`。

### ⚠️ 重要注意事項

- **一次處理一本**：請確保 `cookie.txt` 中的 Cookie 與 `main.py` 中的 Book ID 是**同一本書**。
- **Cookie 與 ID 必須對應**：博客來伺服器會優先根據 Cookie 中的 Session 來決定回傳哪本書的內容。如果您貼了 A 書的 Cookie 但 ID 寫 B 書，程式可能會下載到 A 書的內容，導致檔名與內容不符。

## 檔案結構

```
books-dl-new/
├── main.py              # 主程式入口
├── requirements.txt     # Python 依賴
├── cookie.txt           # 貼上 Cookie 的地方
├── cookie.json          # 程式自動產生的 Cookie 儲存檔
├── books_dl/
│   ├── __init__.py
│   ├── api.py           # API 呼叫與解密邏輯
│   ├── utils.py         # 加解密工具
│   ├── downloader.py    # 下載邏輯
│   └── converter.py     # EPUB 轉 PDF
└── README.md
```
