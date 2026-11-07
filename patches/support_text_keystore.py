#!/usr/bin/env python3
"""Allow an administrator to supply a private PKCS#12 file as text for Falix inline file APIs.
The .b64 is stored ONLY in Falix /plugins/CHCompute, not included in public releases.
"""
from pathlib import Path

source = Path("buildsrc/plugin/src/main/java/com/craftedhorizons/compute/CHComputePlugin.java")
text = source.read_text(encoding="utf-8")
before = """        File file=new File(getDataFolder(),fileName);
        if(!file.isFile())throw new FileNotFoundException("keystore not found at "+file.getAbsolutePath());
        KeyStore ks=KeyStore.getInstance("PKCS12");
        try(InputStream in=new FileInputStream(file)){ks.load(in,pass.toCharArray());}"""
after = """        File file=new File(getDataFolder(),fileName);
        KeyStore ks=KeyStore.getInstance("PKCS12");
        if (file.isFile()) {
            try(InputStream in=new FileInputStream(file)){ks.load(in,pass.toCharArray());}
        } else {
            Path encodedPath=new File(getDataFolder(),fileName+".b64").toPath();
            if(!Files.isRegularFile(encodedPath))throw new FileNotFoundException("keystore missing at "+file.getAbsolutePath()+" or "+encodedPath);
            byte[] keyBytes=Base64.getMimeDecoder().decode(Files.readAllBytes(encodedPath));
            try(InputStream in=new ByteArrayInputStream(keyBytes)){ks.load(in,pass.toCharArray());}
            finally { Arrays.fill(keyBytes,(byte)0); }
        }"""
assert text.count(before) == 1, "Unexpected plugin source; refusing an unsafe patch"
source.write_text(text.replace(before, after), encoding="utf-8")
print("Applied text-transport keystore compatibility patch (private key remains server-only).")
