"""Génère les icônes et le logo P2i (Pillow) dans p2i-assets/{source,dist}/."""
import base64
import io
import os

from PIL import Image

src = Image.open(io.BytesIO(base64.b64decode(open("p2i/icon.png.b64").read()))).convert("RGBA")
ICO_SIZES = [256, 128, 96, 64, 48, 40, 32, 24, 20, 16]


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def png(size):
    b = io.BytesIO()
    src.resize((size, size), Image.LANCZOS).save(b, "PNG", optimize=True)
    return b.getvalue()


def ico(sizes):
    b = io.BytesIO()
    src.resize((256, 256), Image.LANCZOS).save(b, "ICO", sizes=[(s, s) for s in sizes])
    return b.getvalue()


p256 = png(256)
multi = ico(ICO_SIZES)
S, D = "p2i-assets/source/", "p2i-assets/dist/"
# Fichiers remplacés dans les sources avant compilation
save(S + "res/icon.png", p256)
save(S + "res/128x128@2x.png", p256)
for s in (32, 64, 128):
    save(S + f"res/{s}x{s}.png", png(s))
save(S + "res/icon.ico", multi)
save(S + "res/tray-icon.ico", ico([32]))
save(S + "flutter/windows/runner/resources/app_icon.ico", multi)
# Fichiers remplacés dans le dossier compilé
assets = D + "data/flutter_assets/assets/"
save(assets + "icon.png", png(48))
save(assets + "icon.ico", multi)
save(assets + "logo.png", p256)
svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       'width="256" height="256" viewBox="0 0 256 256"><image width="256" height="256" '
       'xlink:href="data:image/png;base64,' + base64.b64encode(p256).decode() + '"/></svg>')
save(assets + "icon.svg", svg.encode())
print("Assets P2i générés.")
