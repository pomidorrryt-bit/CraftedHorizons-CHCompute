#!/usr/bin/env python3
"""Link to the real Bukkit PluginManager API without depending on local fake API stubs.

CHCompute's local test stubs declare an invalid overload:
registerEvents(Listener, JavaPlugin).
At runtime Paper declares registerEvents(Listener, Plugin).

Resolve the real Paper signature at runtime using reflection, so the plugin
can still be compiled with its existing local isolated build harness.
"""
from pathlib import Path
import re

source = Path("buildsrc/plugin/src/main/java/com/craftedhorizons/compute/CHComputePlugin.java")
text = source.read_text(encoding="utf-8")
pattern = r"Bukkit\.getPluginManager\(\)\.registerEvents\(\s*this\s*,\s*this\s*\);"
replacement = """try {
            Class<?> pluginType = Class.forName("org.bukkit.plugin.Plugin");
            Bukkit.getPluginManager().getClass().getMethod(
                    "registerEvents", org.bukkit.event.Listener.class, pluginType)
                    .invoke(Bukkit.getPluginManager(), this, this);
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("Unable to register CHCompute event listener", exception);
        }"""
updated, count = re.subn(pattern, replacement, text)
if count != 1:
    raise SystemExit(f"Refusing patch: expected one original event registration, found {count}")
source.write_text(updated, encoding="utf-8")
print("Patched CHCompute to bind to Bukkit's real registerEvents signature at runtime.")
