"""统一文件提取脚本 — MarkItDown 优先，失败回退到 extract_pdfs.py / extract_pptx.py。

用法：
  python tools/extract_file.py <文件夹>            # 提取该文件夹下所有支持的文件
  python tools/extract_file.py <文件夹> --force    # 强制重新提取
  python tools/extract_file.py <文件夹> --single   # 只提取下一个未处理的文件
  python tools/extract_file.py <文件路径>           # 提取单个文件

支持的格式（MarkItDown）：
  PDF, PPTX, DOCX, XLSX/XLS, 图片(jpg/png/gif/bmp/webp),
  HTML, CSV, JSON, XML, IPYNB, EPUB

输出: .txt 保存在源文件所在目录的 .cache/ 子目录
进度: 记录在目标文件夹的 .extracted 文件
"""

import argparse
import subprocess
import sys
from pathlib import Path

CACHE_DIR = ".cache"
EXTRACTED_FILE_NAME = ".extracted"

# MarkItDown 支持的格式
MARKITDOWN_EXTENSIONS = {
    ".pdf", ".pptx", ".docx", ".xlsx", ".xls",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".html", ".htm",
    ".csv", ".json", ".xml",
    ".ipynb", ".epub",
}

# 有回退脚本的格式（MarkItDown 失败时使用）
LEGACY_FALLBACK = {
    ".pdf": "extract_pdfs.py",
    ".pptx": "extract_pptx.py",
}


def collect_files(search_root: Path) -> list[Path]:
    """收集需要提取的所有文件。"""
    files: list[Path] = []
    for ext in MARKITDOWN_EXTENSIONS:
        files.extend(sorted(search_root.rglob(f"*{ext}")))
        files.extend(sorted(search_root.rglob(f"*{ext.upper()}")))
    # 去重（按文件名，因为同一个课程文件夹内文件名唯一）
    seen: set[str] = set()
    result: list[Path] = []
    for f in sorted(files):
        if f.name not in seen:
            seen.add(f.name)
            result.append(f)
    return result


