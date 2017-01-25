# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2016 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from unittest import mock

import snapcraft
import subprocess

from snapcraft import _options, tests


class OptionsTestCase(tests.TestCase):

    scenarios = [
        ('amd64', dict(
            machine='x86_64',
            gcc_target='x86_64-linux-gnu',
            expected_arch_triplet='x86_64-linux-gnu',
            expected_deb_arch='amd64',
            expected_kernel_arch='x86')),
        ('amd64-kernel-i686-userspace', dict(
            machine='x86_64',
            gcc_target='i386-linux-gnu',
            expected_arch_triplet='i386-linux-gnu',
            expected_deb_arch='i386',
            expected_kernel_arch='x86')),
        ('i686', dict(
            machine='i686',
            gcc_target='i686-linux-gnu',
            expected_arch_triplet='i386-linux-gnu',
            expected_deb_arch='i386',
            expected_kernel_arch='x86')),
        ('armv7l', dict(
            machine='armv7l',
            gcc_target='arm-linux-gnueabihf',
            expected_arch_triplet='arm-linux-gnueabihf',
            expected_deb_arch='armhf',
            expected_kernel_arch='arm')),
        ('aarch64', dict(
            machine='aarch64',
            gcc_target='aarch64-linux-gnu',
            expected_arch_triplet='aarch64-linux-gnu',
            expected_deb_arch='arm64',
            expected_kernel_arch='arm64')),
        ('aarch64-kernel-armv7l-userspace', dict(
            machine='aarch64',
            gcc_target='arm-linux-gnueabihf',
            expected_arch_triplet='arm-linux-gnueabihf',
            expected_deb_arch='armhf',
            expected_kernel_arch='arm')),
        ('ppc', dict(
            machine='ppc',
            gcc_target='powerpc-linux-gnu',
            expected_arch_triplet='powerpc-linux-gnu',
            expected_deb_arch='powerpc',
            expected_kernel_arch='powerpc')),
        ('ppc64le', dict(
            machine='ppc64le',
            gcc_target='powerpc64le-linux-gnu',
            expected_arch_triplet='powerpc64le-linux-gnu',
            expected_deb_arch='ppc64el',
            expected_kernel_arch='powerpc')),
        ('ppc64le-kernel-ppc-userspace', dict(
            machine='ppc64le',
            gcc_target='powerpc-linux-gnu',
            expected_arch_triplet='powerpc-linux-gnu',
            expected_deb_arch='powerpc',
            expected_kernel_arch='powerpc')),
        ('s390x', dict(
            machine='s390x',
            gcc_target='s390x-linux-gnu',
            expected_arch_triplet='s390x-linux-gnu',
            expected_deb_arch='s390x',
            expected_kernel_arch='s390x'))
    ]

    @mock.patch('subprocess.PIPE')
    @mock.patch('subprocess.run')
    @mock.patch('platform.machine')
    def test_architecture_options(
            self, mock_platform_machine,
            mock_subprocess_run, mock_subprocess_pipe):
        mock_platform_machine.return_value = self.machine
        mock_subprocess_run.return_value = mock.MagicMock(stderr=str.encode("""
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/usr/lib/gcc/{target}/5/lto-wrapper
Target: {target}
Configured with: ../src/configure -v
Thread model: posix
gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.4)
            """.format(target=self.gcc_target)))

        options = snapcraft.ProjectOptions()
        mock_subprocess_run.assert_called_once_with(
            ['gcc', '-v'], stderr=mock_subprocess_pipe)
        self.assertEqual(options.arch_triplet, self.expected_arch_triplet)
        self.assertEqual(options.deb_arch, self.expected_deb_arch)
        self.assertEqual(options.kernel_arch, self.expected_kernel_arch)

    @mock.patch('subprocess.PIPE')
    @mock.patch('subprocess.run')
    @mock.patch('platform.machine')
    def test_architecture_options_from_platform(
            self, mock_platform_machine, mock_subprocess_run,
            mock_subprocess_pipe):
        mock_platform_machine.return_value = self.machine
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['gcc', '-v'])

        options = snapcraft.ProjectOptions()
        mock_subprocess_run.assert_called_once_with(
            ['gcc', '-v'], stderr=mock_subprocess_pipe)

        if self.id().endswith('-userspace)'):
            self.skipTest(
                reason='unsupported platform with mismatching userspace')

        self.assertEqual(options.arch_triplet, self.expected_arch_triplet)
        self.assertEqual(options.deb_arch, self.expected_deb_arch)
        self.assertEqual(options.kernel_arch, self.expected_kernel_arch)


