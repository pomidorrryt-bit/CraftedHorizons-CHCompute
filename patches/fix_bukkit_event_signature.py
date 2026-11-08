#!/usr/bin/env python3
"""Compile against Bukkit Plugin rather than JavaPlugin registerEvents overload.

The old prebuilt plugin linked a non-existent method:
PluginManager.registerEvents(Listener, JavaPlugin).
The Bukkit API declares registerEvents(Listener, Plugin).
"""
from pathlib import Path
import re

source = Path("buildsrc/plugin/src/main/java/com/craftedhorizons/compute/CHComputePlugin.java")
text = source.read_text(encoding="utf-8")
pattern = r"(\.registerEvents\s*\([^;]*?,\s*)this(\s*\))"
updated, count = re.subn(
    pattern,
    lambda match: match.group(1) + "((org.bukkit.plugin.Plugin) this)" + match.group(2),
    text,
    count=1,
)
if count != 1:
    raise SystemExit(f"Refusing patch: expected one Bukkit event registration, found {count}")
source.write_text(updated, encoding="utf-8")
print("Patched CHCompute registerEvents static Bukkit Plugin signature.")
