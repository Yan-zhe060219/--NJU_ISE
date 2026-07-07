"""MinerU 文本提取脚本 — 高质量 PDF/文档解析，适合含公式、表格、图表、扫描件的复杂文档。

MinerU (magic-pdf v3) 是一站式高质量数据提取工具，相比 MarkItDown：
  - 公式 → LaTeX 格式保留
  - 表格 → Markdown 表格完整还原
  - 图表 → 识别并在 Markdown 中展示
  - 扫描件 → 自动 OCR（支持中英等多语言）
  - 页眉页脚 → 自动去除
  - 乱码 PDF → 自动识别处理

用法：
  python tools/mineru_extract.py <文件路径>            # 提取单个文件
  python tools/mineru_extract.py <文件夹>              # 提取该文件夹下所有 PDF
  python tools/mineru_extract.py <文件夹> --force      # 强制重新提取
  python tools/mineru_extract.py <文件夹> --single     # 只提取下一个未处理文件

输出: .md 保存在源文件所在目录的 .cache/ 子目录
进度: 记录在目标文件夹的 .mineru_extracted 文件
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CACHE_DIR = ".cache"
EXTRACTED_FILE_NAME = ".mineru_extracted"

# MinerU 支持的格式
MINERU_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg",
    ".docx", ".pptx", ".xlsx",
}

# conda 环境名
CONDA_ENV = "mineru"


def find_mineru() -> str | None:
    """查找 mineru 可执行文件路径。"""
    # 优先尝试 conda run
    try:
        result = subprocess.run(
            ["conda", "run", "-n", CONDA_ENV, "where", "mineru"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            paths = result.stdout.strip().splitlines()
            for p in paths:
                if p.endswith(".exe") or "mineru" in p:
                    return "conda"  # 使用 conda run 方式
    except Exception:
        pass

    # 直接查找已知路径
    known_paths = [
        Path(f"D:/Anaconda/envs/{CONDA_ENV}/Scripts/mineru.exe"),
    ]
    for p in known_paths:
        if p.exists():
            return str(p)

    return None


def run_mineru(file_path: Path, output_dir: Path, method: str = "auto",
               lang: str = "ch", effort: str = "medium") -> tuple[bool, str]:
    """调用 mineru 提取文件。返回 (成功, 消息)。"""
    temp_out = output_dir / f"_mineru_temp_{file_path.stem}"
    temp_out.mkdir(parents=True, exist_ok=True)

    mineru = find_mineru()
    if not mineru:
        return False, "mineru 未找到（请确认 conda env mineru 已安装）"

    # 默认使用 ModelScope 下载模型（国内网络 HuggingFace 不稳定）
    env = os.environ.copy()
    if "MINERU_MODEL_SOURCE" not in env:
        env["MINERU_MODEL_SOURCE"] = "modelscope"

    try:
        if mineru == "conda":
            cmd = [
                "conda", "run", "-n", CONDA_ENV,
                "mineru",
                "-p", str(file_path),
                "-o", str(temp_out),
                "-m", method,
                "-l", lang,
                "-b", "pipeline",
                "--effort", effort,
            ]
        else:
            cmd = [
                mineru,
                "-p", str(file_path),
                "-o", str(temp_out),
                "-m", method,
                "-l", lang,
                "-b", "pipeline",
                "--effort", effort,
            ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
            env=env,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"退出码 {result.returncode}"
            # 清理临时目录
            shutil.rmtree(temp_out, ignore_errors=True)
            return False, f"MinerU 失败: {error_msg[:200]}"

        # 查找 MinerU 生成的 markdown 文件
        md_files: list[Path] = []
        for root, _, files in temp_out.walk():
            for f in files:
                if f.endswith(".md") or f.endswith(".markdown"):
                    md_files.append(Path(root) / f)

        if not md_files:
            shutil.rmtree(temp_out, ignore_errors=True)
            return False, "MinerU 未生成任何 markdown 文件"

        # 取最大的 md 文件作为主输出（通常是完整文档）
        main_md = max(md_files, key=lambda f: f.stat().st_size)

        # 复制到目标位置
        target_md = output_dir / (file_path.stem + ".md")
        target_md.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(main_md, target_md)

        content_size = target_md.stat().st_size
        file_count = len(md_files)

        # 清理临时目录
        shutil.rmtree(temp_out, ignore_errors=True)

        return True, f"MinerU → {content_size} 字节 (共 {file_count} 个输出文件)"

    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_out, ignore_errors=True)
        return False, "MinerU 超时 (>600s)"
    except Exception as e:
        shutil.rmtree(temp_out, ignore_errors=True)
        return False, f"MinerU 异常: {e}"


def collect_files(search_root: Path) -> list[Path]:
    """收集需要提取的所有文件。"""
    files: list[Path] = []
    for ext in MINERU_EXTENSIONS:
        files.extend(sorted(search_root.rglob(f"*{ext}")))
        files.extend(sorted(search_root.rglob(f"*{ext.upper()}")))
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


def detect_lang_from_content(md_path: Path) -> str:
    """从已生成的 markdown 检测内容语言，用于日志。"""
    try:
        content = md_path.read_text(encoding="utf-8")[:5000]
        chinese_chars = sum(1 for c in content if '一' <= c <= '鿿')
        total_chars = sum(1 for c in content if c.isalpha())
        if total_chars > 0 and chinese_chars / total_chars > 0.1:
            return "ch"
        return "en"
    except Exception:
        return "ch"


def process_single(file_path: Path, force: bool, method: str,
                   lang: str, effort: str) -> str:
    """处理单个文件。"""
    cache_dir = file_path.parent / CACHE_DIR
    md_path = cache_dir / (file_path.stem + ".md")

    if md_path.exists() and not force:
        existing_size = md_path.stat().st_size
        return f"跳过（已有 .md, {existing_size} 字节）"

    start_time = time.time()
    ok, msg = run_mineru(file_path, cache_dir, method=method, lang=lang, effort=effort)
    elapsed = time.time() - start_time

    if ok:
        return f"✓ [{elapsed:.1f}s] {msg}"
    else:
        return f"✗ [{elapsed:.1f}s] {msg}"


def get_extracted_path(project_root: Path, search_root: Path) -> Path:
    """确定进度文件位置。"""
    inbox_root = project_root / "inbox"
    try:
        search_root.relative_to(inbox_root)
        return inbox_root / EXTRACTED_FILE_NAME
    except ValueError:
        return search_root / EXTRACTED_FILE_NAME


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MinerU 高质量文档解析 — 适合含公式、表格、图表的复杂 PDF"
    )
    parser.add_argument("target", nargs="?", default=None, help="文件或文件夹路径")
    parser.add_argument("--force", action="store_true", help="强制重新提取所有文件")
    parser.add_argument("--single", action="store_true", help="只提取下一个未处理的文件")
    parser.add_argument("-m", "--method", default="auto",
                        choices=["auto", "txt", "ocr"],
                        help="解析方法 (默认: auto)")
    parser.add_argument("-l", "--lang", default="ch",
                        help="文档语言，用于提升 OCR 精度 (默认: ch)")
    parser.add_argument("--effort", default="medium", choices=["medium", "high"],
                        help="解析精度: medium 更快, high 更准含图片分析 (默认: medium)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    if args.target:
        target = Path(args.target)
        if not target.is_absolute():
            target = project_root / target
    else:
        target = project_root / "inbox"

    if not target.exists():
        print(f"✗ 目标路径不存在: {target}")
        sys.exit(1)

    # 检查 mineru 是否可用
    mineru_path = find_mineru()
    if not mineru_path:
        print("✗ MinerU 未找到。请确保 conda 环境 'mineru' 已安装。")
        print("  安装命令: conda create -n mineru python=3.10 -y")
        print("           conda activate mineru")
        print("           pip install mineru[core]")
        sys.exit(1)

    # 确定搜索根目录和进度文件
    search_root = target if target.is_dir() else target.parent
    extracted_path = get_extracted_path(project_root, search_root)
    already = load_extracted(extracted_path)

    # --- 单文件模式 ---
    if not target.is_dir():
        if not args.force and target.name in already:
            print(f"跳过（已提取）: {target.name}")
            return
        rel = target.relative_to(project_root)
        print(f"MinerU 提取: {rel} ... ", end="", flush=True)
        result = process_single(target, args.force, args.method, args.lang, args.effort)
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

    type_counts: dict[str, int] = {}
    for f in to_process:
        ext = f.suffix.lower()
        type_counts[ext] = type_counts.get(ext, 0) + 1
    type_summary = ", ".join(f"{e}({n})" for e, n in sorted(type_counts.items()))

    print(f"发现 {len(files)} 个文件，待 MinerU 提取 {len(to_process)} 个")
    print(f"格式: {type_summary}")
    print(f"解析模式: method={args.method}, effort={args.effort}, lang={args.lang}\n")

    ok_count = 0
    for i, file_path in enumerate(to_process, 1):
        rel = file_path.relative_to(project_root)
        print(f"[{i}/{len(to_process)}] {rel} ... ", end="", flush=True)
        result = process_single(file_path, args.force, args.method, args.lang, args.effort)
        print(result)
        if result.startswith("✓"):
            ok_count += 1
        save_extracted(extracted_path, file_path.name)

    print(f"\n完成：{ok_count}/{len(to_process)} 个文件提取成功。")


if __name__ == "__main__":
    main()
