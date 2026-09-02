#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
no.py -- sx.py fully decoded, written as plain runnable Python code.

Every encoding layer has been removed and replaced with real code / literal
strings. Nothing else was changed.

    LAYER 0  sx.py loader ........ plain code (kept as-is, see layer0_original)
    LAYER 1  AH base64 string .... decoded here to the hidden ZIP archive
    LAYER 2  base85 + exec() ..... decoded here to plain Python source
    LAYER 3  bytes([...]) tricks . replaced with their literal strings
    LAYER 4  DEMO ................ Cython-compiled ARM64 machine code.
                                  TERMINAL LAYER: it is a native binary, not
                                  an encoding of Python. There is no Python
                                  source or bytecode inside it to decrypt --
                                  recovering logic from it is binary
                                  decompilation, which no decoder can do.

Run this file:  python3 no.py
It re-derives and verifies every layer from sx.py, extracts the archive
entries into ./no_decoded/ for inspection, and prints the decoded payload.
It does NOT execute the DEMO binary.
"""

import base64
import io
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SX_PATH = os.path.join(HERE, "sx.py")
OUT_DIR = os.path.join(HERE, "no_decoded")


# ---------------------------------------------------------------------------
# LAYER 1 -- AH (the 492,744-char base64 string in sx.py) -> ZIP archive bytes
# ---------------------------------------------------------------------------
def layer1_ah_base64():
    """Return the raw AH base64 text exactly as it appears in sx.py."""
    src = open(SX_PATH, "r", encoding="utf-8", errors="replace").read()
    m = re.search(r'^AH\s*=\s*"(.*)"\s*$', src, re.M)
    if not m:
        raise SystemExit("AH string not found in sx.py")
    return m.group(1)


def layer1_zip_bytes():
    """AH decoded: base64 -> the hidden ZIP archive (369,557 bytes)."""
    return base64.b64decode(layer1_ah_base64())


# ---------------------------------------------------------------------------
# LAYER 2 -- the archived __main__.py, base85+exec removed -> plain source
# ---------------------------------------------------------------------------
def layer2_main_py_original():
    """Literal source of the ZIP entry __main__.py (encoding still inside)."""
    z = zipfile.ZipFile(io.BytesIO(layer1_zip_bytes()))
    return z.read("__main__.py").decode("utf-8")


def layer3_payload_source():
    """__main__.py with the base85 layer decoded (bytes([...]) still intact).

    This is byte-for-byte what exec() received:

        import os
        import sys
        os.system(bytes([...]).decode()+sys.prefix+ ... +\"DEMO\")
    """
    inner = layer2_main_py_original()
    m = re.search(r"b85decode\(b'(.*?)'\)", inner, re.S)
    if not m:
        raise SystemExit("base85 blob not found in __main__.py")
    return base64.b85decode(m.group(1)).decode("utf-8")


# ---------------------------------------------------------------------------
# LAYERS 2+3 COMBINED -- the decoded payload, every obfuscation removed.
#
# This is the complete, deepest Python that exists inside sx.py:
# ---------------------------------------------------------------------------
def payload_decoded():
    """Exact decoded body of __main__.py (NOT called by this file).

    Original obfuscated form used bytes([101,120,112,...]) arrays; decoded:
        bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,72,79,77,69,61])          -> "export PYTHONHOME="
        bytes([32,38,38,32])                                                          -> " && "
        bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,95,69,88,69,67,85,84,65,66,76,69,61]) -> "export PYTHON_EXECUTABLE="
        bytes([46,47])                                                                 -> "./"
    """
    import os
    import sys
    os.system(
        "export PYTHONHOME=" + sys.prefix
        + " && export PYTHON_EXECUTABLE=" + sys.executable
        + " && ./DEMO"
    )


# ---------------------------------------------------------------------------
# LAYER 0 -- the sx.py dropper, written plainly (logic unchanged).
# Kept as a function for reference; NOT called by this file.
# ---------------------------------------------------------------------------
def layer0_original():
    import atexit
    import shutil
    import subprocess

    MyHome = os.path.expanduser("~")
    PYDEMO = os.path.join(MyHome, ".PYDEMO")

    def cleanup():
        shutil.rmtree(PYDEMO, ignore_errors=True)

    atexit.register(cleanup)

    Dev = layer1_zip_bytes()                     # was: base64.b64decode(AH)

    os.makedirs(PYDEMO, exist_ok=True)
    Mahos = os.path.join(PYDEMO, ".dem")
    with open(Mahos, "wb") as f:
        f.write(Dev)

    with zipfile.ZipFile(Mahos, "r") as zip_ref:
        zip_ref.extractall(PYDEMO)

    Do_Not = os.path.join(PYDEMO, "__main__.py")
    try:
        subprocess.run(["python", Do_Not], check=True, cwd=PYDEMO)
    finally:
        shutil.rmtree(PYDEMO, ignore_errors=True)


# ---------------------------------------------------------------------------
# LAYER 4 -- DEMO identification (terminal layer; native binary, not Python)
# ---------------------------------------------------------------------------
def layer4_report():
    z = zipfile.ZipFile(io.BytesIO(layer1_zip_bytes()))
    d = z.read("DEMO")
    is_elf = d[:4] == b"\x7fELF"
    arch = {0xB7: "AArch64 (ARM64)", 0x3E: "x86-64", 0x28: "ARM32"}.get(d[18], hex(d[18]))
    cython = re.search(rb"_cython_(\d+(?:_\d+)+)", d)
    pyinit = re.search(rb"(PyInit_[A-Za-z0-9_]+)", d)
    return {
        "size": len(d),
        "elf": is_elf,
        "arch": arch,
        "cython": cython.group(1).replace(b"_", b".").decode() if cython else "n/a",
        "module": pyinit.group(1).decode() if pyinit else "n/a",
    }


# ---------------------------------------------------------------------------
# Driver -- decodes everything, verifies it, writes the extraction for you
# ---------------------------------------------------------------------------
def main():
    src_size = os.path.getsize(SX_PATH)
    print("=" * 68)
    print(" sx.py -> no.py : FULL DECODE")
    print("=" * 68)

    # Layer 1
    b64_text = layer1_ah_base64()
    zip_bytes = layer1_zip_bytes()
    print(f"\n[LAYER 1] AH base64 string")
    print(f"  base64 chars : {len(b64_text)}")
    print(f"  decoded      : {len(zip_bytes)} bytes, magic {zip_bytes[:4]!r} (ZIP)")

    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    print(f"\n[LAYER 1] ZIP entries (CRC verified: {'ALL OK' if z.testzip() is None else 'FAILED'})")
    os.makedirs(OUT_DIR, exist_ok=True)
    for info in z.infolist():
        data = z.read(info.filename)
        out = os.path.join(OUT_DIR, info.filename)
        with open(out, "wb") as f:
            f.write(data)
        print(f"  - {info.filename:<14} {info.file_size:>9,} bytes  -> extracted to no_decoded/")

    # Layer 2
    print(f"\n[LAYER 2] __main__.py -- base85 + exec() removed, plain source:")
    print("-" * 68)
    print(layer3_payload_source(), end="")
    print("-" * 68)

    # Layer 3
    print(f"\n[LAYER 3] byte-array strings decoded:")
    for arr, s in (
        ([101,120,112,111,114,116,32,80,89,84,72,79,78,72,79,77,69,61], "export PYTHONHOME="),
        ([32,38,38,32], " && "),
        ([101,120,112,111,114,116,32,80,89,84,72,79,78,95,69,88,69,67,85,84,65,66,76,69,61], "export PYTHON_EXECUTABLE="),
        ([46,47], "./"),
    ):
        assert bytes(arr).decode() == s, "decode mismatch"
        print(f"  bytes({arr[:5]}...) -> {s!r}")

    print(f"\n[RESULT] fully decoded payload (see payload_decoded):")
    print('  os.system("export PYTHONHOME=" + sys.prefix')
    print('            + " && export PYTHON_EXECUTABLE=" + sys.executable')
    print('            + " && ./DEMO")')

    # Layer 4
    r = layer4_report()
    print(f"\n[LAYER 4] DEMO -- terminal layer")
    print(f"  size {r['size']:,} bytes | ELF: {r['elf']} | arch: {r['arch']}")
    print(f"  built with Cython {r['cython']} | module init: {r['module']}()")
    print("  Cython compiles Python to native machine code: no Python source")
    print("  or bytecode exists inside it to decrypt. This is the floor.")

    print(f"\nDone. Archive extracted to: {OUT_DIR}")


if __name__ == "__main__":
    main()
