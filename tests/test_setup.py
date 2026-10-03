import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

LIB = Path(__file__).resolve().parents[1] / 'lib'


def module(name):
    spec = importlib.util.spec_from_file_location(name, LIB / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


setup = module('setup')
boot = module('boot')


class SetupTests(unittest.TestCase):
    def test_only_selected_overlays_are_staged_and_existing_ones_are_preserved(self):
        self.assertEqual(setup.required_repositories({'groups': ['kde']}), [])
        self.assertEqual(setup.required_repositories({'groups': ['gaming']}), ['guru', 'steam-overlay'])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def clone(command, **kwargs):
                destination = Path(command[-1])
                (destination / 'profiles').mkdir(parents=True)
                (destination / 'profiles/repo_name').write_text(destination.name + '\n')
                return subprocess.CompletedProcess(command, 0)
            with patch.object(setup, 'existing_repository', side_effect=lambda name: Path('/existing') if name == 'guru' else None), patch.object(setup.shutil, 'which', return_value='/usr/bin/git'), patch.object(setup.subprocess, 'run', side_effect=clone) as run:
                fetched = setup.stage_repositories({'groups': ['gaming']}, root)
                self.assertEqual(set(fetched), {'steam-overlay'})
                self.assertEqual(run.call_count, 1)
                config = root / 'etc/portage/repos.conf/fiw-dots-steam-overlay.conf'
                self.assertIn(str(root / 'var/db/repos/steam-overlay'), config.read_text())
                self.assertFalse((root / 'etc/portage/repos.conf/fiw-dots-guru.conf').exists())

    def test_flatpak_failure_is_reported_and_installs_are_user_scoped(self):
        reports = []
        installed = set()
        def run(command, **kwargs):
            if command[:2] == ['flatpak', 'info']:
                return subprocess.CompletedProcess(command, 0 if command[-1] in installed else 1)
            if 'install' in command and command[-1] == 'org.localsend.localsend_app':
                installed.add(command[-1])
                return subprocess.CompletedProcess(command, 0)
            if 'install' in command:
                return subprocess.CompletedProcess(command, 1)
            return subprocess.CompletedProcess(command, 0)
        with patch.object(setup.os, 'geteuid', return_value=1000), patch.object(setup.shutil, 'which', return_value='/usr/bin/flatpak'), patch.object(setup.subprocess, 'run', side_effect=run) as commands, patch.object(setup, 'write_report', side_effect=lambda kind, report: reports.append(report)):
            with self.assertRaises(RuntimeError):
                setup.install_flatpaks({'flatpaks': list(setup.FLATPAKS)}, lambda *args: 'install')
            self.assertEqual(reports[0]['installed'], ['org.localsend.localsend_app'])
            self.assertEqual(reports[0]['failed'], ['org.vinegarhq.Sober'])
            for call in commands.call_args_list:
                self.assertIn('--user', call.args[0])

    def test_missing_services_are_reported_and_enabled_without_starting(self):
        reports = []
        def run(command, **kwargs):
            if 'show' in command:
                state = 'not-found\n' if command[-1] == 'wireplumber.service' else 'loaded\n'
                return subprocess.CompletedProcess(command, 0, state)
            return subprocess.CompletedProcess(command, 0)
        with patch.object(setup.os, 'geteuid', return_value=1000), patch.object(setup.subprocess, 'run', side_effect=run) as commands, patch.object(setup, 'write_report', side_effect=lambda kind, report, system: reports.append(report)):
            setup.enable_services({'services': ['audio', 'network']}, lambda *args: 'enable')
            self.assertEqual(reports[0]['missing'], ['wireplumber.service'])
            self.assertEqual(reports[0]['enabled'], ['pipewire.socket', 'pipewire-pulse.socket'])
            for call in commands.call_args_list:
                self.assertNotIn('--now', call.args[0])
                self.assertIn('--user', call.args[0])


class BootTests(unittest.TestCase):
    def test_managed_limine_block_preserves_other_entries_and_rejects_bad_markers(self):
        original = 'timeout: 8\n\n/Other OS\n    protocol: efi\n    path: boot():/other.efi\n'
        block = boot.render_limine([{'version': 'test-gentoo'}], 'root=UUID=target-root ro')
        merged = boot.merge_limine(original, block)
        self.assertTrue(merged.startswith(original))
        self.assertEqual(boot.merge_limine(merged, block), merged)
        with self.assertRaises(RuntimeError):
            boot.merge_limine(original + boot.BEGIN, block)

    def test_edited_limine_entries_get_proposal_while_external_entries_remain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / 'kernel';image.write_bytes(b'kernel')
            initrd = root / 'initrd';initrd.write_bytes(b'initrd')
            images = [{'version': 'test-gentoo', 'kernel': str(image), 'initrd': str(initrd)}]
            saved = {'mode': 'limine', 'esp': str(root / 'esp'), 'cmdline': 'root=UUID=target-root ro'}
            (root / 'esp').mkdir()
            with patch.object(boot, 'discover_esp', return_value={'path': saved['esp']}), patch.object(boot, 'kernel_images', return_value=images):
                saved = boot.refresh(saved, root / 'backups')
                config = root / 'esp/EFI/Fiw-Gentoo/limine.conf'
                config.write_text(config.read_text() + '\n/Other OS\n    protocol: efi\n')
                saved = boot.refresh(saved, root / 'backups')
                self.assertIn('/Other OS', config.read_text())
                config.write_text(config.read_text().replace('target-root', 'user-edited-root'))
                previous = config.read_text()
                boot.refresh(saved, root / 'backups')
                self.assertEqual(config.read_text(), previous)
                proposals = list(config.parent.glob('limine.conf.new.*'))
                self.assertEqual(len(proposals), 1)
                self.assertIn('/Other OS', proposals[0].read_text())

    def test_failed_grub_generation_does_not_replace_existing_menu(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'boot';(folder / 'grub').mkdir(parents=True)
            config = folder / 'grub/grub.cfg';config.write_text('working config\n')
            images = []
            def run(command, **kwargs):
                Path(command[-1]).write_text('partial failed config')
                raise subprocess.CalledProcessError(1, command)
            # /boot sources prevent normalization writes outside the staging dir.
            images = [{'version': 'test', 'kernel': '/boot/kernel-test', 'initrd': '/boot/initramfs-test.img'}]
            saved = {'mode': 'grub', 'esp': str(root), 'config_hash': boot.file_hash(config)}
            with patch.object(boot, 'GRUB_DIRECTORY', folder), patch.object(boot, 'discover_esp', return_value={'path': str(root)}), patch.object(boot, 'kernel_images', return_value=images), patch.object(boot.subprocess, 'run', side_effect=run):
                with self.assertRaises(subprocess.CalledProcessError):
                    boot.refresh(saved, root / 'backups')
            self.assertEqual(config.read_text(), 'working config\n')
            self.assertFalse(list(config.parent.glob('.*.tmp')))

    def test_firmware_add_preserves_bootorder_and_repeat_default_does_not_duplicate(self):
        target = {'disk': '/dev/testdisk', 'partition': 2, 'partuuid': 'target-partition'}
        loader = '/EFI/Fiw-Gentoo/BOOTX64.EFI'
        command = boot.firmware_commands(target, 'limine', loader, 'add', '')[0]
        self.assertIn('--create-only', command)
        self.assertNotIn('--create', command)
        listing = 'BootOrder: 0001,0002\nBoot0002* Fiw-Gentoo-limine HD(2,GPT,target-partition)/File(\\EFI\\Fiw-Gentoo\\BOOTX64.EFI)\n'
        commands = boot.firmware_commands(target, 'limine', loader, 'default', listing)
        self.assertEqual(commands, [['efibootmgr', '--bootorder', '0002,0001']])
        self.assertEqual(boot.firmware_commands(target, 'limine', loader, 'add', listing), [])
        self.assertEqual(boot.plan('keep'), {'mode': 'keep', 'changes': []})


if __name__ == '__main__':
    unittest.main()
