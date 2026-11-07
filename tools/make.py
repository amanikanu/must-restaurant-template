"""Builds index.html — a single self-contained file.

  tools/src-v2.html  -> markup / css / js
  build/v2/*.webp    -> photography (inlined)
  fonts/v2/poppins.css -> embedded Poppins webfont (inlined)

Run:  python3 tools/make.py
"""
import base64, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "src-v2.html"
OUT = ROOT / "index.html"
IMG_DIR = "build/v2"
FONT = ROOT / "fonts" / "v2" / "poppins.css"


def main():
    html = SRC.read_text()

    # ---- webfont ----
    css = FONT.read_text().replace("PoppinsEmbed", "Poppins")
    assert "<!--FONTS-->" in html
    html = html.replace("<!--FONTS-->", "<style>\n" + css + "</style>")

    # ---- inline every referenced image once (reuse slots hydrate at runtime) ----
    refs = sorted(set(re.findall(r"build/v2/([A-Za-z0-9_-]+\.webp)", html)))
    report = []
    for ref in refs:
        path = ROOT / IMG_DIR / ref
        b64 = base64.b64encode(path.read_bytes()).decode()
        html = html.replace(f"build/v2/{ref}", f"data:image/webp;base64,{b64}")
        report.append(f"  {ref:26s} {path.stat().st_size//1024:4d} KB")

    left = re.findall(r"build/[A-Za-z0-9_/-]+\.webp", html)
    assert not left, f"unresolved assets: {left[:5]}"

    OUT.write_text(html)
    print("\n".join(report))
    print(f"\ninlined {len(refs)} images")
    print(f"index.html -> {OUT.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
