"""EPUB to PDF converter using Calibre's ebook-convert."""

import subprocess
import shutil
from pathlib import Path


def convert_epub_to_pdf(epub_path: str, output_path: str = None) -> str:
    """
    Convert an EPUB file to PDF using Calibre's ebook-convert.
    
    Args:
        epub_path: Path to the EPUB file
        output_path: Optional output PDF path. If not provided,
                     uses the same name as the EPUB with .pdf extension.
    
    Returns:
        Path to the created PDF file.
    
    Raises:
        RuntimeError: If Calibre is not installed or conversion fails.
    """
    epub_path = Path(epub_path)
    
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    # Determine output path
    if output_path:
        pdf_path = Path(output_path)
    else:
        pdf_path = epub_path.with_suffix('.pdf')
    
    # Find ebook-convert
    ebook_convert = _find_ebook_convert()
    if not ebook_convert:
        raise RuntimeError(
            "找不到 Calibre 的 ebook-convert 工具。\n"
            "請先安裝 Calibre: https://calibre-ebook.com/download\n"
            "macOS 安裝後，ebook-convert 通常在:\n"
            "  /Applications/calibre.app/Contents/MacOS/ebook-convert"
        )
    
    print(f"正在轉換 EPUB 為 PDF...")
    print(f"  輸入: {epub_path}")
    print(f"  輸出: {pdf_path}")
    
    try:
        result = subprocess.run(
            [
                ebook_convert,
                str(epub_path),
                str(pdf_path),
                '--pdf-page-numbers',
                '--paper-size', 'a4',
                '--pdf-default-font-size', '20',
                '--pdf-mono-font-size', '16',
                '--margin-top', '20',
                '--margin-bottom', '20',
                '--margin-left', '20',
                '--margin-right', '20',
                '--output-profile', 'kindle',
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        if pdf_path.exists():
            print(f"✅ PDF 轉換完成: {pdf_path}")
            return str(pdf_path)
        else:
            raise RuntimeError("PDF 檔案未產生")
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"PDF 轉換失敗:\n{e.stderr}")


def _find_ebook_convert() -> str:
    """Find the ebook-convert executable."""
    # Check common locations on macOS
    mac_paths = [
        '/Applications/calibre.app/Contents/MacOS/ebook-convert',
        '/usr/local/bin/ebook-convert',
    ]
    
    for path in mac_paths:
        if Path(path).exists():
            return path
    
    # Try to find in PATH
    result = shutil.which('ebook-convert')
    if result:
        return result
    
    return None


def is_calibre_installed() -> bool:
    """Check if Calibre is installed."""
    return _find_ebook_convert() is not None
