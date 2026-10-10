import zipfile
from pathlib import Path

root = Path(r"C:\Users\Alien C Jomon\Documents\Q-Care")
original_apk = root / "installed-qcare.apk"
modified_html = root / "apk-patch" / "assets" / "public" / "index.html"
output_apk = root / "patched-unsigned.apk"

target = "assets/public/index.html"
replacement = modified_html.read_bytes()
replaced = False

with zipfile.ZipFile(original_apk, "r") as source:
    with zipfile.ZipFile(output_apk, "w") as output:
        for item in source.infolist():
            if item.filename == target:
                output.writestr(item, replacement)
                replaced = True
            else:
                output.writestr(item, source.read(item.filename))

if not replaced:
    raise SystemExit(f"ERROR: {target} was not found in the original APK.")

with zipfile.ZipFile(output_apk, "r") as check:
    assert check.read(target) == replacement

print(f"Success! Patched APK created: {output_apk}")
print(f"Updated frontend size: {len(replacement)} bytes")