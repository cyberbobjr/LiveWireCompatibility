"""Turn the supported-mod list of README.steam* into a BBCode table with posters of one size.

Each entry is an optional poster line ``[url=X][img]Y[/img][/url]`` followed by a text line starting
with ``[b][url=X]``. Entries run from the line after ``[h2]...`` (first heading) to the next ``[h2]``.
The poster is resized by Steam's image service (128 x 128, letterboxed: letterbox=true pads to the exact box, checked 2026-11-20). Usage:
    python tools/steam_mod_table.py README.steam README.steam.fr ...
Idempotent: a file already holding a [table] is left unchanged.
"""
import re
import sys

SIZE = "?imw=128&imh=128&impolicy=Letterbox&letterbox=true"
POSTER = re.compile(r"^\[url=([^\]]+)\]\[img\]([^\[?]+?)/?(\?[^\[]*)?\[/img\]\[/url\]$")


def convert(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    if any("[table]" in l for l in lines):
        return None
    heads = [i for i, l in enumerate(lines) if l.startswith("[h2]")]
    start, end = heads[0], heads[1]
    rows, poster, body = [], None, []
    for line in lines[start + 1:end]:
        if not line.strip():
            continue
        m = POSTER.match(line)
        if m:
            poster = "[url=%s][img]%s/%s[/img][/url]" % (m.group(1), m.group(2), SIZE)
            continue
        if not line.startswith("[b][url="):
            raise ValueError("unexpected line in the mod list: " + line[:60])
        rows.append("[tr][td]%s[/td][td]%s[/td][/tr]" % (poster or "", line))
        poster = None
    block = ["", "[table]"] + rows + ["[/table]", ""]
    return nl.join(lines[:start + 1] + block + lines[end:])


def main(paths):
    for p in paths:
        with open(p, encoding="utf-8", newline="") as f:
            text = f.read()
        out = convert(text)
        if out is None:
            print(p, "already a table")
            continue
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(out)
        print(p, len(out.encode("utf-8")), "bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