def load_extracted(extracted_path: Path) -> set[str]:
    """加载已提取文件列表。"""
    if extracted_path.exists():
        return {
            line.strip()
            for line in extracted_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    return set()


def save_extracted(extracted_path: Path, filename: str) -> None:
    """记录已提取的文件。"""
    extracted_path.parent.mkdir(parents=True, exist_ok=True)
    with open(extracted_path, "a", encoding="utf-8") as f:
        f.write(filename + "\n")


def extract_via_markitdown(file_path: Path, txt_path: Path) -> tuple[bool, str]:
    """通过 markitdown CLI 提取文本。返回 (成功, 消息)。"""
    try:
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["markitdown", str(file_path), "-o", str(txt_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and txt_path.exists():
            content = txt_path.read_text(encoding="utf-8").strip()
            if len(content) > 10:
                return True, f"MarkItDown ({len(content)} 字)"
            else:
                return False, "MarkItDown 输出过短"
        return False, (
            f"MarkItDown 失败: {result.stderr[:80] if result.stderr else '退出码 ' + str(result.returncode)}"
        )
    except FileNotFoundError:
        return False, "markitdown CLI 未安装"
    except subprocess.TimeoutExpired:
        return False, "MarkItDown 超时"
    except Exception as e:
        return False, f"MarkItDown 异常: {e}"


def extract_via_legacy(file_path: Path, txt_path: Path, script_dir: Path) -> tuple[bool, str]:
    """回退到 extract_pdfs.py 或 extract_pptx.py。"""
    ext = file_path.suffix.lower()
    script_name = LEGACY_FALLBACK.get(ext)
    if not script_name:
        return False, f"无回退脚本（格式 {ext}）"

    script_path = script_dir / script_name
    if not script_path.exists():
        return False, f"回退脚本不存在: {script_name}"

    # 回退脚本只处理单个文件，输出到 <parent>/.cache/<stem>.txt
    legacy_txt = file_path.parent / CACHE_DIR / (file_path.stem + ".txt")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(file_path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if legacy_txt.exists():
            content = legacy_txt.read_text(encoding="utf-8").strip()
            if len(content) > 10:
                # 如果回退脚本的输出位置与目标不同，复制过去
                if legacy_txt.resolve() != txt_path.resolve():
                    txt_path.parent.mkdir(parents=True, exist_ok=True)
                    txt_path.write_text(content, encoding="utf-8")
                return True, f"回退 → {script_name} ({len(content)} 字)"
        return False, (
            f"回退无输出: {result.stderr[:80] if result.stderr else '-'}"
        )
    except subprocess.TimeoutExpired:
        return False, "回退脚本超时"
    except Exception as e:
        return False, f"回退异常: {e}"


def process_single(file_path: Path, force: bool, script_dir: Path) -> str:
    """处理单个文件: MarkItDown 优先 → 回退（如果存在）。"""
    cache_dir = file_path.parent / CACHE_DIR
    txt_path = cache_dir / (file_path.stem + ".txt")

    if txt_path.exists() and not force:
        existing = txt_path.read_text(encoding="utf-8").strip()
        return f"跳过（已有 .txt, {len(existing)} 字）"

    # 1) 尝试 MarkItDown
    ok, msg = extract_via_markitdown(file_path, txt_path)

    if ok:
        return f"✓ {msg}"

    # 2) MarkItDown 失败 → 如果该格式有回退脚本则回退
    ext = file_path.suffix.lower()
    if ext in LEGACY_FALLBACK:
        ok2, msg2 = extract_via_legacy(file_path, txt_path, script_dir)
        if ok2:
            return f"✓ {msg2}"
        return f"✗ MarkItDown: {msg} | 回退: {msg2}"

    # 3) 无回退脚本 → 失败
    return f"✗ {msg}（无回退方案）"


def get_extracted_path(project_root: Path, search_root: Path) -> Path:
    """确定 .extracted 文件的位置。

    如果 search_root 在 inbox/ 下，沿用 inbox/.extracted（兼容旧脚本）；
    否则使用 search_root/.extracted。
    """
    inbox_root = project_root / "inbox"
    try:
        search_root.relative_to(inbox_root)
        return inbox_root / EXTRACTED_FILE_NAME
    except ValueError:
        return search_root / EXTRACTED_FILE_NAME


def get_legacy_extracted(project_root: Path) -> set[str]:
    """读取旧脚本的进度文件，合并到新系统中。"""
    legacy_files = [
        project_root / "inbox" / ".extracted",       # extract_pdfs.py
        project_root / "inbox" / ".extracted_pptx",  # extract_pptx.py
    ]
    entries: set[str] = set()
    for lf in legacy_files:
        if lf.exists():
            for line in lf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    entries.add(line)
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="统一文件文本提取 — MarkItDown 优先，回退到 extract_pdfs/extract_pptx"
    )
    parser.add_argument("target", nargs="?", default=None, help="课程文件夹路径或单个文件")
    parser.add_argument("--force", action="store_true", help="强制重新提取所有文件")
    parser.add_argument("--single", action="store_true", help="只提取下一个未处理的文件")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    script_dir = project_root / "tools"

    if args.target:
        target = Path(args.target)
        if not target.is_absolute():
            target = project_root / target
    else:
        target = project_root / "inbox"

    if not target.exists():
        print(f"✗ 目标路径不存在: {target}")
        sys.exit(1)

    # 确定搜索根目录和进度文件
    if target.is_dir():
        search_root = target
    else:
        # 单文件模式
        search_root = target.parent

    extracted_path = get_extracted_path(project_root, search_root)
    already = load_extracted(extracted_path)

    # 合并旧脚本的进度（首次运行时避免重复提取）
    legacy_entries = get_legacy_extracted(project_root)
    already |= legacy_entries

    # --- 单文件模式 ---
    if not target.is_dir():
        if not args.force and target.name in already:
            print(f"跳过（已提取）: {target.name}")
            return
        rel = target.relative_to(project_root)
        print(f"提取: {rel} ... ", end="", flush=True)
        result = process_single(target, args.force, script_dir)
        print(result)
        if result.startswith("✓"):
            save_extracted(extracted_path, target.name)
        return

    # --- 目录模式 ---
    files = collect_files(search_root)

    if args.single:
        for f in files:
            if f.name not in already:
                files = [f]
                break
        else:
            print("所有文件均已提取，无需处理。")
            return

    to_process = [f for f in files if f.name not in already] if not args.force else files

    if not to_process:
        print("没有新文件需要提取。")
        return

    # 统计文件类型
    type_counts: dict[str, int] = {}
    for f in to_process:
        ext = f.suffix.lower()
        type_counts[ext] = type_counts.get(ext, 0) + 1
    type_summary = ", ".join(f"{e}({n})" for e, n in sorted(type_counts.items()))

    print(f"发现 {len(files)} 个文件，待提取 {len(to_process)} 个")
    print(f"格式: {type_summary}\n")

    ok_count = 0
    for i, file_path in enumerate(to_process, 1):
        rel = file_path.relative_to(project_root)
        print(f"[{i}/{len(to_process)}] {rel} ... ", end="", flush=True)
        result = process_single(file_path, args.force, script_dir)
        print(result)
        if result.startswith("✓"):
            ok_count += 1
        save_extracted(extracted_path, file_path.name)

    print(f"\n完成：{ok_count}/{len(to_process)} 个文件提取成功。")


if __name__ == "__main__":
    main()
