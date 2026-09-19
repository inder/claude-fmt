"""Checks on the shipped plugin files themselves."""

import json
import os
import re
import unittest

import helpers

MANIFESTS = (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "hooks/hooks.json")
SKIP_NAMES = {".git", "__pycache__"}


def load(rel):
    with open(os.path.join(helpers.ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def walk_keys(value):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key
            yield from walk_keys(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from walk_keys(inner)


class PackageTest(unittest.TestCase):
    def test_manifests_carry_no_email(self):
        for rel in MANIFESTS:
            self.assertNotIn("email", set(walk_keys(load(rel))), rel)

    def test_plugin_and_marketplace_agree(self):
        plugin = load(".claude-plugin/plugin.json")
        market = load(".claude-plugin/marketplace.json")
        self.assertEqual(plugin["name"], "fmt")
        self.assertEqual([p["name"] for p in market["plugins"]], ["fmt"])

    def test_every_hook_is_exec_form_with_short_timeout(self):
        hooks = load("hooks/hooks.json")["hooks"]
        self.assertTrue(hooks)
        for event, groups in hooks.items():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertEqual(hook["command"], "python3", event)
                    self.assertIsInstance(hook["args"], list, event)
                    self.assertLessEqual(hook["timeout"], 5, event)

    def test_mode_skill_is_user_only(self):
        with open(os.path.join(helpers.ROOT, "skills/mode/SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("disable-model-invocation: true", text)

    def test_no_personal_paths_or_addresses_in_repo(self):
        home = re.compile(r"/(Users|home)/(?!user/)[A-Za-z0-9._-]+/")
        address = re.compile(r"[A-Za-z0-9._%+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com")
        for dirpath, dirnames, filenames in os.walk(helpers.ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
            for name in filenames:
                if name in SKIP_NAMES:
                    continue
                full = os.path.join(dirpath, name)
                with open(full, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                rel = os.path.relpath(full, helpers.ROOT)
                self.assertIsNone(home.search(text), rel)
                self.assertIsNone(address.search(text), rel)


if __name__ == "__main__":
    unittest.main()
