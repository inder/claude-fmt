"""The corpus meta-test: the checker against real and hand-crafted replies.

This is the mechanical gate for the checker's regexes. Every real reply
captured with the instruction on must get the verdict an independent labeler
gave it; every hand-crafted near-miss must fail its mode; every terse valid
reply must pass. Near-misses and terse replies are only meaningful if the rule
under test decided them, so none may be waved through by the short-reply floor.
"""

import collections
import json
import os
import unittest

import helpers
import fmt_check as K

CORPUS = os.path.join(helpers.ROOT, "tests", "corpus")


def load_manifest():
    with open(os.path.join(CORPUS, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def read(rel):
    with open(os.path.join(CORPUS, rel), encoding="utf-8") as f:
        return f.read()


class CorpusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def test_every_near_miss_fails_its_mode(self):
        for item in self.manifest["near"]:
            ok, reason = K.check(item["mode"], read(item["file"]))
            self.assertFalse(ok, "%s passed: %s" % (item["file"], reason))

    def test_every_terse_reply_passes_on_its_rule(self):
        for item in self.manifest["terse"]:
            ok, reason = K.check(item["mode"], read(item["file"]))
            self.assertTrue(ok, "%s failed: %s" % (item["file"], reason))
            self.assertNotEqual(reason, "short reply", item["file"])

    def test_captured_replies_match_their_independent_labels(self):
        for item in self.manifest["captured"]:
            text = read(item["file"])
            for mode, expected in item["expect"].items():
                ok, reason = K.check(mode, text)
                self.assertEqual(
                    "pass" if ok else "fail",
                    expected,
                    "%s as %s: %s" % (item["file"], mode, reason),
                )

    def test_known_false_passes_still_pass(self):
        # Accepted, documented passes the independent grader disagreed with.
        # If one starts failing, the checker's behavior changed: decide on
        # purpose whether that is an improvement and update the manifest.
        for item in self.manifest["captured"]:
            for mode, why in item.get("known_false_pass", {}).items():
                self.assertTrue(K.check(mode, read(item["file"]))[0], "%s as %s" % (item["file"], mode))
                self.assertTrue(why)

    def test_coverage_per_checked_mode(self):
        captured_pass = collections.Counter()
        captured_fail = collections.Counter()
        for item in self.manifest["captured"]:
            for mode, expected in item["expect"].items():
                (captured_pass if expected == "pass" else captured_fail)[mode] += 1
        terse = collections.Counter(item["mode"] for item in self.manifest["terse"])
        near = collections.Counter(item["mode"] for item in self.manifest["near"])
        for mode in K.CHECKED_MODES:
            self.assertGreaterEqual(captured_pass[mode], 3, mode)
            self.assertGreaterEqual(captured_fail[mode], 1, mode)
            self.assertGreaterEqual(terse[mode], 1, mode)
            self.assertGreaterEqual(near[mode], 3, mode)

    def test_near_misses_name_distinct_failure_modes(self):
        seen = collections.defaultdict(set)
        for item in self.manifest["near"]:
            self.assertTrue(item.get("failure_mode"), item["file"])
            seen[item["mode"]].add(item["failure_mode"])
        for mode in K.CHECKED_MODES:
            if mode == "concise":
                continue  # one semantic failure mode: too long
            self.assertGreaterEqual(len(seen[mode]), 3, mode)

    def test_captures_carry_no_account_details(self):
        # A capture run without --strict-mcp-config once appended a note about
        # the capturing account's claude.ai connectors. Replies in a public
        # corpus must be about the question only.
        leaks = ("connector", "~/.claude", "/users/", "/home/")
        for item in self.manifest["captured"]:
            text = read(item["file"]).lower()
            for marker in leaks:
                self.assertNotIn(marker, text, "%s mentions %r" % (item["file"], marker))

    def test_manifest_and_files_agree(self):
        listed = {
            item["file"]
            for kind in ("near", "terse", "captured")
            for item in self.manifest[kind]
        }
        on_disk = {
            os.path.join(kind, name)
            for kind in ("near", "terse", "captured")
            for name in os.listdir(os.path.join(CORPUS, kind))
            if name.endswith(".md")
        }
        self.assertEqual(listed, on_disk)


if __name__ == "__main__":
    unittest.main()
