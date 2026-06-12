"""预处理 inbox/ 中的 PDF —— 先用 pdfplumber 提取文本，扫描件自动回退到 EasyOCR。

用法：
  python tools/extract_pdfs.py                     # 处理 inbox 下全部 PDF
  python tools/extract_pdfs.py inbox/OS            # 处理指定课程文件夹
  python tools/extract_pdfs.py --force inbox/OS    # 强制重新提取（覆盖已有 .txt）
  python tools/extract_pdfs.py --single inbox/OS   # 只提取下一个未处理的（供 /learn 自动调用）
  python tools/extract_pdfs.py <任意路径>/xxx.pdf  # 处理单个 PDF（可不在 inbox 内）

输出：生成 .txt 在 PDF 所在目录的 .cache/ 子目录；进度记录在 inbox/.extracted
扫描件页面的 OCR 文本末尾会带 [OCR] 标记，方便 AI 判断是否为高置信度文本。
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

# 抑制 OpenMP 冲突警告（PyTorch + Anaconda 常见问题）
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
warnings.filterwarnings("ignore")

import numpy as np

import fitz
import pdfplumber

CACHE_DIR = ".cache"

# 扫描件检测：一页 pdfplumber 提取的文本少于此字符数，且页面包含图片，则触发 OCR
SCAN_THRESHOLD_CHARS = 30

# OCR 全局单例，延迟初始化
_ocr_reader = None


def get_ocr_reader():
    """延迟初始化 EasyOCR reader（模型加载较慢，只做一次）。"""
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    return _ocr_reader


def is_scanned_page(page_text: str, pdfplumber_page) -> bool:
    """判断一页是否为扫描件（无文本层或文本极少 + 包含图片）。"""
    text_len = len(page_text.strip())
    if text_len >= SCAN_THRESHOLD_CHARS:
        return False
    # 检查是否包含图片对象（pdfplumber 的 page.images）
    images = getattr(pdfplumber_page, "images", [])
    return len(images) > 0 and text_len < SCAN_THRESHOLD_CHARS


def ocr_page(page_num: int, fitz_page) -> str:
    """用 EasyOCR 识别单页扫描件。"""
    reader = get_ocr_reader()
    pix = fitz_page.get_pixmap(dpi=200)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    results = reader.readtext(img)
    if not results:
        return ""
    lines = []
    for (_, text, _) in results:
        lines.append(text)
    return "\n".join(lines)


def extract_text(pdf_path: Path) -> str:
    """提取 PDF 全文，扫描件页面自动回退到 EasyOCR。"""
    # 用 pdfplumber 和 fitz 同时打开（fitz 用于渲染扫描件页面）
    with pdfplumber.open(str(pdf_path)) as pdf:
        fitz_doc = fitz.open(str(pdf_path))
        pages = []

        for i in range(len(pdf.pages)):
            # 先用 pdfplumber 提取文本
            text = pdf.pages[i].extract_text() or ""

            if is_scanned_page(text, pdf.pages[i]):
                # 扫描件回退：用 EasyOCR
                try:
                    ocr_text = ocr_page(i, fitz_doc[i])
                    if ocr_text.strip():
                        pages.append(
                            f"--- 第 {i + 1} 页 [OCR] ---\n{ocr_text}"
                        )
                    else:
                        pages.append(
                            f"--- 第 {i + 1} 页 [OCR 失败：未检测到文本] ---"
                        )
                except Exception as e:
                    pages.append(
                        f"--- 第 {i + 1} 页 [OCR 失败: {e}] ---"
                    )
            elif text.strip():
                pages.append(f"--- 第 {i + 1} 页 ---\n{text}")
            else:
                pages.append(f"--- 第 {i + 1} 页 [空白] ---")

        fitz_doc.close()
        return "\n\n".join(pages)


def load_extracted(extracted_path: Path) -> set[str]:
    if extracted_path.exists():
        return {
            line.strip()
            for line in extracted_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    return set()


def save_extracted(extracted_path: Path, entry: str) -> None:
    with open(extracted_path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def process_single(pdf_path: Path, force: bool) -> str:
    cache_dir = pdf_path.parent / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    txt_path = cache_dir / (pdf_path.stem + ".txt")

    if txt_path.exists() and not force:
        return "跳过（已有 .txt）"

    try:
        text = extract_text(pdf_path)
        txt_path.write_text(text, encoding="utf-8")
        # 统计 OCR 页数
        ocr_count = text.count("[OCR]")
        if ocr_count > 0:
            return f"完成（{ocr_count} 页扫描件已 OCR）"
        return "完成"
    except Exception as e:
        return f"失败: {e}"


def collect_pdfs(root: Path, pattern: str | None) -> list[Path]:
    if pattern:
        target = Path(pattern)
        if target.is_file():
            return [target]
        return sorted(target.rglob("*.pdf"))
    return sorted(root.rglob("*.pdf"))


def main():
    parser = argparse.ArgumentParser(description="从 inbox 中提取 PDF 文本（扫描件自动 OCR）")
    parser.add_argument("target", nargs="?", default=None, help="课程文件夹或单个 PDF")
    parser.add_argument("--force", action="store_true", help="强制重新提取，覆盖已有 .txt")
    parser.add_argument("--single", action="store_true", help="只处理下一篇未提取的文件（供 /learn 自动调用）")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    inbox_root = project_root / "inbox"
    extracted_file = inbox_root / ".extracted"

    if args.target:
        candidate = Path(args.target)
        if not candidate.is_absolute():
            candidate = project_root / candidate
    else:
        candidate = inbox_root

    pdfs = collect_pdfs(
        candidate if candidate.is_dir() else inbox_root,
        str(candidate) if candidate.is_file() else None,
    )

    already = load_extracted(extracted_file)

    if args.single:
        for pdf in pdfs:
            if pdf.name not in already:
                pdfs = [pdf]
                break
        else:
            print("所有文件均已提取，无需处理。")
            return

    to_process = [p for p in pdfs if p.name not in already] if not args.force else pdfs

    if not to_process:
        print("没有新的 PDF 需要提取。")
        return

    print(f"共 {len(pdfs)} 个 PDF，待提取 {len(to_process)} 个\n")

    for i, pdf in enumerate(to_process, 1):
        rel = pdf.relative_to(project_root)
        print(f"[{i}/{len(to_process)}] {rel} ... ", end="", flush=True)
        result = process_single(pdf, args.force)
        print(result)
        # 用 PDF 文件名（非全路径）记录，匹配 inbox 内去重
        save_extracted(extracted_file, pdf.name)

    print(f"\n全部完成。提取的文本已保存为同名 .txt 文件。")


if __name__ == "__main__":
    main()
