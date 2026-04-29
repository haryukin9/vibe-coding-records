"""
画面キャプチャスクリプト（Playwrightヘッドレス）

ブックマーク・タブ・拡張機能などは映らない（ヘッドレスChrome相当）。
URLを1つだけ撮るモードと、URLリストファイルから一括で撮るモードがある。

使い方:
    # 単一URLを撮る（出力先指定）
    python capture.py https://example.com -o ../images/png/example.png

    # 単一URL（出力先未指定 → ../images/png/ に自動命名で保存）
    python capture.py https://example.com

    # フルページ（縦長全体）で撮る
    python capture.py https://example.com --full-page

    # 一括キャプチャ（urls.txt に1行1URL）
    python capture.py --batch urls.txt

    # 解像度・スケール指定（Retina相当=2）
    python capture.py https://example.com --width 1440 --height 900 --scale 2

オプション:
    -o, --output       出力ファイルパス（省略時は自動命名）
    -d, --output-dir   出力ディレクトリ（デフォルト: ../images/png/）
    --batch FILE       URLリストファイル（1行1URL、#でコメント）
    --full-page        ページ全体（縦長）を撮る
    --width INT        ビューポート幅（デフォルト 1440）
    --height INT       ビューポート高さ（デフォルト 900）
    --scale FLOAT      デバイススケール（デフォルト 2 = Retina相当）
    --wait-ms INT      キャプチャ前の待機ミリ秒（デフォルト 800）
"""
import argparse
import asyncio
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

DEFAULT_OUTPUT_DIR = Path("J:/マイドライブ/AI_support_Projects/playwright-captures")


def slugify_url(url: str) -> str:
    """URL から PNG のファイル名を作る"""
    p = urlparse(url)
    host = p.hostname or "site"
    path = p.path.strip("/").replace("/", "-") or "index"
    base = f"{host}-{path}"
    base = re.sub(r"[^\w\-.]", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")
    return base[:80]


def resolve_output_path(url: str, output: str | None, output_dir: Path) -> Path:
    if output:
        return Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return output_dir / f"{stamp}_{slugify_url(url)}.png"


async def capture_one(
    page,
    url: str,
    out_path: Path,
    full_page: bool,
    wait_ms: int,
):
    print(f"  -> {url}")
    await page.goto(url, wait_until="networkidle", timeout=60_000)
    if wait_ms > 0:
        await page.wait_for_timeout(wait_ms)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(out_path), full_page=full_page)
    print(f"     saved: {out_path}")


async def run(args):
    urls: list[tuple[str, str | None]] = []
    if args.batch:
        batch_file = Path(args.batch)
        for line in batch_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append((line, None))
    elif args.url:
        urls.append((args.url, args.output))
    else:
        print("URLか --batch のどちらかを指定してください", file=sys.stderr)
        sys.exit(2)

    output_dir = Path(args.output_dir).resolve()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale,
        )
        page = await context.new_page()

        print(f"[capture] {len(urls)} URL(s)  full_page={args.full_page}  size={args.width}x{args.height}@{args.scale}x")
        for url, explicit_out in urls:
            out_path = resolve_output_path(url, explicit_out, output_dir)
            try:
                await capture_one(page, url, out_path, args.full_page, args.wait_ms)
            except Exception as e:
                print(f"     ERROR: {e}", file=sys.stderr)

        await browser.close()
    print("[capture] done.")


def main():
    parser = argparse.ArgumentParser(
        description="Playwrightで画面キャプチャを取る（ヘッドレス・装飾なし）",
    )
    parser.add_argument("url", nargs="?", help="撮影するURL")
    parser.add_argument("-o", "--output", help="出力ファイルパス")
    parser.add_argument("-d", "--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="出力ディレクトリ")
    parser.add_argument("--batch", help="URLリストファイル（1行1URL）")
    parser.add_argument("--full-page", action="store_true", help="ページ全体（縦長）")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--wait-ms", type=int, default=800)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
