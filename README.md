# CH Compute — Crafted Horizons

Experimental, opt-in auxiliary computing for Minecraft Paper 1.21.11.

- **Windows app:** a user-controlled application; no automatic background computing.
- **Paper plugin:** issues limited, non-authoritative terrain preview tasks.
- **Consent:** required on every app start; users can stop or revoke at any time.
- **Limits:** 1–2 worker threads, 64–2048 MiB configurable soft memory limit, CPU duty-cycle limit.
- **Languages:** automatically selects Windows UI language from 60 available locales.

**Important:** This is a proof of concept, **not** a Minecraft TPS accelerator. Client RAM is not shared with server RAM. A dedicated TCP port and TLS certificate are required.

## Downloads
After the GitHub Actions build completes, open **Actions → Build CH Compute → latest successful run → Artifacts** to download the Windows executable ZIP and the Paper plugin ZIP.

## Source and security
- `desktop/`: Go desktop app
- `plugin/`: Java Paper plugin
- `docs/`: installation and security information
- **Never upload your private Falix server certificate, PKCS12 keystore, or passwords to this repository.**

The Windows application is unsigned. Do not disable Windows security to run it. First use should be on a test machine or sandbox.

This project is experimental and has not been end-to-end tested on a public Falix allocation.
