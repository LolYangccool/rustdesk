"""Personnalisation « P2i Assistance » appliquée aux sources RustDesk avant compilation.

Reprend les modifications faites par RDGen (bryangerlach/rdgen, generator-windows.yml)
avec les réglages choisis pour P2i. Lancé depuis la racine du dépôt, stdlib uniquement.
"""
import base64
import json
import os
import sys

APP_DISPLAY = "P2i Assistance"
APP = "P2iAssistance"          # nom technique (sans espace), comme RDGen
COMPANY = "P2i"
URL = "https://p2informatique.fr"
SERVER = "rd.p2informatique.fr"
KEY = "Afj2TQvqmEOflC+K9nmymU6PCLaesGq39Gc0dj7+pL8="
API = SERVER + ":21114"

errors = []


def edit(path, pairs, required=True):
    if not os.path.exists(path):
        (errors if required else []).append(f"absent : {path}")
        print(f"[skip] {path} absent")
        return
    with open(path, "r", encoding="utf-8", newline="") as f:
        txt = f.read()
    for old, new, *opt in pairs:
        must = (opt[0] if opt else True) and required
        if old not in txt:
            msg = f"motif introuvable dans {path} : {old[:70]!r}"
            print(("[ERREUR] " if must else "[info] ") + msg)
            if must:
                errors.append(msg)
            continue
        txt = txt.replace(old, new)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(txt)
    print(f"[ok] {path}")


def edit_glob(folder, ext, pairs, first_only=False):
    for root, _, files in os.walk(folder):
        for n in files:
            if n.endswith(ext):
                p = os.path.join(root, n)
                with open(p, "r", encoding="utf-8", newline="") as f:
                    txt = f.read()
                for old, new in pairs:
                    txt = txt.replace(old, new, 1) if first_only else txt.replace(old, new)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(txt)


# 1. Nom de l'application
for cargo in ("Cargo.toml", "libs/portable/Cargo.toml"):
    edit(cargo, [
        ('description = "RustDesk Remote Desktop"', f'description = "{APP}"', False),
        ('ProductName = "RustDesk"', f'ProductName = "{APP}"', False),
        ('FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{APP}"', False),
        ('OriginalFilename = "rustdesk.exe"', f'OriginalFilename = "{APP}.exe"', False),
    ])
edit("libs/portable/src/main.rs", [
    ('const APP_PREFIX: &str = "rustdesk";', f'const APP_PREFIX: &str = "{APP}";', False),
])
edit("flutter/windows/runner/Runner.rc", [
    ('"RustDesk Remote Desktop"', f'"{APP}"', False),
    ('VALUE "InternalName", "rustdesk" "\\0"', f'VALUE "InternalName", "{APP}" "\\0"', False),
    ('"rustdesk.exe"', f'"{APP}"', False),
    ('"RustDesk"', f'"{APP}"', False),
])
# Langues : « Powered by » → société, puis première occurrence de RustDesk → nom de l'appli
for root, _, files in os.walk("src/lang"):
    for n in files:
        if not n.endswith(".rs"):
            continue
        p = os.path.join(root, n)
        with open(p, "r", encoding="utf-8", newline="") as f:
            lines = f.read().split("\n")
        lines = [l.replace("RustDesk", COMPANY) if "powered_by_me" in l else l for l in lines]
        lines = [l.replace("RustDesk", APP, 1) for l in lines]
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(lines))
edit("res/msi/Package/License.rtf", [("RustDesk", APP, False)])

# 2. Société
for p in ("flutter/lib/desktop/pages/desktop_setting_page.dart", "res/msi/preprocess.py",
          "flutter/windows/runner/Runner.rc", "Cargo.toml", "libs/portable/Cargo.toml",
          "res/msi/Package/License.rtf", "src/main.rs"):
    edit(p, [("Purslane Tech Pte. Ltd.", COMPANY, False), ("Purslane Ltd", COMPANY, False)])
edit("res/msi/preprocess.py", [
    (r'r"Purslane(?: Tech Pte\.)? Ltd"', f'"{COMPANY}"', False),
    ("PURSLANE", COMPANY, False),
])

