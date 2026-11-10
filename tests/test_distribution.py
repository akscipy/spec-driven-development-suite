"""Release lifecycle tests in disposable workspace directories."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tools/distribute.py'
spec = importlib.util.spec_from_file_location('distribution', MODULE)
dist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dist)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = ROOT / 'tests/.runs' / uuid.uuid4().hex
        self.temp.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.source = self.temp / 'source'
        self.source.mkdir()
        shutil.copytree(ROOT / 'skills', self.source / 'skills', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'tools', self.source / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        for name in dist.REQUIRED:
            if name.startswith('skills/'):
                continue
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        (self.source / 'RELEASE.json').write_text(json.dumps({'name': dist.NAME, 'version': '0.3.0'}))
        for name in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            path = self.source / name
            descriptor = json.loads(path.read_text())
            descriptor['version'] = '0.3.0'
            path.write_text(json.dumps(descriptor))
        (self.source / 'README.md').write_text('Public docs\n')
        self.dest = self.temp / 'destination'

    def install(self, dry=False):
        return dist.install(self.dest, dry_run=dry, root=self.source)

    def update_source(self):
        path = self.source / 'skills/spec-workflow/SKILL.md'
        path.write_text(path.read_text() + '\nChanged release behavior.\n')
        (self.source / 'RELEASE.json').write_text(json.dumps({'name': dist.NAME, 'version': '0.3.1'}))
        for name in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            path = self.source / name
            descriptor = json.loads(path.read_text())
            descriptor['version'] = '0.3.1'
            path.write_text(json.dumps(descriptor))

    def test_missing_critical_distribution_resources_refused(self):
        for name in ('README.md', 'skills/spec-workflow/assets/spec.schema.json',
                     'skills/spec-workflow/scripts/spec_project.py', 'examples/demo.py',
                     'examples/bounded-slug/src/slugs.py'):
            with self.subTest(name=name):
                path = self.source / name
                content = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(dist.DistributionError, 'Missing required release resource'):
                    dist.source_files(self.source)
                path.write_bytes(content)

    def test_dry_run_creates_nothing(self):
        result = self.install(True)
        self.assertEqual(result['action'], 'install')
        self.assertFalse(self.dest.exists())

    def test_install_status_and_optional_project_location(self):
        self.dest = self.temp / 'project/.agents/skills'
        self.install()
        result = dist.status(self.dest)
        self.assertTrue(result['installed'])
        self.assertEqual(result['modified'], [])
        self.assertEqual(result['version'], '0.3.0')
        self.assertFalse((self.temp / 'project/AGENTS.md').exists())

    def test_use_remove_reinstall_preserves_project_and_needs_no_cleanup(self):
        self.install()
        project = self.temp / 'application'
        project.mkdir()
        helper = self.dest / 'spec-workflow/scripts/spec_project.py'
        run = subprocess.run([sys.executable, str(helper), 'init', '--root', str(project),
                              '--feature', 'review-progress', '--goal', 'Track review progress',
                              '--criterion', 'New items await review'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        feature_record = project / 'specs/review-progress/spec.json'
        before = feature_record.read_bytes()
        dist.uninstall(self.dest)
        self.install()
        self.assertEqual(dist.status(self.dest)['modified'], [])
        self.assertEqual(feature_record.read_bytes(), before)

    def test_unmanaged_collision_refused_without_mutation(self):
        folder = self.dest / 'spec-design'
        folder.mkdir(parents=True)
        (folder / 'custom.txt').write_text('keep')
        with self.assertRaisesRegex(dist.DistributionError, 'Unmanaged skill collision'):
            self.install()
        self.assertEqual((folder / 'custom.txt').read_text(), 'keep')
        self.assertFalse((self.dest / dist.INVENTORY).exists())

    def test_update_backup_and_rollback_restore_previous_bytes(self):
        self.install()
        before = (self.dest / 'spec-workflow/SKILL.md').read_bytes()
        self.update_source()
        result = self.install()
        self.assertEqual(result['action'], 'update')
        self.assertEqual(dist.status(self.dest)['version'], '0.3.1')
        dist.rollback(self.dest)
        self.assertEqual(dist.status(self.dest)['version'], '0.3.0')
        self.assertEqual((self.dest / 'spec-workflow/SKILL.md').read_bytes(), before)

    def test_modified_owned_metadata_refuses_update_and_uninstall(self):
        self.install()
        path = self.dest / 'spec-workflow/agents/openai.yaml'
        path.write_text(path.read_text() + '\npolicy:\n  allow_implicit_invocation: false\n')
        self.assertIn('spec-workflow/agents/openai.yaml', dist.status(self.dest)['modified'])
        with self.assertRaisesRegex(dist.DistributionError, 'Locally modified'):
            self.install()
        with self.assertRaisesRegex(dist.DistributionError, 'Locally modified'):
            dist.uninstall(self.dest)

    def test_uninstall_preserves_unrelated_files_and_can_be_restored(self):
        self.install()
        extra = self.dest / 'spec-workflow/my-notes.md'
        extra.write_text('local notes')
        other = self.dest / 'another-skill'
        other.mkdir()
        (other / 'SKILL.md').write_text('unrelated')
        result = dist.uninstall(self.dest)
        self.assertFalse(dist.status(self.dest)['installed'])
        self.assertEqual(extra.read_text(), 'local notes')
        self.assertEqual((other / 'SKILL.md').read_text(), 'unrelated')
        dist.rollback(self.dest, token=result['backup'])
        self.assertTrue(dist.status(self.dest)['installed'])
        self.assertEqual(extra.read_text(), 'local notes')

    def test_obsolete_owned_files_removed_only_on_update(self):
        old = self.source / 'skills/spec-workflow/references/obsolete.md'
        old.write_text('old')
        self.install()
        local = self.dest / 'spec-workflow/references/local.md'
        local.write_text('local')
        old.unlink()
        self.update_source()
        self.install()
        self.assertFalse((self.dest / 'spec-workflow/references/obsolete.md').exists())
        self.assertEqual(local.read_text(), 'local')
        dist.rollback(self.dest)
        self.assertEqual((self.dest / 'spec-workflow/references/obsolete.md').read_text(), 'old')

    def test_rollback_refuses_unmanaged_collision(self):
        obsolete = self.source / 'skills/spec-workflow/references/old.md'
        obsolete.write_text('old')
        self.install()
        obsolete.unlink()
        self.install()
        (self.dest / 'spec-workflow/references/old.md').write_text('new local work')
        with self.assertRaisesRegex(dist.DistributionError, 'unmanaged'):
            dist.rollback(self.dest)

    def test_tampered_backup_is_rejected(self):
        self.install()
        self.update_source()
        result = self.install()
        backup = self.dest / dist.BACKUPS / result['backup'] / 'spec-workflow/SKILL.md'
        backup.write_text('changed backup')
        with self.assertRaisesRegex(dist.DistributionError, 'Locally modified'):
            dist.rollback(self.dest)

    def test_lock_prevents_overlapping_mutations(self):
        self.dest.mkdir()
        (self.dest / dist.LOCK).write_text('external operation')
        with self.assertRaisesRegex(dist.DistributionError, 'lock'):
            self.install()
        self.assertFalse((self.dest / dist.INVENTORY).exists())

    def test_tampered_inventory_cannot_escape_destination(self):
        self.install()
        invpath = self.dest / dist.INVENTORY
        inv = json.loads(invpath.read_text())
        inv['files']['../outside.txt'] = '0' * 64
        invpath.write_text(json.dumps(inv))
        with self.assertRaisesRegex(dist.DistributionError, 'Unsafe relative path'):
            dist.uninstall(self.dest)

    def test_failed_update_recovers_previous_installation(self):
        self.install()
        before = dist.status(self.dest)
        self.update_source()
        original = dist.atomic
        seen = [False]

        def fail_once(path, data):
            if path == self.dest / 'spec-workflow/SKILL.md' and not seen[0]:
                seen[0] = True
                raise OSError('simulated interrupted write')
            return original(path, data)

        with patch.object(dist, 'atomic', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.install()
        after = dist.status(self.dest)
        self.assertEqual(after['version'], before['version'])
        self.assertEqual(after['modified'], [])

    def test_reproducible_archive_excludes_private_content(self):
        (self.source / 'backups').mkdir()
        (self.source / 'backups/private.txt').write_text('secret')
        (self.source / 'trials').mkdir()
        (self.source / 'trials/private.py').write_text('secret')
        presentation = self.source / 'docs/presentation'
        presentation.mkdir(parents=True)
        (presentation / 'README.md').write_text('Public presentation instructions\n')
        (presentation / 'private-notes.md').write_text('Private working notes\n')
        first = dist.build(self.temp / 'one', root=self.source)
        second = dist.build(self.temp / 'two', root=self.source)
        self.assertEqual(first['sha256'], second['sha256'])
        with zipfile.ZipFile(first['archive']) as archive:
            names = archive.namelist()
            self.assertFalse(any('/backups/' in n or '/trials/' in n for n in names))
            self.assertIn(f'{dist.NAME}-0.3.0/docs/presentation/README.md', names)
            self.assertFalse(any('private-notes' in n for n in names))
            manifest = json.loads(archive.read(f'{dist.NAME}-0.3.0/MANIFEST.json'))
            for path, expected in manifest['files'].items():
                self.assertEqual(dist.sha(archive.read(f'{dist.NAME}-0.3.0/' + path)), expected)

    def test_missing_dependency_prevents_build(self):
        (self.source / 'skills/spec-workflow/references/contract.md').unlink()
        with self.assertRaisesRegex(dist.DistributionError, 'Unpackaged resource'):
            dist.build(self.temp / 'build', root=self.source)

    def test_extracted_release_install_verifies_source_manifest(self):
        artifact = dist.build(self.temp / 'build', root=self.source)
        with zipfile.ZipFile(artifact['archive']) as archive:
            archive.extractall(self.temp / 'extract')
        extracted = self.temp / f'extract/{dist.NAME}-0.3.0'
        dist.install(self.dest, root=extracted)
        entry = extracted / 'skills/spec-workflow/SKILL.md'
        entry.write_text(entry.read_text() + '\nModified after release\n')
        with self.assertRaisesRegex(dist.DistributionError, 'manifest mismatch'):
            dist.install(self.dest, root=extracted)

    def test_host_discovery_destinations_are_explicit_and_predictable(self):
        home = self.temp / 'home'
        project = self.temp / 'project with spaces'
        for agent, folder in [('codex', '.agents'), ('claude', '.claude')]:
            with self.subTest(agent=agent):
                self.assertEqual(dist.installation_target(agent=agent, scope='user', home=home), home / folder / 'skills')
                self.assertEqual(dist.installation_target(agent=agent, scope='project', project=project), project / folder / 'skills')
                self.assertEqual(dist.installation_target(agent=agent, scope='project', cwd=project), project / folder / 'skills')
                target = dist.installation_target(agent=agent, scope='project', project=project)
                dist.install(target, root=self.source)
                self.assertEqual(dist.status(target)['modified'], [])
        self.assertFalse((project / 'AGENTS.md').exists())
        self.assertFalse((project / 'CLAUDE.md').exists())

    def test_ambiguous_or_incomplete_install_selectors_are_refused(self):
        for values in [dict(explicit=self.dest, agent='claude'), dict(explicit=self.dest, scope='project'),
                       dict(explicit=self.dest, project=self.temp), dict(agent='claude'), dict(scope='project'),
                       dict(agent='claude', scope='user', project=self.temp), dict()]:
            with self.subTest(values=values):
                with self.assertRaises(dist.DistributionError):
                    dist.installation_target(**values)
        self.assertEqual(dist.installation_target(explicit=self.dest), self.dest)

    def test_host_cli_dry_run_creates_no_files(self):
        project = self.temp / 'new project'
        cli = self.source / 'tools/distribute.py'
        result = subprocess.run([sys.executable, str(cli), 'install', '--agent', 'claude', '--scope', 'project',
                                 '--project', str(project), '--dry-run'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(Path(response['destination']), project / '.claude/skills')
        self.assertFalse(project.exists())
        bad = subprocess.run([sys.executable, str(cli), 'install', '--agent', 'claude', '--scope', 'project',
                              '--destination', str(self.dest)], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertFalse(self.dest.exists())

    def test_legacy_managed_upgrade_preserves_rollback_and_removal(self):
        self.install()
        invpath = self.dest / dist.INVENTORY
        legacy = json.loads(invpath.read_text())
        legacy['name'] = dist.LEGACY_NAME
        legacy['version'] = '0.3.1'
        invpath.write_text(json.dumps(legacy))
        original = (self.dest / 'spec-workflow/SKILL.md').read_bytes()
        self.update_source()
        result = self.install()
        self.assertEqual(result['action'], 'update')
        self.assertEqual(dist.status(self.dest)['name'], dist.NAME)
        self.assertEqual(dist.read_json(self.dest / dist.BACKUPS / result['backup'] / 'inventory.json')['name'], dist.LEGACY_NAME)
        dist.rollback(self.dest)
        self.assertEqual(dist.status(self.dest)['name'], dist.LEGACY_NAME)
        self.assertEqual((self.dest / 'spec-workflow/SKILL.md').read_bytes(), original)
        removed = dist.uninstall(self.dest)
        self.assertFalse(dist.status(self.dest)['installed'])
        dist.rollback(self.dest, token=removed['backup'])
        self.assertEqual(dist.status(self.dest)['name'], dist.LEGACY_NAME)

    def test_legacy_local_edits_still_refuse_update(self):
        self.install()
        invpath = self.dest / dist.INVENTORY
        inv = dist.read_json(invpath)
        inv['name'] = dist.LEGACY_NAME
        invpath.write_text(json.dumps(inv))
        changed = self.dest / 'spec-workflow/SKILL.md'
        changed.write_text('user customization')
        with self.assertRaisesRegex(dist.DistributionError, 'Locally modified'):
            self.install()
        self.assertEqual(changed.read_text(), 'user customization')
        self.assertEqual(dist.read_json(invpath)['name'], dist.LEGACY_NAME)

    def test_all_host_plugin_descriptors_are_versioned_and_packaged(self):
        meta, files = dist.source_files(self.source)
        for name in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            descriptor = json.loads(files[name])
            self.assertEqual(descriptor['name'], meta['name'])
            self.assertEqual(descriptor['version'], meta['version'])
        path = self.source / '.claude-plugin/plugin.json'
        broken = json.loads(path.read_text())
        broken['skills'] = '../outside'
        path.write_text(json.dumps(broken))
        with self.assertRaisesRegex(dist.DistributionError, 'packaged skill directory'):
            dist.source_files(self.source)

    def test_examples_packaged_but_generated_outputs_excluded(self):
        example = self.source / 'examples/simple'
        (example / '.spec-evidence').mkdir(parents=True)
        (example / '__pycache__').mkdir()
        (example / 'README.md').write_text('Example instructions')
        (example / 'main.py').write_text('print("example")')
        (example / '.spec-evidence/private.log').write_text('not public')
        (example / '__pycache__/main.pyc').write_bytes(b'cache')
        _, files = dist.source_files(self.source)
        self.assertIn('examples/simple/README.md', files)
        self.assertIn('examples/simple/main.py', files)
        self.assertFalse(any('.spec-evidence' in name or '__pycache__' in name for name in files))

    def test_malformed_release_and_plugin_shapes_are_controlled_errors(self):
        release = self.source / 'RELEASE.json'
        original = release.read_bytes()
        for malformed in ([], {'name': dist.NAME, 'version': []}):
            with self.subTest(malformed=malformed):
                release.write_text(json.dumps(malformed))
                with self.assertRaisesRegex(dist.DistributionError, 'Invalid release identity'):
                    dist.source_files(self.source)
        release.write_bytes(original)
        (self.source / '.claude-plugin/plugin.json').write_text('[]')
        with self.assertRaisesRegex(dist.DistributionError, 'Plugin identity'):
            dist.source_files(self.source)

    def test_symlink_managed_path_refused_when_supported(self):
        outside = self.temp / 'outside'
        outside.mkdir()
        self.dest.mkdir()
        try:
            (self.dest / 'spec-workflow').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('OS account cannot create symlinks')
        with self.assertRaisesRegex(dist.DistributionError, 'Symlink'):
            self.install()


if __name__ == '__main__':
    unittest.main()
