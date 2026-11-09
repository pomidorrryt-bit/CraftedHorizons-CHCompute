#!/usr/bin/env python3
"""Build a standalone additive Santa's Totem pack for Minecraft Java 1.21.11."""
from pathlib import Path
import hashlib
import json
import struct
import zipfile

root = Path(__file__).resolve().parents[1]
png = (root / "assets" / "santa_totem.png").read_bytes()
if png[:8] != bytes.fromhex("89504e470d0a1a0a"):
    raise ValueError("Santa texture is not PNG")
width, height = struct.unpack(">II", png[16:24])
if (width, height) != (32, 32):
    raise ValueError("Santa texture must be 32x32")

files = {
    "pack.mcmeta": json.dumps({"pack": {
        "description": "CraftedHorizons Santa's Totem (Java 1.21.11)",
        "min_format": [75, 0], "max_format": [75, 0]
    }}),
    "assets/craftedhorizons/items/santa_totem.json": json.dumps({
        "model": {"type": "minecraft:model", "model": "craftedhorizons:item/santa_totem"}
    }),
    "assets/craftedhorizons/models/item/santa_totem.json": json.dumps({
        "parent": "minecraft:item/generated",
        "textures": {"layer0": "craftedhorizons:item/santa_totem"}
    }),
    "assets/craftedhorizons/textures/item/santa_totem.png": png,
}
output = root / "CHSantaTotem-1.21.11.zip"
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, content in files.items():
        archive.writestr(name, content)
with zipfile.ZipFile(output) as archive:
    if archive.testzip() is not None or set(archive.namelist()) != set(files):
        raise ValueError("Pack archive integrity failure")
digest = hashlib.sha1(output.read_bytes()).hexdigest()
(root / "CHSantaTotem-SHA1.txt").write_text(
    f"{digest}  {output.name}\n", encoding="ascii")
print(f"Santa Totem pack: {output.stat().st_size} bytes; SHA1: {digest}")
