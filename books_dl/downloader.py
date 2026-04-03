"""EPUB downloader for books.com.tw."""

import os
import zipfile
from pathlib import Path
from typing import Optional

from lxml import etree

from .api import API


def _strip_namespaces(doc) -> None:
    for elem in doc.iter():
        if isinstance(elem.tag, str) and elem.tag.startswith('{'):
            elem.tag = elem.tag.split('}', 1)[1]


class Downloader:
    """Downloads and packages ebooks as EPUB files."""

    def __init__(self, book_id: str, output_dir: str = '.'):
        self.book_id = book_id
        self.output_dir = Path(output_dir)
        self.api = API(book_id)

        self.files: list[tuple[str, bytes]] = []
        self.root_file_path: Optional[str] = None
        self._root_doc = None
        self.title: Optional[str] = None

    def download(self) -> str:
        """Download the book and create EPUB file. Returns path to the EPUB."""
        existing_files = list(self.output_dir.glob(f"{self.book_id}*.epub"))
        if existing_files:
            epub_path = existing_files[0]
            print(f"\n偵測到已存在的 EPUB: {epub_path}")
            if self._is_valid_epub(epub_path):
                print(f"✅ EPUB 驗證完整，跳過下載")
                return str(epub_path)
            print(f"❌ EPUB 檔案損毀或不完整，將重新下載...")

        self.files.append(('mimetype', b'application/epub+zip'))

        self._job('取得 META-INF/container.xml', self._fetch_container)
        self._job('取得 META-INF/encryption.xml', self._fetch_encryption)
        self._job(f'取得 {self.root_file_path}', self._fetch_root_file)
        self._fetch_content()

        epub_path = self._build_epub()
        print(f"\n✅ {self.book_id} 下載完成: {epub_path}")
        return epub_path

    def _job(self, name: str, func) -> bool:
        print(f"正在{name}...", end='', flush=True)
        try:
            func()
            print('成功')
            return True
        except Exception as e:
            print(f'失敗: {e}')
            return False

    def _fetch_container(self) -> None:
        path = 'META-INF/container.xml'
        content = self.api.fetch(path)
        self.files.append((path, content))

        doc = etree.fromstring(content)
        ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfiles = doc.xpath('//c:rootfile/@full-path', namespaces=ns)
        if not rootfiles:
            rootfiles = doc.xpath('//rootfile/@full-path')
        if rootfiles:
            self.root_file_path = rootfiles[0]

    def _fetch_encryption(self) -> None:
        path = 'META-INF/encryption.xml'
        content = self.api.fetch(path)
        self.files.append((path, content))

    def _fetch_root_file(self) -> None:
        if not self.root_file_path:
            raise ValueError("root_file_path not set")

        content = self.api.fetch(self.root_file_path)
        self.files.append((self.root_file_path, content))

        doc = etree.fromstring(content)
        _strip_namespaces(doc)
        self._root_doc = doc

        title_elem = doc.find('.//title')
        if title_elem is not None and title_elem.text:
            self.title = title_elem.text

    def _fetch_content(self) -> None:
        if not self._root_doc:
            return

        base_dir = os.path.dirname(self.root_file_path)
        items = self._root_doc.findall('.//item')
        total = len(items)

        for i, item in enumerate(items):
            href = item.get('href')
            if not href:
                continue
            file_path = os.path.normpath(f"{base_dir}/{href}" if base_dir else href)
            print(f"{i + 1}/{total} => 開始下載 {file_path}")
            try:
                content = self.api.fetch(file_path)
                self.files.append((file_path, content))
            except Exception as e:
                print(f"  ⚠️ 下載失敗: {e}")

    def _build_epub(self) -> str:
        title = self.title or self.book_id
        safe_title = "".join(c for c in title if c.isalnum() or c in ' -_').strip()
        filename = f"{self.book_id}_{safe_title}.epub"
        filepath = self.output_dir / filename

        print(f"\n正在製作 EPUB 檔案: {filename}...")

        with zipfile.ZipFile(filepath, 'w') as zf:
            for path, content in self.files:
                compress = zipfile.ZIP_STORED if path == 'mimetype' else zipfile.ZIP_DEFLATED
                zf.writestr(path, content, compress_type=compress)

        return str(filepath)

    def _is_valid_epub(self, filepath: Path) -> bool:
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if zf.testzip() is not None:
                    return False
                if 'META-INF/container.xml' not in zf.namelist():
                    return False
            return True
        except (zipfile.BadZipFile, OSError):
            return False