# 3. Liens vers le site
edit("build.py", [("Homepage: https://rustdesk.com", f"Homepage: {URL}", False)])
edit("flutter/lib/common.dart", [("launchUrl(Uri.parse('https://rustdesk.com'));", f"launchUrl(Uri.parse('{URL}'));", False)])
edit("flutter/lib/desktop/pages/desktop_setting_page.dart", [
    ("launchUrlString('https://rustdesk.com');", f"launchUrlString('{URL}');", False),
    ("launchUrlString('https://rustdesk.com/privacy.html')", f"launchUrlString('{URL}/privacy.html')", False),
])
edit("flutter/lib/desktop/pages/install_page.dart", [("https://rustdesk.com/privacy.html", f"{URL}/privacy.html", False)])
edit("res/msi/Package/License.rtf", [("rustdesk.com", URL, False)])

# 4. Serveur et clé intégrés
edit("libs/hbb_common/src/config.rs", [
    ("rs-ny.rustdesk.com", SERVER),
    ("OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=", KEY),
])
edit("src/common.rs", [("https://admin.rustdesk.com", API)])

# 5. custom_.txt sans signature RustDesk Pro (équivalent allowCustom.py de RDGen)
p = "src/common.rs"
with open(p, "r", encoding="utf-8", newline="") as f:
    lines = f.read().split("\n")
start = next((i for i, l in enumerate(lines)
              if l.strip().startswith('const KEY: &str = "5Qbwsde3unUcJBtrx9ZkvUmwFNoExHzpryHuPUdqlWM=";')), None)
if start is None:
    errors.append("bloc de vérification de signature introuvable dans src/common.rs")
else:
    block = lines[start:start + 9]
    if "sign::verify" not in "\n".join(block):
        errors.append("le bloc de signature de src/common.rs a changé de forme")
    else:
        del lines[start:start + 9]
lines = [l.replace("custom.txt", "custom_.txt") for l in lines]
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(lines))
print("[ok] custom_.txt autorisé")

# 6. Pas d'assistant « configurer le serveur », pas de notification de mise à jour, correctif de délai
edit("flutter/lib/desktop/pages/connection_page.dart", [
    ("if (!isIncomingOnly) setupServerWidget(),", "//if (!isIncomingOnly) setupServerWidget(),", False)])
edit("flutter/lib/desktop/pages/desktop_home_page.dart", [("updateUrl.isNotEmpty", "false", False)])
edit("src/client.rs", [(
    "if is_local || peer_nat_type == NatType::SYMMETRIC {",
    "if is_local || peer_nat_type == NatType::SYMMETRIC || !key.is_empty() {", False)])

# 7. Icône intégrée à l'interface Sciter (ui.rs), pour cohérence
icon_b64 = open("p2i/icon.png.b64").read().strip()
import re
p = "src/ui.rs"
if os.path.exists(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        txt = f.read()
    txt = re.sub(r"iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHL[A-Za-z0-9+/=]+", icon_b64, txt)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(txt)

# 8. Configuration client (custom_.txt), identique au client généré par RDGen
custom = {
    "conn-type": "incoming",
    "disable-settings": "Y",
    "app-name": APP_DISPLAY,
    "override-settings": {},
    "default-settings": {
        "access-mode": "custom",
        "enable-keyboard": "Y", "enable-clipboard": "Y", "enable-file-transfer": "Y",
        "enable-audio": "Y", "enable-tunnel": "Y", "enable-remote-restart": "Y",
        "enable-record-session": "Y", "enable-block-input": "Y",
        "allow-remote-config-modification": "N", "direct-server": "N",
        "verification-method": "use-both-passwords", "approve-mode": "password-click",
        "allow-hide-cm": "N", "allow-remove-wallpaper": "Y",
        "enable-remote-printer": "Y", "enable-camera": "Y", "enable-terminal": "Y",
    },
    "enable-lan-discovery": "Y",
    "allow-auto-disconnect": "N",
}
with open("p2i/custom_.txt", "w", encoding="ascii", newline="") as f:
    f.write(base64.b64encode(json.dumps(custom).encode("ascii")).decode("ascii"))

if errors:
    print("\n".join(["", "ÉCHEC de la personnalisation :"] + errors))
    sys.exit(1)
print("Personnalisation P2i appliquée.")
