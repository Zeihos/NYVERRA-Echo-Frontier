"""Validate NYVERRA Visual Polish texture pack before importing into UE.

Stdlib only. Checks all nine 1024x1024 PNGs, chunk CRC32 and optional
0.55 TEXTURE_MANIFEST.json SHA256 hashes. Exits nonzero on any failure.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "Content" / "VisualPolishSource" / "Terrain"
TEXTURES = tuple(
    (kind, channel, TERRAIN / f"T_Ny{kind}_{channel}.png")
    for kind in ("Grass", "Rock", "Soil")
    for channel in ("Albedo", "Normal", "Roughness")
)

def verify_png(filename, channel):
    data = filename.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG: " + filename.name)
    offset, width, height, color_type, found_end = 8, None, None, None, False
    seen_idat = False
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        tag = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            raise ValueError("Truncated chunk: " + filename.name)
        expected = struct.unpack_from(">I", data, offset + 8 + size)[0]
        observed = zlib.crc32(data[offset + 4:offset + 8 + size]) & 0xFFFFFFFF
        if observed != expected:
            raise ValueError(f"PNG CRC mismatch ({tag!r}): {filename.name}")
        if tag == b"IHDR":
            if width is not None or size != 13:
                raise ValueError("Invalid IHDR")
            width, height, depth, color_type, comp, filt, interlace = \
                struct.unpack_from(">IIBBBBB", data, offset + 8)
            if (width, height, depth, comp, filt, interlace) != (1024, 1024, 8, 0, 0, 0):
                raise ValueError("Expected 1024x1024 non-interlaced 8-bit PNG: " + filename.name)
            if channel == "Roughness" and color_type != 0:
                raise ValueError("Roughness must be single-channel grayscale: " + filename.name)
            if channel != "Roughness" and color_type not in (2, 6):
                raise ValueError("Albedo/Normal must be RGB(A): " + filename.name)
        elif tag == b"IDAT":
            seen_idat = True
        elif tag == b"IEND":
            found_end = True
            if end != len(data):
                raise ValueError("Trailing bytes after IEND: " + filename.name)
            break
        offset = end
    if width is None or not seen_idat or not found_end:
        raise ValueError("Missing IHDR, IDAT or IEND: " + filename.name)
    return len(data), hashlib.sha256(data).hexdigest()

def main():
    if not (ROOT / "NYVERRA.uproject").is_file():
        raise ValueError("Expected NYVERRA.uproject next to Tools/")
    missing = [str(p) for _, _, p in TEXTURES if not p.is_file()]
    if missing:
        raise ValueError("Incomplete visual pack:\n" + "\n".join(missing))
    stats = {}
    for kind, channel, path in TEXTURES:
        size, digest = verify_png(path, channel)
        stats[path.name] = {"size": size, "sha256": digest}
        print(f"[OK] {path.name}: 1024x1024, CRC OK, {size} bytes")
    manifest_path = ROOT / "TEXTURE_MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for texture in manifest.get("textures", []):
            name = texture["file"]
            if name not in stats:
                raise ValueError("Unexpected file in manifest: " + name)
            if (stats[name]["size"] != texture["size"] or
                    stats[name]["sha256"].lower() != texture["sha256"].lower()):
                raise ValueError("Manifest size / SHA256 mismatch: " + name)
        print(f"[OK] SHA256 manifest matches {len(manifest.get('textures', []))} entries")
    print("[SUCCESS] NYVERRA terrain PBR image set is structurally valid: 9 of 9 PNGs")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("[ERROR] " + str(exc), file=sys.stderr)
        sys.exit(1)
