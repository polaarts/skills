"""Offline tests for the deterministic scripts (no network, no ffmpeg).

Run from the repository root:  python -m unittest discover tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "demo")
sys.path.insert(0, SCRIPTS)

from common import find_pkg, parse_ts, slug, ts  # noqa: E402


def run(script, *args, env=None):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                          capture_output=True, text=True, env=env)


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
        self.assertNotIn('class="player"', page)  # no YouTube source, no player

    def test_build_page_youtube_player(self):
        import json
        mf = os.path.join(self.pkg, "manifest.json")
        m = json.load(open(mf, encoding="utf-8"))
        m["meta"].update(id="na1OyJ3E7Kc", url="https://www.youtube.com/watch?v=na1OyJ3E7Kc")
        json.dump(m, open(mf, "w", encoding="utf-8"))
        p = run("build.py", self.pkg)
        self.assertEqual(p.returncode, 0, p.stderr)
        page = open(os.path.join(self.pkg, "index.html"), encoding="utf-8").read()
        self.assertIn('data-id="na1OyJ3E7Kc" ', page)
        self.assertIn('src="https://www.youtube-nocookie.com/embed/na1OyJ3E7Kc?enablejsapi=1', page)

    def test_obsidian_export(self):
        import json
        mf = os.path.join(self.pkg, "manifest.json")
        m = json.load(open(mf, encoding="utf-8"))
        m["meta"].update(url="https://www.youtube.com/watch?v=na1OyJ3E7Kc", upload_date="20261020")
        json.dump(m, open(mf, "w", encoding="utf-8"))
        with tempfile.TemporaryDirectory() as vault, tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home)  # the remembered vault path goes to a throwaway home
            self.assertIn("no vault known", run("obsidian.py", self.pkg, env=env).stderr)
            self.assertEqual(run("obsidian.py", self.pkg, vault, env=env).returncode, 1)  # not a vault
            os.makedirs(os.path.join(vault, ".obsidian"))
            for name in ("Cache", "inicio"):  # "inicio": lowercase, never auto-linked
                open(os.path.join(vault, name + ".md"), "w").close()
            md = os.path.join(self.pkg, "article.md")
            open(md, "a", encoding="utf-8").write("\nCache it, Cache it again, `Cache`, inicio.\n")
            p = run("obsidian.py", self.pkg, vault, env=env)
            self.assertEqual(p.returncode, 0, p.stderr)
            note = p.stdout.splitlines()[0]
            text = open(note, encoding="utf-8").read()
            self.assertTrue(text.startswith("---\ntitle: "))
            self.assertIn("published: 2026-10-20\n", text)
            self.assertIn("![](https://www.youtube.com/watch?v=na1OyJ3E7Kc)", text)
            self.assertEqual(text.count("[[Cache]]"), 1)  # first mention only
            self.assertNotIn("[[inicio]]", text)
            self.assertNotIn("\n# ", text)  # H1 dropped: the note's name is the title
            self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(note), "images", "0130.jpg")))
            self.assertTrue(os.path.isfile(os.path.join(vault, "Talks", "Talks.base")))
            run("build.py", self.pkg, env=env)  # the page links to the exported note
            page = open(os.path.join(self.pkg, "index.html"), encoding="utf-8").read()
            self.assertIn('href="obsidian://open?path=' + quote(note) + '"', page)
            m["options"]["use"] = "external"  # never a local path in a page shared outside
            json.dump(m, open(mf, "w", encoding="utf-8"))
            run("build.py", self.pkg, env=env)
            self.assertNotIn("obsidian://", open(os.path.join(self.pkg, "index.html"), encoding="utf-8").read())
            p = run("obsidian.py", self.pkg, env=env)  # vault remembered from the first run
            self.assertIn("already exists", p.stderr)  # ...and never overwrites

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
