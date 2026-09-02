#!/usr/bin/env python3
# no.py = sx.py completely decoded. All encodings (base64, base85, bytes([...]))
# are removed and replaced with real Python code and literal strings.
# Run:  python3 no.py   (decodes everything from sx.py, verifies it, extracts it)
#
# The file sx.py is 493,406 bytes. 492,744 of those bytes (99.87%) are ONE
# base64 string (AH) holding a ZIP with a 1.68 MB compiled ARM64 binary
# ("DEMO"). The actual Python code in the whole chain is the ~40 lines you
# see below -- everything that exists, decoded 100%.
#
# About DEMO: it is NOT encoded Python. It is machine code produced by a
# compiler (Cython 3.2.5 -> C -> native ARM64). Nothing in it is encrypted,
# so there is nothing to decrypt: the Python source it was built from simply
# does not exist inside it, the same way a .exe has no C++ source inside.
# Verified: no PyInstaller archive, no .pyc bytecode, no source strings.

import ast
import atexit
import base64
import io
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SX = os.path.join(HERE, "sx.py")
OUT = os.path.join(HERE, "no_decoded")


# ===========================================================================
# PART 1 -- the AH string from sx.py, decoded
# ===========================================================================
def ah_decoded():
    """AH was a 492,744-character base64 string. Decoded, it is this ZIP."""
    src = open(SX, "r", encoding="utf-8", errors="replace").read()
    ah = re.search(r'^AH\s*=\s*"(.*)"\s*$', src, re.M).group(1)
    return base64.b64decode(ah)          # 369,557 bytes, starts with PK\x03\x04


# ===========================================================================
# PART 2 -- the hidden script that sx.py ran (__main__.py), fully decoded
#
# In sx.py it looked like this:
#     from base64 import b85decode
#     exec(b85decode(b'3TbU{Z*p`XZ*vN1ZE$aLbRctia|&;BE^~Q...'))
# ...and inside THAT, the strings were hidden as byte arrays:
#     bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,72,79,77,69,61])
#     bytes([32,38,38,32])
#     bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,95,69,88,69,67,
#            85,84,65,66,76,69,61])
#     bytes([46,47])
#
# Here it is with EVERY encoding removed. This is the entire script --
# all of it, word for word:
# ===========================================================================
def decoded_hidden_script():
    import os
    import sys
    os.system("export PYTHONHOME=" + sys.prefix + " && export PYTHON_EXECUTABLE=" + sys.executable + " && ./DEMO")


# Its exact original text (base85 blob and byte arrays intact), for reference:
HIDDEN_SCRIPT_ORIGINAL = (
    "\n\n#Dec_it_If_You_Can \n\n#BY DEMO\n\n"
    "from base64 import b85decode\n"
    "exec(b85decode(b'3TbU{Z*p`XZ*vN1ZE$aLbRctia|&;BE^~QvbY*QQVtI6Bb0}LeFflA3F)}"
    "bLATcpAEFdv4F)Sc4F*Gb7F)=nQATu&7AUH5AAUHWJAUHHEAU85BAU8QIAU8NHAU85BAU8QIAU8KG"
    "AT~KHAT}{wDK2DXV{c?-C@Cv*d2=psa%E;|cq?LgbY*iWTQf2&ATu~DATu~DATu&uDK2DXV{c?-C"
    "@Cvqd30rSC|fZwF)Sc4GB7M4F)=bMATcp9EFdv4G%O%7F*Yn9Gcqh7I4~?AI5{jJI5aFEH!>_BH#"
    "saIH#jUHIW;UGHaRRHI5;dIHaRRHHa9FFI5jLFI5aFEHZ?3DHa09EH#RIFHaRRHHZff(E@Wk6Z)9a"
    "CDJye%b1r3gWn*=8VPb4$D`I(cWpgN7Gcqh7GdL_DGdL_DGcsK%E@Wk6Z)9aCDJx=mbY*iWTQoK-"
    "AT&2!DK2DXV{c?-C@CN-AR<IXO-~{z3I'))\n"
)


def decode_hidden_script_from_sx():
    """Decode the hidden script straight out of sx.py and return its source."""
    zf = zipfile.ZipFile(io.BytesIO(ah_decoded()))
    inner = zf.read("__main__.py").decode("utf-8")
    blob = re.search(r"b85decode\(b'(.*?)'\)", inner, re.S).group(1)
    return base64.b85decode(blob).decode("utf-8")


# ===========================================================================
# PART 3 -- sx.py itself, decoded end to end (logic unchanged, AH resolved)
# ===========================================================================
def decoded_sxpy():
    MyHome = os.path.expanduser("~")
    PYDEMO = os.path.join(MyHome, ".PYDEMO")

    def cleanup():
        shutil.rmtree(PYDEMO, ignore_errors=True)

    atexit.register(cleanup)

    Dev = ah_decoded()                                # was: base64.b64decode(AH)

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


# ===========================================================================
# Driver: decode everything, verify, extract
# ===========================================================================
def main():
    src = open(SX, "r", encoding="utf-8", errors="replace").read()
    ah = re.search(r'^AH\s*=\s*"(.*)"\s*$', src, re.M).group(1)
    raw = base64.b64decode(ah)

    print("=" * 66)
    print(" sx.py decoded -- complete contents")
    print("=" * 66)
    print(f"sx.py size            : {os.path.getsize(SX):,} bytes")
    print(f"  the AH base64 string: {len(ah):,} bytes ({len(ah)*100//os.path.getsize(SX)}% of the file)")
    print(f"  everything else     : {os.path.getsize(SX)-len(ah):,} bytes (the 33 lines of code)")
    print(f"AH decoded            : {len(raw):,} bytes  magic={raw[:4]!r}  <- a ZIP")

    zf = zipfile.ZipFile(io.BytesIO(raw))
    print(f"ZIP integrity         : {'all CRCs OK' if zf.testzip() is None else 'CORRUPT'}")

    os.makedirs(OUT, exist_ok=True)
    print("\nFiles inside the ZIP:")
    for info in zf.infolist():
        data = zf.read(info.filename)
        with open(os.path.join(OUT, info.filename), "wb") as f:
            f.write(data)
        kind = "Python script" if info.filename.endswith(".py") else "ARM64 machine code (Cython-compiled)"
        print(f"  {info.filename:<14} {info.file_size:>9,} bytes  [{kind}]  -> no_decoded/")

    print("\nThe hidden script, decoded (this is all of it):")
    print("-" * 66)
    print(decode_hidden_script_from_sx())
    print("-" * 66)
    print("With the byte arrays decoded it reads:")
    print('    os.system("export PYTHONHOME=" + sys.prefix')
    print('              + " && export PYTHON_EXECUTABLE=" + sys.executable')
    print('              + " && ./DEMO")')
    print("\nEverything decodable in sx.py is now decoded above and in no_decoded/.")


if __name__ == "__main__":
    main()
