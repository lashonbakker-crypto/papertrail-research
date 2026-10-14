"""Render README graphics from a real demo run, using optional Pillow.

Pillow is needed only to rebuild these checked-in images, not to use PaperTrail.
The report graphic is a data overview, not a browser screenshot.
"""

import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("To rebuild graphics only: python -m pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONT = Path(os.environ.get("PAPERTRAIL_VISUAL_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
BOLD = FONT.with_name("DejaVuSans-Bold.ttf")
MONO = FONT.with_name("DejaVuSansMono.ttf")
NAVY, INK, MUTED, TEAL = "#12283b", "#152c3e", "#617486", "#168e79"


def font(size, bold=False, mono=False):
    path = MONO if mono else BOLD if bold else FONT
    return ImageFont.truetype(str(path if path.is_file() else FONT), size)


def text(draw, xy, value, size=20, color=INK, bold=False, mono=False):
    draw.text(xy, str(value), font=font(size, bold, mono), fill=color)


def panel(draw, box, color="white", radius=20):
    draw.rounded_rectangle(box, radius=radius, fill=color)


def overview(result):
    image = Image.new("RGB", (1280, 790), "#eef3f5")
    draw = ImageDraw.Draw(image)
    panel(draw, (32, 30, 1248, 213), NAVY, 24)
    text(draw, (62, 55), "PAPERTRAIL / REAL DEMO DATA", 16, "#7ed5be", True)
    text(draw, (62, 89), "Your research, with a record.", 40, "white", True)
    text(draw, (62, 153), "References, evidence and experiment outputs in one auditable workflow.", 20, "#c2d1dd")
    stats = [("REFERENCES", result["counts"]["references"]), ("EVIDENCE CARDS", result["counts"]["claims"]), ("RESULT RECORDS", result["counts"]["runs"]), ("ERRORS / REMINDERS", f'{len(result["errors"])} / {len(result["warnings"])}')]
    for i, (label, number) in enumerate(stats):
        left = 32 + i * 309
        panel(draw, (left, 235, left + 289, 354))
        text(draw, (left + 22, 253), label, 14, MUTED, True)
        text(draw, (left + 22, 283), number, 39, INK, True)
    panel(draw, (32, 377, 800, 699))
    text(draw, (60, 400), "01 / Measured retrieval results", 24, INK, True)
    text(draw, (60, 442), "Handwritten toy corpus / 12 queries / fixed 0-1 scale", 17, MUTED)
    for i, row in enumerate(r for r in result["runs"] if r["metric"] == "MRR"):
        top = 492 + i * 85
        text(draw, (60, top), f'{row["method"]} / {row["metric"]}', 20, INK, True)
        text(draw, (670, top), f'{float(row["value"]):.4f}', 20, TEAL, True)
        draw.rounded_rectangle((60, top + 37, 753, top + 51), 7, fill="#e4ecef")
        draw.rounded_rectangle((60, top + 37, 60 + round(693 * float(row["value"])), top + 51), 7, fill=TEAL if i == 0 else "#619ca9")
    text(draw, (60, 662), "Both methods score 1.0 here; this does not establish superiority.", 16, MUTED)
    panel(draw, (823, 377, 1248, 699), "#fff6df")
    text(draw, (849, 400), "02 / Before the next meeting", 22, INK, True)
    counts = Counter(item["code"] for item in result["warnings"])
    for i, (code, count) in enumerate(counts.items()):
        text(draw, (849, 452 + i * 39), f"{code} x{count}", 18, "#90621d", mono=True)
    for i, line in enumerate(("Read the original sources.", "Explain one result and one limit.", "Complete the manuscript TODO.")):
        text(draw, (849, 553 + i * 34), line, 18, INK)
    text(draw, (36, 726), "Data overview, not a browser screenshot. Open report/index.html for the full local report.", 17, MUTED)
    text(draw, (36, 755), "Source: PaperTrail demo / audit.json. Structural consistency is not scientific validity.", 15, MUTED)
    image.save(ASSETS / "report-preview.png", optimize=True)


def social(result):
    image = Image.new("RGB", (1280, 640), NAVY)
    draw = ImageDraw.Draw(image)
    text(draw, (70, 51), "PAPERTRAIL / OPEN SOURCE RESEARCH WORKFLOW", 18, "#7ed5be", True)
    text(draw, (67, 112), "Stop losing the trail", 55, "white", True)
    text(draw, (67, 181), "from sources to results.", 55, "white", True)
    text(draw, (70, 278), "References  /  Evidence  /  Experiments  /  Draft  /  Handoff", 24, "#c2d1dd")
    panel(draw, (69, 346, 1211, 443), "#214154", 16)
    text(draw, (91, 378), "$ python -m papertrail demo my-first-study", 29, "#a1ead3", mono=True)
    for i, (label, count) in enumerate((("references", result["counts"]["references"]), ("evidence cards", result["counts"]["claims"]), ("result records", result["counts"]["runs"]))):
        left = 71 + i * 300
        text(draw, (left, 474), count, 38, "white", True)
        text(draw, (left + 51, 490), label, 20, "#c2d1dd")
    text(draw, (70, 576), "Python 3.10+  /  local-first  /  no runtime dependencies  /  Chinese beginner guide", 18, "#92aab9")
    image.save(ASSETS / "social-preview.png", optimize=True)


def cli_replay(records):
    frames, durations = [], []
    for heading, command, lines, expected in records:
        lengths = list(range(0, len(command), 5)) + [len(command)]
        for length in lengths:
            image = Image.new("RGB", (1180, 660), "#0d1925")
            draw = ImageDraw.Draw(image)
            panel(draw, (22, 21, 1158, 639), "#142536", 19)
            for i, color in enumerate(("#ed7065", "#dfb659", "#69b997")):
                draw.ellipse((45 + i * 24, 42, 57 + i * 24, 54), fill=color)
            text(draw, (143, 37), "PaperTrail / CLI replay", 17, "#aac0cf")
            text(draw, (46, 90), heading, 27, "white", True)
            text(draw, (46, 159), "$ " + command[:length], 21, "#8adebc", mono=True)
            if length == len(command):
                for i, line in enumerate(lines):
                    text(draw, (46, 211 + i * 39), line, 19, "#d2e0e9", mono=True)
                text(draw, (46, 533), f"EXIT STATUS: {expected}", 20, "#8adebc" if expected == 0 else "#efbb65", True)
            text(draw, (46, 594), "Actual output excerpts. Paths shortened. Demonstration uses handwritten toy data.", 15, "#89a3b5")
            frames.append(image)
            durations.append(4200 if length == len(command) else 65)
    frames[0].save(ASSETS / "demo.gif", save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)


def main():
    ASSETS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        environment = dict(os.environ, PYTHONPATH=str(ROOT))

        def call(*args):
            completed = subprocess.run([sys.executable, "-m", "papertrail", *args], cwd=directory, env=environment, capture_output=True, text=True, encoding="utf-8")
            return completed.returncode, completed.stdout

        status, stdout = call("demo", "first-study")
        assert status == 0, stdout
        result = json.loads((Path(directory) / "first-study/report/audit.json").read_text(encoding="utf-8"))
        overview(result)
        social(result)
        exp_status, exp_stdout = call("experiment", "first-study", "--run-id", "again")
        assert exp_status == 0, exp_stdout
        manuscript = Path(directory) / "first-study/manuscript.md"
        with manuscript.open("a", encoding="utf-8") as handle:
            handle.write("\n[@notExists2026]\n")
        failure, fail_stdout = call("check", "first-study")
        assert failure == 2 and "missing_reference" in fail_stdout
        cli_replay([
            ("1 / Run the complete local workflow", "python -m papertrail demo first-study", [stdout.splitlines()[0], "Human review of sources and research design is still required.", "Open in your browser: first-study/report/index.html"], status),
            ("2 / Rerun the experiment with a new ID", "python -m papertrail experiment first-study --run-id again", exp_stdout.splitlines(), exp_status),
            ("3 / Add [@notExists2026], then check", "python -m papertrail check first-study", [fail_stdout.splitlines()[0], "ERROR [missing_reference] manuscript.md", "Human review of sources and research design is still required."], failure),
        ])
    print("Built data overview, social card and real-output CLI replay.")


if __name__ == "__main__":
    main()
