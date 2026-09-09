"""Offline source-sync contracts; uses real yq and a fake GitHub CLI.

Run: python3 -m unittest discover -s scripts/tests -p test_source_sync.py -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40
GH = r'''#!/usr/bin/env python3
import base64, json, os, sys
args = sys.argv[1:]
if args[:2] == ['auth', 'status']:
    sys.exit(0)
with open(os.environ['SYNC_TEST_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\n')
url = args[1]
if '/commits?' in url:
    print('' if os.environ.get('SYNC_TEST_NO_COMMIT') else 'a' * 40)
elif '/git/trees/' in url:
    print('skills/demo/SKILL.md\tblob\thttps://api.github.test/blob/skill')
    print('skills/demo/reference.md\tblob\thttps://api.github.test/blob/reference')
elif '/blob/skill' in url:
    if os.environ.get('SYNC_TEST_FAIL_BLOB'):
        sys.exit(1)
    print(base64.b64encode(b'---\nname: demo\ndescription: Use when testing sync.\n---\n# Demo\n').decode())
elif '/blob/reference' in url:
    print(base64.b64encode(b'Reference\n').decode())
elif '/contents/' in url:
    print('{}')
else:
    raise SystemExit('Unexpected fake gh call: ' + repr(args))
'''


@unittest.skipUnless(shutil.which('yq'), 'source-sync tests require mikefarah/yq')
class SourceSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='source-sync-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        for name in ['sync-vendor.sh', 'add-vendor.sh']:
            shutil.copy2(ROOT / 'scripts' / name, self.root / 'scripts' / name)
        binary = self.root / 'bin'
        binary.mkdir()
        (binary / 'gh').write_text(GH)
        (binary / 'gh').chmod(0o755)
        self.log = self.root / 'gh.jsonl'
        self.env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'],
                        SYNC_TEST_LOG=str(self.log))

    def manifest(self, **extra):
        entry = {'name': 'demo', 'upstream': {
            'owner': 'example', 'repo': 'source', 'path': 'skills/demo', 'branch': 'main'},
            'last_sync': {'date': '', 'commit': ''}, **extra}
        (self.root / 'vendor.yaml').write_text(json.dumps({'skills': [entry]}))

    def run_sync(self, *args, success=True, **env):
        result = subprocess.run(['/bin/bash', str(self.root / 'scripts/sync-vendor.sh'), *args],
                                env={**self.env, **env}, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def entry(self):
        return json.loads(subprocess.check_output(
            ['yq', '-o=json', '.skills[0]', str(self.root / 'vendor.yaml')], text=True))

    def seed_copy(self, collection='owned'):
        dest = self.root / 'skills' / collection / 'demo'
        dest.mkdir(parents=True)
        (dest / 'SKILL.md').write_text('last good copy')
        return dest

    def test_default_vendor_destination_and_pinned_commit(self):
        self.manifest()
        self.run_sync('demo')
        self.assertTrue((self.root / 'skills/vendor/demo/SKILL.md').is_file())
        self.assertFalse((self.root / 'skills/owned').exists())
        self.assertEqual(self.entry()['last_sync']['commit'], COMMIT)
        self.assertIn('/git/trees/' + COMMIT, self.log.read_text())

    def test_owned_series_destination(self):
        self.manifest(collection='owned', series='browser-tools')
        self.run_sync('demo')
        self.assertTrue((self.root / 'skills/owned/browser-tools/demo/SKILL.md').is_file())
        self.assertFalse((self.root / 'skills/vendor').exists())

    def test_check_does_not_change_files_or_manifest(self):
        self.manifest(collection='owned')
        dest = self.seed_copy()
        before = (self.root / 'vendor.yaml').read_bytes()
        self.run_sync('--check', 'demo')
        self.assertEqual((dest / 'SKILL.md').read_text(), 'last good copy')
        self.assertEqual((self.root / 'vendor.yaml').read_bytes(), before)

    def test_pending_bootstrap_skips_api_and_requires_activation(self):
        self.manifest(collection='owned', pending_upstream=True)
        dest = self.seed_copy()
        result = self.run_sync('demo')
        self.assertIn('pending upstream publication', result.stdout)
        self.assertFalse(self.log.exists())
        self.assertEqual((dest / 'SKILL.md').read_text(), 'last good copy')
        self.run_sync('--activate', 'demo')
        self.assertNotIn('pending_upstream', self.entry())
        self.assertEqual(self.entry()['last_sync']['commit'], COMMIT)

    def test_unpublished_activation_preserves_bootstrap(self):
        self.manifest(collection='owned', pending_upstream=True)
        dest = self.seed_copy()
        self.run_sync('--activate', 'demo', success=False, SYNC_TEST_NO_COMMIT='1')
        self.assertTrue(self.entry()['pending_upstream'])
        self.assertEqual((dest / 'SKILL.md').read_text(), 'last good copy')

    def test_failed_early_blob_keeps_last_good_copy_and_sync_record(self):
        self.manifest(collection='owned')
        dest = self.seed_copy()
        before = (self.root / 'vendor.yaml').read_bytes()
        self.run_sync('demo', success=False, SYNC_TEST_FAIL_BLOB='1')
        self.assertEqual((dest / 'SKILL.md').read_text(), 'last good copy')
        self.assertEqual((self.root / 'vendor.yaml').read_bytes(), before)
        self.assertEqual(list((self.root / 'skills').glob('.skill-sync.*')), [])

    def test_invalid_destinations_and_pending_vendor_are_rejected(self):
        for entry in [{'collection': '../outside'}, {'series': '../outside'},
                      {'name': '../outside'}, {'pending_upstream': True}]:
            with self.subTest(entry=entry):
                self.manifest(**entry)
                self.run_sync(success=False)
                self.assertFalse((self.root / 'skills').exists())

    def test_frozen_owned_copy_is_preserved(self):
        self.manifest(collection='owned', frozen={'reason': 'fixture'})
        dest = self.seed_copy()
        self.run_sync('demo')
        self.assertEqual((dest / 'SKILL.md').read_text(), 'last good copy')
        self.assertFalse(self.log.exists())

    def test_add_owned_records_collection_without_sync(self):
        (self.root / 'vendor.yaml').write_text('{"skills": []}')
        result = subprocess.run(['/bin/bash', str(self.root / 'scripts/add-vendor.sh'),
                                 '--owned', '--no-sync', 'example/source/skills/demo'],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.entry()['collection'], 'owned')
        self.assertFalse((self.root / 'skills').exists())

    def test_activate_requires_one_named_write_operation(self):
        self.manifest(collection='owned', pending_upstream=True)
        self.run_sync('--activate', success=False)
        self.run_sync('--activate', '--check', 'demo', success=False)


if __name__ == '__main__':
    unittest.main()
