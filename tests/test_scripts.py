"""Offline tests for the deterministic scripts (no network, no ffmpeg).

Run from the repository root:  python -m unittest discover tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "demo")
sys.path.insert(0, SCRIPTS)

from common import find_pkg, parse_ts, slug, ts  # noqa: E402


def run(script, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                          capture_output=True, text=True)


class Helpers(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slug("Design Will Never Be The Same"), "design-will-never-be-the-same")
        self.assertEqual(slug("Diseño & Código: ¿IA?"), "diseno-codigo-ia")
        self.assertEqual(slug(""), "")
        self.assertLessEqual(len(slug("x" * 200)), 60)

    def test_timestamps(self):
        self.assertEqual(parse_ts("3:55"), 235)
        self.assertEqual(parse_ts("1:02:03"), 3723)
        self.assertEqual(ts(235), "03:55")
        self.assertEqual(ts(3723), "1:02:03")

    def test_find_pkg(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "my-talk-abc123"))
            self.assertTrue(find_pkg(root, "abc123").endswith("my-talk-abc123"))
            self.assertIsNone(find_pkg(root, "zzz"))


class Package(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pkg = os.path.join(self.tmp, "demo-talk-demo-000000")
        shutil.copytree(FIXTURE, self.pkg)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_check_ok(self):
        p = run("check.py", self.pkg)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("OK", p.stdout)

    def test_check_flags_image_without_caption(self):
        md = os.path.join(self.pkg, "article.md")
        text = open(md, encoding="utf-8").read().replace(
            "*Screenshot 01:30 · Run time of the tool before and after adding a cache (placeholder slide).*", "")
        open(md, "w", encoding="utf-8").write(text)
        p = run("check.py", self.pkg)
        self.assertEqual(p.returncode, 1)
        self.assertIn("without a timestamped caption", p.stdout)

    def test_build_page(self):
        p = run("build.py", self.pkg)
        self.assertEqual(p.returncode, 0, p.stderr)
        page = open(os.path.join(self.pkg, "index.html"), encoding="utf-8").read()
        self.assertIn('<aside class="side">', page)
        self.assertIn('href="#key-ideas"', page)
        self.assertIn('id="1-do-less-before-doing-it-faster"', page)
        self.assertIn('src="images/0130.jpg"', page)  # assets stay as files next to the page
        self.assertIn('placeholder="Search"', page)

    def test_clean_keeps_deliverable(self):
        for name in ("video.mp4", "subs.en.json3", "info.json"):
            open(os.path.join(self.pkg, name), "w").close()
        os.makedirs(os.path.join(self.pkg, "candidates"))
        p = run("build.py", self.pkg, "--clean")
        self.assertEqual(p.returncode, 0, p.stderr)
        left = set(os.listdir(self.pkg))
        self.assertTrue({"index.html", "article.md", "images", "manifest.json"} <= left)
        self.assertFalse({"video.mp4", "subs.en.json3", "info.json", "candidates"} & left)


if __name__ == "__main__":
    unittest.main()
