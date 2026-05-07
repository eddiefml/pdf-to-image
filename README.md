# PDF to Image Converter

Convert each page of a PDF to JPG or PNG images. GUI + CLI.

## Download (Windows)

Get the latest pre-built `.exe` from [Releases](https://github.com/eddiefml/pdf-to-image/releases).  
Download `pdf-to-image.zip`, unzip, and run:

- **`pdf_to_image_gui.exe`** — double-click, graphical interface
- **`pdf_to_image.exe`** — command-line, for scripting

No Python required.

## GUI Usage

Double-click `pdf_to_image_gui.exe`:

| Field | Description |
|---|---|
| Input PDF | Pick a `.pdf` file |
| Output Folder | Where images go (default: `./output`) |
| Width / Height (px) | Set either or both. Leave empty = auto from ratio. Both empty = original size |
| Pages | e.g. `1-3` or `1,2,5`. Empty = all pages |
| Quality | 1–100 (JPEG only) |
| Format | `jpg` or `png` |
| File Name Prefix | Output filename prefix → `prefix_01.jpg` |
| Compress | Enable Pillow lossless optimization (~20-25% smaller) |

## CLI Usage

```
python pdf_to_image.py input.pdf [options]
```

```
pdf_to_image.exe input.pdf [options]
```

| Option | Default | Description |
|---|---|---|
| `-o`, `--output` | `./output` | Output directory |
| `--height` | (original) | Output height in px |
| `--width` | (auto) | Output width in px |
| `--format` | `jpg` | `jpg` or `png` |
| `--quality` | `85` | JPEG quality 1–100 |
| `--pages` | (all) | e.g. `1-3` or `1,2,5` |
| `--prefix` | `page` | Filename prefix |
| `-c`, `--compress` | off | Enable lossless compression |

### Examples

```bash
# All pages, 1080px height, JPEG quality 90
python pdf_to_image.py document.pdf --height 1080 --quality 90

# Pages 1 to 5 only, 800px width, PNG
python pdf_to_image.py document.pdf --width 800 --pages 1-5 --format png

# Use original size, compress output
python pdf_to_image.py document.pdf --compress
```

## Build your own .exe

Requires Python 3.10+.

```bash
# Clone
git clone https://github.com/eddiefml/pdf-to-image.git
cd pdf-to-image

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build CLI exe
python -m PyInstaller --onefile --name pdf_to_image --distpath . pdf_to_image.py

# Build GUI exe
python -m PyInstaller --onefile --name pdf_to_image_gui --distpath . pdf_to_image_gui.py

# Clean up build artifacts
rm -rf build *.spec
```

The `.exe` files will be in the project folder (~35 MB each, self-contained).
