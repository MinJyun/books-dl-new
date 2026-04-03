#!/usr/bin/env python3
"""
博客來電子書下載工具

使用方法:
1. 先至博客來購買電子書
2. 進入該書的閱讀頁面，取得網址列中的 book_id
   例如：https://viewer-ebook.books.com.tw/viewer/epub/web/?book_uni_id=E050017049_reflowable_normal
   book_uni_id= 之後的字串就是 book_id

注意：下載時請不要用瀏覽器操作博客來網站，該站電子書區有防多重登入。
"""

import sys
from books_dl import Downloader, convert_epub_to_pdf
from books_dl.converter import is_calibre_installed


def main():
    # 設定要下載的書籍 ID
    # 你可以在這裡修改 book_ids 列表，一次下載多本書
    book_ids = [
        'E050272147_reflowable_normal',
    ]
    
    # 是否轉換為 PDF (需要安裝 Calibre)
    convert_to_pdf = True
    
    if convert_to_pdf and not is_calibre_installed():
        print("⚠️  警告: 未偵測到 Calibre，將只下載 EPUB 不轉換 PDF")
        print("   請安裝 Calibre: https://calibre-ebook.com/download")
        print()
        convert_to_pdf = False
    
    for book_id in book_ids:
        print(f"\n{'=' * 50}")
        print(f"開始下載書籍: {book_id}")
        print('=' * 50)
        
        try:
            # 下載 EPUB
            downloader = Downloader(book_id)
            epub_path = downloader.download()
            
            # 轉換為 PDF
            if convert_to_pdf:
                print()
                try:
                    pdf_path = convert_epub_to_pdf(epub_path)
                except Exception as pdf_err:
                    print(f"⚠️  PDF 轉換失敗 (可能是圖片加密導致): {pdf_err}")
                    print(f"   但 EPUB 已成功下載: {epub_path}")
                


        except KeyboardInterrupt:
            print("\n\n已取消下載")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 下載失敗: {e}")
            continue


    
    print("\n🎉 所有書籍處理完成！")


if __name__ == '__main__':
    main()
