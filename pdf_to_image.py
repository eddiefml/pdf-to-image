import argparse
import io
import os
import sys

import fitz
from PIL import Image


def parse_pages(s):
    """Parse a page spec string like '1-3,5,7-9' into a list of 1-indexed page numbers.

    Returns None if s is empty or None (meaning all pages).
    """
    if not s or not s.strip():
        return None
    pages = []
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return pages


def convert_pdf(input_path, output_dir, fmt, quality, prefix,
                height=None, width=None, pages=None, compress=False,
                progress_callback=None):
    """Convert PDF pages to image files.

    Args:
        input_path: Path to the PDF file.
        output_dir: Directory to write images into.
        fmt: 'jpg' or 'png'.
        quality: JPEG quality 1-100 (ignored for PNG).
        prefix: Output filename prefix.
        height: Output height in pixels (None = auto from width or original).
        width: Output width in pixels (None = auto from height or original).
        pages: List of 1-indexed page numbers, or None for all pages.
        progress_callback: Optional callable(current_page, total).

    Returns:
        List of output file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    ext = fmt
    pil_fmt = "JPEG" if ext == "jpg" else "PNG"

    doc = fitz.open(input_path)
    all_pages = list(range(1, len(doc) + 1))

    if pages:
        target_pages = [p for p in pages if 1 <= p <= len(doc)]
    else:
        target_pages = all_pages

    total = len(target_pages)
    out_paths = []

    for idx, page_num in enumerate(target_pages):
        page = doc[page_num - 1]
        page_w = page.rect.width
        page_h = page.rect.height

        if width is not None and height is not None:
            scale_x = width / page_w
            scale_y = height / page_h
        elif width is not None:
            scale_x = scale_y = width / page_w
        elif height is not None:
            scale_x = scale_y = height / page_h
        else:
            # Both empty: use original dimensions (1 point = 1 pixel at 72 DPI)
            scale_x = scale_y = 1.0

        pix = page.get_pixmap(matrix=fitz.Matrix(scale_x, scale_y))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        if ext == "jpg":
            img = img.convert("RGB")

        out_path = os.path.join(output_dir, f"{prefix}_{page_num:02d}.{ext}")
        save_kwargs = {"format": pil_fmt, "optimize": compress}
        if ext == "jpg":
            save_kwargs["quality"] = quality
        img.save(out_path, **save_kwargs)
        out_paths.append(out_path)

        if progress_callback:
            progress_callback(idx + 1, total)

    doc.close()
    return out_paths


def main():
    parser = argparse.ArgumentParser(
        description="Convert each page of a PDF to JPG or PNG images."
    )
    parser.add_argument("input", help="Path to the PDF file")
    parser.add_argument(
        "-o", "--output", default="./output", help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--format", choices=["jpg", "png"], default="jpg",
        help="Output image format (default: jpg)"
    )
    parser.add_argument(
        "--height", type=int, default=None,
        help="Output height in pixels (default: original height)"
    )
    parser.add_argument(
        "--width", type=int, default=None,
        help="Output width in pixels (default: auto from height, or original)"
    )
    parser.add_argument(
        "--quality", type=int, default=85,
        help="JPEG quality 1-100, ignored for PNG (default: 85)"
    )
    parser.add_argument(
        "--prefix", default="page",
        help="Output filename prefix (default: page)"
    )
    parser.add_argument(
        "--pages", default=None,
        help="Pages to export, e.g. '1-3' or '1,2,5' (default: all)"
    )
    parser.add_argument(
        "-c", "--compress", action="store_true",
        help="Enable Pillow optimize (lossless compression, smaller output)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"Error: input file not found: {args.input}")

    page_list = parse_pages(args.pages)

    def print_progress(current, total):
        print(f"[{current}/{total}]")

    out_paths = convert_pdf(
        args.input, args.output, args.format, args.quality, args.prefix,
        height=args.height, width=args.width, pages=page_list,
        compress=args.compress,
        progress_callback=print_progress
    )

    print(f"Done — {len(out_paths)} page(s) saved to {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
