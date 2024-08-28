##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import unittest
import os.path
from mock import Mock, patch

from litp.core.plugin_manager import PluginManager
from litp.core.model_manager import ModelManager
from litp.core.plugin_context_api import PluginApiContext
from litp.extensions.core_extension import CoreExtension
from litp.core.execution_manager import ExecutionManager
from volmgr_extension.volmgr_extension import VolMgrExtension, FileSystemValidator, ROOT_FS_MOUNT_POINT, \
FileSystemValidatorSnapSize, FileSystemValidatorBackupSnapSize

from litp.core.validators import ValidationError
from litp.core.extension import ViewError

class TestVolMgrExtension(unittest.TestCase):
    def setUp(self):
        self.model_manager = ModelManager()
        self.validator = self.model_manager.validator
        self.plugin_manager = PluginManager(self.model_manager)
        self.context = PluginApiContext(self.model_manager)

        core_ext = CoreExtension()
        self.volmgr_ext = VolMgrExtension()

        self.prop_types = dict()
        for prop_type in self.volmgr_ext.define_property_types():
            self.prop_types[prop_type.property_type_id] = prop_type

        self.item_types = dict()
        for item_type in self.volmgr_ext.define_item_types():
            self.item_types[item_type.item_type_id] = item_type

        for ext in [core_ext, self.volmgr_ext]:
            self.plugin_manager.add_property_types(ext.define_property_types())
            self.plugin_manager.add_item_types(ext.define_item_types())
            if ext == core_ext:
                self.plugin_manager.add_default_model()

    def tearDown(self):
        pass

    def test_valid_fs_type(self):
        self.assertTrue('fs_type' in self.prop_types)
        type_pt = self.prop_types['fs_type']

        bad_value_return = self.validator._run_property_type_validators(type_pt, 'type', 'foo')
        self.assertEquals(1, len(bad_value_return))
        self.assertEquals('ValidationError', bad_value_return[0].error_type)

        self.assertEquals([], self.validator._run_property_type_validators(type_pt, 'type', 'ext4'))
        self.assertEquals([], self.validator._run_property_type_validators(type_pt, 'type', 'swap'))
        self.assertEquals([], self.validator._run_property_type_validators(type_pt, 'type', 'xfs'))
        self.assertEquals([], self.validator._run_property_type_validators(type_pt, 'type', 'vxfs'))

    def test_valid_snap_size(self):
        self.assertTrue('snap_size' in self.prop_types)

        snap_size_pt = self.prop_types['snap_size']

        for value in ['invalid10', '23valid', '43.5', '-1', '102', '6786']:
            errors = self.validator._run_property_type_validators(snap_size_pt, 'snap_size', value)
            expected = ValidationError(property_name='snap_size',
                                       error_message="Invalid value '%s'. Value must be an integer between 0 and 100" % value)
            self.assertEquals([expected], errors)

        for value in ['0', '1', '23', '99', '100']:
            errors = self.validator._run_property_type_validators(snap_size_pt, 'snap_size', value)
            self.assertEquals([], errors)

    def test_valid_mount_point(self):
        self.assertTrue('fs_mount_point' in self.prop_types)
        mountpoint_pt = self.prop_types['fs_mount_point']

        bad_value_return = self.validator._run_property_type_validators(mountpoint_pt, 'mount_point', 'foo')
        self.assertEquals(1, len(bad_value_return))
        self.assertEquals('ValidationError', bad_value_return[0].error_type)

        for value in ['swap', '/', '//', '/var/', '/var/foo']:
            errors = self.validator._run_property_type_validators(mountpoint_pt, 'mount_point', value)
            self.assertEquals([], errors)

    def test_valid_driver(self):
        self.assertTrue('vol_driver' in self.prop_types)
        driver_pt = self.prop_types['vol_driver']

        bad_value_return = self.validator._run_property_type_validators(driver_pt, 'volume_driver', 'foo')
        self.assertEquals(1, len(bad_value_return))
        self.assertEquals('ValidationError', bad_value_return[0].error_type)

        self.assertEquals([], self.validator._run_property_type_validators(driver_pt, 'volume_driver', 'lvm'))
        self.assertEquals([], self.validator._run_property_type_validators(driver_pt, 'volume_driver', 'vxvm'))

    def _create_mock_profiles(self):
        self.model_manager.create_core_root_items()
        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='a')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/home', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='a')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/1_vg_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/opt', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/ovg',
                volume_group_name='bravo')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_A',
                mount_point='/usr', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_0_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_B',
                mount_point='/tmp', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/opt', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/ovg',
                volume_group_name='bravo')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_A',
                mount_point='/usr', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_B',
                mount_point='/', size='12G')


        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/rvg',
                volume_group_name='alpha')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_A',
                mount_point='/', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_B',
                mount_point='/var', size='12G')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/ovg',
                volume_group_name='bravo')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_A',
                mount_point='/usr', size='20G')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_2_root_fs/'\
                        'volume_groups/ovg/file_systems/fs_B',
                mount_point='/', size='12G')

        self.model_manager.create_item('storage-profile',
                '/infrastructure/storage/storage_profiles/vxfs')
        self.model_manager.create_item('volume-group',
                '/infrastructure/storage/storage_profiles/vxfs/'\
                        'volume_groups/rvg',
                volume_group_name='delta')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/vxfs/'\
                        'volume_groups/rvg/file_systems/vol0',
                size='20G', name='vol1')
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/'\
                        'volume_groups/rvg/file_systems/vol1',
                size='12G', name='vol1')

    def _get_storage_profile(self, item_id):
        for sp_qi in self.context.query('storage-profile'):
            if item_id == sp_qi.item_id:
                return sp_qi
        raise Exception("Could not find storage profile with item_id {0}".format(item_id))

    def _get_fs(self, item_id):
        for fs_qi in self.context.query('file-system'):
            if item_id == fs_qi.item_id:
                return fs_qi
        raise Exception("Could not find file system with item_id {0}".format(item_id))

    def test_root_vg_view_single_vg_no_root(self):
        self._create_mock_profiles()
        sp_qi = self._get_storage_profile('1_vg_0_root_fs')
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage profile /infrastructure/storage/'\
                    'storage_profiles/1_vg_0_root_fs does not have a VG with '\
                    'a FS mounted on \'/\'', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_single_vg_single_root(self):
        self._create_mock_profiles()
        sp_qi = self._get_storage_profile('1_vg_1_root_fs')
        self.assertEquals('alpha', sp_qi.view_root_vg)

    def test_root_vg_view_single_vg_two_roots(self):
        self._create_mock_profiles()
        sp_qi = self._get_storage_profile('1_vg_2_root_fs')
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage profile /infrastructure/storage/'\
                    'storage_profiles/1_vg_2_root_fs has a VG \'a\' with >1 '\
                    'FS mounted on \'/\': fs_A,fs_B', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_two_vgs_no_root(self):
        self._create_mock_profiles()
        sp_qi = self._get_storage_profile('2_vgs_0_root_fs')
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage profile /infrastructure/storage/'\
                    'storage_profiles/2_vgs_0_root_fs does not have a VG '\
                    'with a FS mounted on \'/\'', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_two_vgs_two_roots(self):
        self._create_mock_profiles()
        sp_qi = self._get_storage_profile('2_vgs_2_root_fs')
        try:
            getattr(sp_qi, 'view_root_vg')
        except ViewError as ve:
            self.assertEquals('Storage profile /infrastructure/storage/'\
                    'storage_profiles/2_vgs_2_root_fs has >1 VG with a FS '\
                    'mounted on \'/\': alpha,bravo', str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_root_vg_view_two_vgs_single_root(self):
        self._create_mock_profiles()
        sp_qi = self._get_storage_profile('2_vgs_1_root_fs')
        self.assertEquals('bravo', sp_qi.view_root_vg)

    @patch('litp.core.plugin_context_api.PluginApiContext.snapshot_name', return_value='snapshot')
    def test_snap_size_view_deployment_snapshot(self, _):
        self._create_mock_profiles()
        self.assertEqual('100', self._get_fs('fs_A').current_snap_size)

    @patch('litp.core.plugin_context_api.PluginApiContext.snapshot_name', return_value='pepe')
    def test_snap_size_view_named_snapshot(self, _):
        self._create_mock_profiles()
        self.model_manager.create_item('file-system',
                '/infrastructure/storage/storage_profiles/2_vgs_1_root_fs/'\
                        'volume_groups/rvg/file_systems/fs_snapsize2',
                mount_point='/opt', size='20G', backup_snap_size='50')
        # will use the new property if it is set
        self.assertEqual('50', self._get_fs('fs_snapsize2').current_snap_size)
        # and will use the old one if the other snap size is not set
        self.assertEqual('100', self._get_fs('fs_A').current_snap_size)

    @patch('litp.core.plugin_context_api.PluginApiContext.snapshot_name', return_value='')
    def test_snap_size_view_no_snapshot(self, _):
        self._create_mock_profiles()
        try:
            self._get_fs('fs_A').current_snap_size
        except ViewError as ve:
            self.assertEquals("No snapshot object was found", str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_litpcds_11003(self):

        self.model_manager.create_core_root_items()

        sp = self.model_manager.create_item(
            'storage-profile',
            '/infrastructure/storage/storage_profiles/sp1'
        )
        vg = self.model_manager.create_item(
            'volume-group',
            '/infrastructure/storage/storage_profiles/sp1/volume_groups/vg1',
            volume_group_name='vg1'
        )
        pd = self.model_manager.create_item(
            'physical-device',
            '/infrastructure/storage/storage_profiles/sp1/volume_groups/vg1'
            '/physical_devices/lun_0',
            device_name='lun_0'
        )

        sp.set_applied()
        vg.set_applied()
        pd.set_applied()

        # attempt to update a read-only property
        errors = self.model_manager.update_item(
            '/infrastructure/storage/storage_profiles/sp1/volume_groups/vg1'
            '/physical_devices/lun_0',
            device_name='other_lun'
        )

        self.assertEqual(1, len(errors))

        e = errors[0]

        self.assertEqual(
            'InvalidRequestError', e.error_type
        )
        self.assertEqual(
            'Unable to modify readonly property: device_name',
            e.error_message
        )

    def test_litpcds_12940(self):

        fs = Mock(item_id='fs12940',
                  applied_properties={'mount_point':ROOT_FS_MOUNT_POINT},
                  mount_point=None)

        vg = Mock(item_id='vg12940',
                  volume_group_name='vg12490',
                  file_systems=[fs])

        sp = Mock(item_id='sp12940',
                  volume_groups=[vg])

        try:
            VolMgrExtension.cb_select_root_vg(None, sp)
        except ViewError as ve:
            expected = "'/' mount point can not be removed " \
                       "for VG 'vg12490', FS 'fs12940'"
            self.assertEquals(expected, str(ve))
        else:
            self.fail('Should have thrown a ViewError')

    def test_for_litpcds_9877(self):

        vld8r = FileSystemValidatorSnapSize()
        vld8rBackup = FileSystemValidatorBackupSnapSize()

        properties = {'type': 'ext4', 'size': '10G'}

        # 'snap_size' is missing
        error = vld8r.validate(properties)
        self.assertEquals(None, error)

        # ----
        # Still the wrong 'type' value
        properties['snap_size'] = '50'
        error = vld8r.validate(properties)
        self.assertEquals(None, error)

        # ----
        # 'size' and 'snap_size' numbers large enough
        properties['type'] = 'vxfs'
        properties['mount_point'] = '/test_9877'
        error = vld8r.validate(properties)
        self.assertEquals(None, error)

        # ----
        # With a different 'size' numbers remain large enough
        for size in ['20T', '100M']:
            properties['size'] = size
            error = vld8r.validate(properties)
            self.assertEquals(None, error)

        # ----

        # With a 'snap_size' of 0 checking is disabled
        properties['snap_size'] = '0'
        error = vld8r.validate(properties)
        self.assertEquals(None, error)
        properties['snap_size'] = '50'

        # ----

        msg = 'Invalid "snap_size" value. ' + \
              'The "size" and "snap_size" properties on the ' + \
              '"file-system" would combine to result in a ' + \
              'snapshot cache object size less than the ' + \
              'minimum of 13M'
        expected = ValidationError(property_name="snap_size",
                                   error_message=msg)

        # With an invalid 'size' things go awry
        properties['size'] = 'bogusG'
        error = vld8r.validate(properties)
        self.assertEquals(expected, error)
        properties['size'] = '100M'

        # ----

        # With a reduced 'snap_size' things also go awry
        properties['snap_size'] = '1'
        error = vld8r.validate(properties)
        self.assertEquals(expected, error)

        msg = ('Invalid "backup_snap_size" value. ' + \
               'The "size" and "backup_snap_size" properties on' + \
               ' the "file-system" would combine to result in a ' + \
               'snapshot cache object size less than the ' + \
               'minimum of 13M')
        expected_backup = ValidationError(property_name="backup_snap_size",
                                   error_message=msg)

        errors = []
        properties['backup_snap_size'] = '1'
        errors.append(vld8r.validate(properties))
        errors.append(vld8rBackup.validate(properties))
        self.assertEquals(2, errors.__len__())
        self.assertEquals(expected, errors[0])
        self.assertEquals(expected_backup, errors[1])

        errors = []
        properties['backup_snap_size'] = '50'
        errors.append(vld8r.validate(properties))
        errors.append(vld8rBackup.validate(properties))
        self.assertEquals(2, errors.__len__())
        self.assertEquals(expected, errors[0])

        errors = []
        properties['backup_snap_size'] = '0'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(1, errors.__len__())
        self.assertEquals(expected, errors[0])

        errors = []
        properties['snap_size'] = '50'
        properties['backup_snap_size'] = '1'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(1, errors.__len__())
        self.assertEquals(expected_backup, errors[0])

        errors = []
        properties['backup_snap_size'] = '50'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(0, errors.__len__())

        errors = []
        properties['backup_snap_size'] = '0'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(0, errors.__len__())

        errors = []
        properties['snap_size'] = '0'
        properties['backup_snap_size'] = '1'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(1, errors.__len__())
        self.assertEquals(expected_backup, errors[0])

        errors = []
        properties['backup_snap_size'] = '50'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(0, errors.__len__())

        errors = []
        properties['backup_snap_size'] = '0'
        error = vld8r.validate(properties)
        errors.append(error) if error else None
        error = vld8rBackup.validate(properties)
        errors.append(error) if error else None
        self.assertEquals(0, errors.__len__())