class GccTargetTests(tests.TestCase):

    @mock.patch('subprocess.PIPE')
    @mock.patch('subprocess.run')
    def test_gcc_target_parsing(
            self, mock_subprocess_run, mock_subprocess_pipe):
        mock_subprocess_run.return_value = mock.MagicMock(stderr=(b"""
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/usr/lib/gcc/my-awesome-target/5/lto-wrapper
Target: my-awesome-target
Configured with: ../src/configure -v
Thread model: posix
gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.4)
            """))

        self.assertEqual(_options._get_gcc_target(), 'my-awesome-target')

    @mock.patch('subprocess.PIPE')
    @mock.patch('subprocess.run')
    def test_gcc_target_missing(
            self, mock_subprocess_run, mock_subprocess_pipe):
        mock_subprocess_run.return_value = mock.MagicMock(stderr=(b"""
COLLECT_GCC=gcc
Configured with: ../src/configure -v
Thread model: posix
gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.4)
            """))

        self.assertIsNone(_options._get_gcc_target())

    @mock.patch('subprocess.PIPE')
    @mock.patch('subprocess.run')
    def test_gcc_target_empty(
            self, mock_subprocess_run, mock_subprocess_pipe):
        mock_subprocess_run.return_value = mock.MagicMock(stderr=(b"""
COLLECT_GCC=gcc
Target:
Configured with: ../src/configure -v
Thread model: posix
gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.4)
            """))

        self.assertIsNone(_options._get_gcc_target())

    @mock.patch('subprocess.PIPE')
    @mock.patch('subprocess.run')
    def test_get_gcc_target_call_fails(
            self, mock_subprocess_run, mock_subprocess_pipe):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['gcc', '-v'])

        self.assertIsNone(_options._get_gcc_target())
        mock_subprocess_run.assert_called_once_with(
            ['gcc', '-v'], stderr=mock_subprocess_pipe)

    @mock.patch('snapcraft._options._ARCH_TRANSLATIONS')
    def test_get_platform_from_gcc_triplet(self, mock_arch_translations):
        archs = {'foo': {'triplet': 'bar-linux-gnu'}}
        mock_arch_translations.items.side_effect = archs.items
        self.assertEqual(
            _options._get_platform_from_gcc_triplet('bar-linux-gnu'), 'foo')

    @mock.patch('snapcraft._options._ARCH_TRANSLATIONS')
    def test_get_platform_from_gcc_triplet_overriding(
            self, mock_arch_translations):
        archs = {
            'foo': {
                'triplet': 'bar-linux-gnu',
                'gcc_triplet': 'barbar-linux-gnu'
            }
        }
        mock_arch_translations.items.side_effect = archs.items
        self.assertEqual(
            _options._get_platform_from_gcc_triplet('barbar-linux-gnu'), 'foo')

    @mock.patch('snapcraft._options._ARCH_TRANSLATIONS')
    def test_get_platform_from_gcc_triplet_invalid(
            self, mock_arch_translations):
        archs = {
            'foo': {
                'triplet': 'bar-linux-gnu',
                'gcc_triplet': 'barbar-linux-gnu'
            }
        }
        mock_arch_translations.items.side_effect = archs.items
        self.assertIsNone(
            _options._get_platform_from_gcc_triplet('foo-linux-gnu'))
