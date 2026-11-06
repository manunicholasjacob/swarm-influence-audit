"""Post-build: retarget the template's title footnote from the collusion sprint to this sprint.
Usage: python fix_footnote.py <docx>"""
import sys, zipfile, shutil, os

path = sys.argv[1]
SPRINT_URL = "https://apartresearch.com/sprints/swarm-alignment-2026"
repl = {
    "word/footnotes.xml": [
        ("AI Collusion Research Sprint", "Apart Swarm Alignment Hackathon"),
        (", October 2026", ", November 2026"),
    ],
    "word/_rels/footnotes.xml.rels": [
        ("https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25", SPRINT_URL),
    ],
}
tmp = path + ".tmp"
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.namelist():
        data = zin.read(item)
        if item in repl:
            s = data.decode("utf-8")
            for a, b in repl[item]:
                assert a in s, f"{a!r} not found in {item}"
                s = s.replace(a, b)
            data = s.encode("utf-8")
        zout.writestr(item, data)
os.replace(tmp, path)
print("footnote retargeted to", SPRINT_URL)
