"""扫描件 PDF OCR 工具 —— EasyOCR + 图像预处理增强"""
import sys
import os
import fitz  # PyMuPDF

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
import numpy as np


def preprocess_image(img: np.ndarray, level: str = "light") -> np.ndarray:
    """图像预处理：轻度去噪增强（可选，对清晰扫描件通常不需要）"""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    if level == "none":
        return gray

    # Light: 仅轻微去噪
    if level == "light":
        return cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Medium: 对比度增强 + 去噪
    if level == "medium":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

    return gray


def ocr_pdf(pdf_path: str, output_path: str = None, dpi: int = 300,
            preprocess_level: str = "none", keep_images: bool = False) -> str:
    """OCR 扫描件 PDF，输出文本"""
    import easyocr

    if output_path is None:
        output_path = pdf_path.replace(".pdf", "_ocr.txt")

    doc = fitz.open(pdf_path)
    total = doc.page_count
    reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
    all_results = []

    pre_label = {"none": "OCR", "light": "去噪+OCR", "medium": "增强+OCR"}[preprocess_level]
    print(f"📄 {os.path.basename(pdf_path)} — {total} 页 — EasyOCR — {pre_label}")

    for i in range(total):
        print(f"  第 {i+1}/{total} 页...", end=" ", flush=True)
        page = doc[i]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n).copy()

        if img.shape[2] == 4:  # RGBA → RGB
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

        processed = preprocess_image(img, level=preprocess_level)

        if keep_images:
            cv2.imwrite(f"{pdf_path}.page{i+1}.png", processed)

        ocr_result = reader.readtext(processed)
        page_lines = [(text, conf) for _, text, conf in ocr_result]
        all_results.append(page_lines)

        if keep_images:
            print(f"💾 {pdf_path}.page{i+1}.png", end=" ")

        char_count = sum(len(t[0]) for t in page_lines)
        print(f"→ {char_count} 字, {len(page_lines)} 行")

    doc.close()

    # 写输出
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# OCR: {os.path.basename(pdf_path)}\n")
        f.write(f"# 引擎: EasyOCR, DPI={dpi}, 预处理={preprocess_level}\n")
        f.write(f"# 共 {total} 页\n\n")
        for i, page_lines in enumerate(all_results):
            f.write(f"## 第 {i+1} 页\n\n")
            for text, _ in page_lines:
                f.write(f"{text}\n")
            f.write("\n")

    print(f"✅ → {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="扫描件 PDF OCR")
    p.add_argument("pdf", help="PDF 文件路径")
    p.add_argument("-o", "--output", help="输出文本路径")
    p.add_argument("-d", "--dpi", type=int, default=300)
    p.add_argument("--preprocess", choices=["none", "light", "medium"], default="none",
                   help="图像预处理级别: none=不处理, light=轻去噪, medium=对比度增强 (默认 none)")
    p.add_argument("--keep-images", action="store_true", help="保留预处理后的图片用于调试")
    args = p.parse_args()

    ocr_pdf(args.pdf, args.output, args.dpi,
            preprocess_level=args.preprocess,
            keep_images=args.keep_images)
