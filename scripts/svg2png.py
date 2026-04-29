"""
SVG -> PNG 変換スクリプト（Playwrightレンダリング）

CSSやWebフォントが効くようChromiumで実レンダリングしてキャプチャする。
単一SVG変換と、ディレクトリの一括変換に対応。

使い方:
    # 単一SVG変換（出力先指定）
    python svg2png.py ../images/svg/foo.svg -o ../images/png/foo.png

    # 単一SVG変換（出力先省略 → ../images/png/foo.png に保存）
    python svg2png.py ../images/svg/foo.svg

    # ../images/svg/ 配下を全部変換
    python svg2png.py --all

    # 高解像度（Retina相当）
    python svg2png.py ../images/svg/foo.svg --scale 2

    # 透過背景
    python svg2png.py ../images/svg/foo.svg --transparent

オプション:
    -o, --output         出力ファイルパス
    -d, --output-dir     出力ディレクトリ（デフォルト: ../images/png/）
    --all                ../images/svg/ 配下を一括変換
    --svg-dir            一括変換時の入力ディレクトリ（デフォルト: ../images/svg/）
    --scale FLOAT        デバイススケール（デフォルト 2 = Retina相当）
    --transparent        背景を透過にする（デフォルトは白背景）
    --padding INT        SVG周囲の余白px（デフォルト 0）
"""
import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SVG_DIR = ROOT / "images" / "svg"
DEFAULT_OUTPUT_DIR = ROOT / "images" / "png"


def build_html(svg_text: str, transparent: bool, padding: int) -> str:
    bg = "transparent" if transparent else "white"
    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<style>
  html, body {{ margin: 0; padding: {padding}px; background: {bg}; }}
  svg {{ display: block; }}
</style>
</head><body>{svg_text}</body></html>
"""


async def convert_one(page, svg_path: Path, png_path: Path, transparent: bool, padding: int):
    print(f"  -> {svg_path.name}")
    svg_text = svg_path.read_text(encoding="utf-8")
    await page.set_content(build_html(svg_text, transparent, padding))
    locator = page.locator("svg").first
    png_path.parent.mkdir(parents=True, exist_ok=True)
    await locator.screenshot(path=str(png_path), omit_background=transparent)
    print(f"     saved: {png_path}")


async def run(args):
    targets: list[tuple[Path, Path]] = []
    output_dir = Path(args.output_dir).resolve()

    if args.all:
        svg_dir = Path(args.svg_dir).resolve()
        for svg_path in sorted(svg_dir.glob("*.svg")):
            png_path = output_dir / (svg_path.stem + ".png")
            targets.append((svg_path, png_path))
        if not targets:
            print(f"no SVG files in {svg_dir}", file=sys.stderr)
            sys.exit(1)
    elif args.input:
        svg_path = Path(args.input).resolve()
        if not svg_path.exists():
            print(f"file not found: {svg_path}", file=sys.stderr)
            sys.exit(1)
        png_path = Path(args.output).resolve() if args.output else output_dir / (svg_path.stem + ".png")
        targets.append((svg_path, png_path))
    else:
        print("入力SVGか --all を指定してください", file=sys.stderr)
        sys.exit(2)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(device_scale_factor=args.scale)
        page = await context.new_page()
        print(f"[svg2png] {len(targets)} file(s)  scale={args.scale}x  transparent={args.transparent}")
        for svg_path, png_path in targets:
            try:
                await convert_one(page, svg_path, png_path, args.transparent, args.padding)
            except Exception as e:
                print(f"     ERROR: {e}", file=sys.stderr)
        await browser.close()
    print("[svg2png] done.")


def main():
    parser = argparse.ArgumentParser(description="SVG -> PNG 変換（Chromiumレンダリング）")
    parser.add_argument("input", nargs="?", help="入力SVGファイル")
    parser.add_argument("-o", "--output", help="出力PNGファイル")
    parser.add_argument("-d", "--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--all", action="store_true", help="入力ディレクトリの全SVGを変換")
    parser.add_argument("--svg-dir", default=str(DEFAULT_SVG_DIR))
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--transparent", action="store_true")
    parser.add_argument("--padding", type=int, default=0)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
