"""EPUB downloader for books.com.tw."""

import os
import zipfile
from pathlib import Path
from typing import Optional

from lxml import etree

from .api import API


class Downloader:
    """Downloads and packages ebooks as EPUB files."""
    
    def __init__(self, book_id: str, output_dir: str = '.'):
        self.book_id = book_id
        self.output_dir = Path(output_dir)
        self.api = API(book_id)
        
        self.files: list[tuple[str, bytes]] = []
        self.root_file_path: Optional[str] = None
        self.title: Optional[str] = None
    
    def download(self) -> str:
        """
        Download the book and create EPUB file.
        Returns the path to the created EPUB file.
        """
        # Check if file exists (using pattern book_id*.epub)
        existing_files = list(self.output_dir.glob(f"{self.book_id}*.epub"))
        if existing_files:
            # Pick the first one found
            epub_path = existing_files[0]
            print(f"\n偵測到已存在的 EPUB: {epub_path}")
            
            if self._is_valid_epub(epub_path):
                print(f"✅ EPUB 驗證完整，跳過下載")
                return str(epub_path)
            else:
                print(f"❌ EPUB 檔案損毀或不完整，將重新下載...")
                # Optional: Remove invalid file
                # os.remove(epub_path)

        # Add mimetype first (must be uncompressed)
        self.files.append(('mimetype', b'application/epub+zip'))
        
        self._job('取得 META-INF/container.xml', self._fetch_container)
        self._job('取得 META-INF/encryption.xml', self._fetch_encryption)
        self._job(f'取得 {self.root_file_path}', self._fetch_root_file)
        self._fetch_content()
        
        epub_path = self._build_epub()
        print(f"\n✅ {self.book_id} 下載完成: {epub_path}")
        return epub_path
    
    def _job(self, name: str, func) -> bool:
        """Execute a job with status output."""
        print(f"正在{name}...", end='', flush=True)
        try:
            result = func()
            print('成功')
            return result
        except Exception as e:
            print(f'失敗: {e}')
            return False
    
    def _fetch_container(self) -> bool:
        """Fetch and parse container.xml."""
        path = 'META-INF/container.xml'
        content = self.api.fetch(path)
        self.files.append((path, content))
        
        # Parse to get root file path
        doc = etree.fromstring(content)
        ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfiles = doc.xpath('//c:rootfile/@full-path', namespaces=ns)
        if rootfiles:
            self.root_file_path = rootfiles[0]
        else:
            # Try without namespace
            rootfiles = doc.xpath('//rootfile/@full-path')
            if rootfiles:
                self.root_file_path = rootfiles[0]
        
        return True
    
    def _fetch_encryption(self) -> bool:
        """Fetch encryption.xml (optional file)."""
        try:
            path = 'META-INF/encryption.xml'
            content = self.api.fetch(path)
            self.files.append((path, content))
            return True
        except Exception as e:
            print(f"\n  (encryption.xml 不存在，跳過: {e})")
            return False
    
    def _fetch_root_file(self) -> bool:
        """Fetch the root file (content.opf)."""
        if not self.root_file_path:
            raise ValueError("root_file_path not set")
        
        content = self.api.fetch(self.root_file_path)
        self.files.append((self.root_file_path, content))
        
        # Parse for title and file list
        doc = etree.fromstring(content)
        
        # Get title
        # Remove namespaces for easier parsing

        for elem in doc.iter():
            if not isinstance(elem.tag, str):
                continue
            if elem.tag.startswith('{'):
                elem.tag = elem.tag.split('}', 1)[1]

        
        title_elem = doc.find('.//title')
        if title_elem is not None and title_elem.text:
            self.title = title_elem.text
        
        return True
    
    def _fetch_content(self) -> None:
        """Fetch all content files listed in the root file."""
        if not self.root_file_path:
            return
        
        # Re-parse root file for items
        root_content = None
        for path, content in self.files:
            if path == self.root_file_path:
                root_content = content
                break
        
        if not root_content:
            return
        
        doc = etree.fromstring(root_content)
        
        # Get base directory
        base_dir = os.path.dirname(self.root_file_path)
        
        # Find all items (remove namespace for xpath)

        for elem in doc.iter():
            if not isinstance(elem.tag, str):
                continue
            if elem.tag.startswith('{'):
                elem.tag = elem.tag.split('}', 1)[1]

        
        items = doc.findall('.//item')
        total = len(items)
        
        for i, item in enumerate(items):
            href = item.get('href')
            if not href:
                continue
            
            # Construct full path
            if base_dir:
                file_path = f"{base_dir}/{href}"
            else:
                file_path = href
            
            # Normalize path (handle ../ etc)
            file_path = os.path.normpath(file_path)
            
            print(f"{i + 1}/{total} => 開始下載 {file_path}")
            try:
                content = self.api.fetch(file_path)
                self.files.append((file_path, content))
            except Exception as e:
                print(f"  ⚠️ 下載失敗: {e}")
    
    def _build_epub(self) -> str:
        """Build the EPUB file from downloaded content."""
        title = self.title or self.book_id
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in ' -_').strip()
        filename = f"{self.book_id}_{safe_title}.epub"
        filepath = self.output_dir / filename
        
        print(f"\n正在製作 EPUB 檔案: {filename}...")
        
        with zipfile.ZipFile(filepath, 'w') as zf:
            for path, content in self.files:
                if path == 'mimetype':
                    # mimetype must be first and uncompressed
                    zf.writestr(path, content, compress_type=zipfile.ZIP_STORED)
                else:
                    zf.writestr(path, content, compress_type=zipfile.ZIP_DEFLATED)
        
        return str(filepath)

    def _is_valid_epub(self, filepath: Path) -> bool:
        """Check if the EPUB file is valid and not corrupt."""
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Check for bad zip file
                if zf.testzip() is not None:
                    return False
                
                # Check for required container file
                if 'META-INF/container.xml' not in zf.namelist():
                    return False
                
            return True
        except (zipfile.BadZipFile, OSError):
            return False
