##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.validators import ValidationError, ItemValidator
from litp.core.extension import ModelExtension, ViewError
from litp.core.model_type import ItemType, Collection, Property, PropertyType
from litp.core.model_type import View

ROOT_FS_MOUNT_POINT = '/'
LVM_FS_DEFAULT_MOUNT_OPTIONS = 'defaults,x-systemd.device-timeout=300'

VXFS_CACHE_OBJ_MIN_SIZE_MB = 13


class VolMgrExtension(ModelExtension):
    """
    The LITP volmgr model extension enables the modelling of LVM and VxVM
    volume management.
    """

    def define_property_types(self):

        property_types = []

        expr = '^(ext4|xfs|vxfs|swap)$'
        error_desc = "Value must be a valid file system type: " + \
                     "one of 'ext4', 'xfs', 'vxfs' or 'swap'"
        property_types.append(PropertyType('fs_type',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^(swap|(/[a-zA-Z0-9_/-]*))$'
        error_desc = "Value must be 'swap' or a valid directory path"
        property_types.append(PropertyType('fs_mount_point',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^([a-zA-Z0-9_/][a-zA-Z0-9_/-]*)$'
        error_desc = "Value must be a valid file system name containing " + \
                     "only alphanumerics, underscores, hyphens and slashes"
        property_types.append(PropertyType('fs_name',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^[1-9][0-9]{0,}[MGT]$'
        error_desc = "Value must be a valid file system size with a " + \
                     "non-zero numeral followed by one of 'M', 'G' or 'T'"
        property_types.append(PropertyType('fs_size',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^(([0-9])|([1-9][0-9])|(100))$'
        error_desc = "Value must be an integer between 0 and 100"
        property_types.append(PropertyType('snap_size',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^[^,-]+$'
        error_desc = "Value must be a valid Litp Disk Item ID"
        property_types.append(PropertyType('disk_id',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^([a-zA-Z0-9_/][a-zA-Z0-9_/-]*)$'
        error_desc = "Value must be a valid volume group name containing " + \
                     "only alphanumerics, underscores, hyphens and slashes"
        property_types.append(PropertyType('vol_group',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^(lvm|vxvm)$'
        error_desc = "Value must be a valid Litp volume driver type: " + \
                     "one of 'lvm' or 'vxvm'"
        property_types.append(PropertyType('vol_driver',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        expr = '^([a-zA-Z0-9_-]*)$'
        error_desc = "Value must be a valid snapshot name containing " + \
                     "only alphanumerics, underscores and hyphens"
        property_types.append(PropertyType('snap_name',
                                           regex=expr,
                                           regex_error_desc=error_desc))

        return property_types

    def define_item_types(self):

        # Properties
        type_prop = Property('fs_type',
            prop_description='File system type.',
            required=True,
            updatable_rest=False,
            default='xfs')

        mount_prop = Property('fs_mount_point',
            prop_description='File system mount point. The value of this'
                             ' property must not be any system directory'
                             ' that can be used by the operating system.',
            updatable_rest=True,
            required=False)

        mount_options_prop = Property('any_string',
            prop_description='The mount options are passed through to the '
                              'nodes\'s /etc/fstab file.',
            updatable_plugin=True)

        fsck_pass_prop = Property("integer",
            prop_description='File system fsck pass. The value of this '
                             'property controls if fsck checking is '
                             'performed on the file system',
            default="2",
            updatable_plugin=True)

        size_prop = Property('fs_size',
            prop_description='File system size.',
            required=True)

        snap_size_prop = Property('snap_size',
            prop_description='The percentage of the file-system size ' +
                             'that is reserved for snapshots.',
           required=True,
           default='100',
           configuration=False)

        backup_snap_size_prop = Property('snap_size',
            prop_description='The percentage of the file-system size ' +
                             'that is reserved for named snapshots.',
           required=False,
           configuration=False)

        snap_name_prop = Property('snap_name',
            prop_description='Deprecated. Please do not use.',
            required=False,
            deprecated=True,
            updatable_rest=False,
            updatable_plugin=True)

        disk_prop = Property('disk_id',
            prop_description='Identifier of physical device item.',
            required=True,
            updatable_rest=False)

        vg_prop = Property('vol_group',
            prop_description='Name of volume group item.',
            updatable_rest=False,
            required=True)

        driver_prop = Property('vol_driver',
            prop_description='Logical volume managment driver. ' +
                             'Must be one of ``vxvm`` and ``lvm``.',
            updatable_rest=False,
            required=True,
            default='lvm')

        snap_ext_prop = Property('basic_boolean',
            prop_description='Whether snapshots are managed by a plugin ' +
                             'external to the storage provider.',
            required=False,
            updatable_plugin=False,
            updatable_rest=True,
            default='false')

        # Item Types
        fs_itype = ItemType('file-system',
            item_description='This item type'
                             ' represents a file system.',
            type=type_prop,
            size=size_prop,
            snap_size=snap_size_prop,
            backup_snap_size=backup_snap_size_prop,
            current_snap_size=View('basic_string',
                              VolMgrExtension.cb_select_snap_size,
                              view_description="Selected snap_size."),
            snap_name=snap_name_prop,
            snap_external=snap_ext_prop,
            mount_point=mount_prop,
            fsck_pass=fsck_pass_prop,
            backup_policy=Property("any_string",
                prop_description="Used to specify how the file system "
                             "should be backed up (from snapshot or direct).",
                required=False,
                configuration=False),
            mount_options=mount_options_prop,
            validators=[
                FileSystemValidatorSnapSize(),
                FileSystemValidatorBackupSnapSize(),
                FileSystemValidatorSwapMountPoint(),
            ],
        )

        pd_itype = ItemType('physical-device',
            item_description='This item type'
                             ' represents a physical device.',
            device_name=disk_prop)

        vg_itype = ItemType('volume-group',
            item_description='This item type'
                             ' represents a storage volume group.',
            volume_group_name=vg_prop,
            file_systems=Collection('file-system', min_count=1, max_count=255),
            physical_devices=Collection('physical-device',
                                        min_count=1,
                                        max_count=1))

        sp_itype = ItemType('storage-profile',
            item_description='This item type represents'
                             ' a storage profile, which'
                             ' is a description of volume'
                             ' groups and the file systems'
                             ' that live on them.',
            extend_item='storage-profile-base',
            volume_groups=Collection('volume-group',
                                     min_count=1, max_count=255),
            view_root_vg=View('basic_string',
                              VolMgrExtension.cb_select_root_vg,
                              view_description="Root volume group name."),
            volume_driver=driver_prop)

        item_types = [fs_itype, pd_itype, vg_itype, sp_itype]

        return item_types

    @staticmethod
    def cb_select_root_vg(plugin_api_context, query_item):
        root_vg_claimants = list()

        for vol_group in query_item.volume_groups:
            roots_in_vg = set()
            for fs in vol_group.file_systems:
                if ROOT_FS_MOUNT_POINT == fs.mount_point:
                    roots_in_vg.add(fs.item_id)
                elif fs.mount_point is None and \
                     fs.applied_properties.get('mount_point') == \
                     ROOT_FS_MOUNT_POINT:
                    raise ViewError("'{0}' mount point can not be removed "
                                    "for VG '{1}', FS '{2}'".
                                    format(ROOT_FS_MOUNT_POINT,
                                           vol_group.volume_group_name,
                                           fs.item_id))

            if 1 < len(roots_in_vg):
                raise ViewError("Storage profile {0} has a VG '{1}' with >1 FS"
                        " mounted on '{2}': {3}".format(
                            query_item.get_vpath(),
                            vol_group.volume_group_name,
                            ROOT_FS_MOUNT_POINT,
                            ','.join(list(roots_in_vg))))
            elif 1 == len(roots_in_vg):
                root_vg_claimants.append(vol_group)

        if not root_vg_claimants:
            raise ViewError("Storage profile {0} does not have a VG with a "\
                    "FS mounted on '{1}'".format(query_item.get_vpath(),
                                                 ROOT_FS_MOUNT_POINT))

        if 1 < len(root_vg_claimants):
            raise ViewError("Storage profile {0} has >1 VG with a "\
                    "FS mounted on '{1}': {2}".format(
                        query_item.get_vpath(),
                        ROOT_FS_MOUNT_POINT,
                        ','.join([vg.volume_group_name for vg in \
                                root_vg_claimants])))

        return root_vg_claimants[0].volume_group_name

    @staticmethod
    def cb_select_snap_size(plugin_api_context, query_item):
        """
        Will return snap_size if the user is creating a deployment snapshot
        and backup_snap_size if the user is creating a named snapshot.

        Since backup_snap_size is not mandatory, will return snap_size if
        backup_snap_size is unset.
        """
        snapshot_name = plugin_api_context.snapshot_name()
        if snapshot_name == 'snapshot':
            # deployment snap
            return query_item.snap_size
        elif snapshot_name != '':
            # named snap
            if query_item.backup_snap_size is None:
                return query_item.snap_size
            return query_item.backup_snap_size
        # no snapshot object found
        raise ViewError("No snapshot object was found")


class FileSystemValidator(ItemValidator):
    """
    Custom ItemValidator for file-system item type

    Ensures a file-system of type 'vxfs' will have a snapshot
    cache size of 13MB minimum.
    """

    def validate_with_pro_name(self, properties, snap_size_type):
        if all(prop_name in properties
               for prop_name in ['type', 'size', snap_size_type]) and \
           'vxfs' == properties['type'] and \
           '0' != properties[snap_size_type]:

            size = FileSystemValidator._gen_vxfs_cache_size(
                       FileSystemValidator._get_size_in_mb(properties['size']),
                       properties[snap_size_type])

            if VXFS_CACHE_OBJ_MIN_SIZE_MB > size:
                msg = ('Invalid "%s" value. ' + \
                       'The "size" and "%s" properties on the ' + \
                       '"file-system" would combine to result in a ' + \
                       'snapshot cache object size less than the minimum ' + \
                       'of %sM') % (snap_size_type, snap_size_type, \
                                    VXFS_CACHE_OBJ_MIN_SIZE_MB)
                error = ValidationError(property_name=snap_size_type,
                                        error_message=msg)
                return error

        if properties.get('type', 'xfs') not in ('ext4', 'xfs'):
            if not properties.get('mount_point'):
                msg = 'A "mount_point" must be specified for a ' \
                      '"file-system" of "type" ' \
                      "'{0}'".format(properties.get('type'))
                error = ValidationError(property_name="mount_point",
                                        error_message=msg)
                return error

    @staticmethod
    def _gen_vxfs_cache_size(size, snapshot_size):
        return int(float(size) * float(snapshot_size) / 100.0)

    @staticmethod
    def _get_size_in_mb(size_and_units):
        size_str = size_and_units[:-1]
        unit = size_and_units[-1]

        try:
            size = int(size_str)
        except ValueError:
            return 0

        if unit == 'G':
            size *= 1024
        elif unit == 'T':
            size *= 1024 * 1024

        return size


class FileSystemValidatorSnapSize(FileSystemValidator):
    def validate(self, properties):
        return self.validate_with_pro_name(properties, 'snap_size')


class FileSystemValidatorBackupSnapSize(FileSystemValidator):
    def validate(self, properties):
        return self.validate_with_pro_name(properties, \
                                           'backup_snap_size')


class FileSystemValidatorSwapMountPoint(ItemValidator):
    def validate(self, properties):
        if 'mount_point' in properties and 'type' in properties:
            if properties['mount_point'] == 'swap' and \
                properties['type'] != 'swap':
                msg = 'A "mount_point" of "swap" may only be specified for ' \
                      'a "file-system" of "type" "swap".'
                error = ValidationError(property_name="mount_point",
                                        error_message=msg)
                return error
            if properties['type'] == 'swap' and \
                properties['mount_point'] != 'swap':
                msg = 'A "file-system" of "type" "swap" must also have ' \
                      'a "mount_point" of "swap".'
                error = ValidationError(property_name="mount_point",
                                        error_message=msg)
                return error
