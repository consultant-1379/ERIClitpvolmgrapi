from litp.core.litp_logging import LitpLogger
from litp.migration import BaseMigration
from litp.migration.operations import BaseOperation

log = LitpLogger()

class FileSystemOperation(BaseOperation):
    '''
    Migration operation for fsck_pass property on file-system items.
    '''

    def __init__(self):
        self.new_prop_name = 'fsck_pass'
        self.ROOT_FS_MOUNT_POINT = '/'

    def mutate_forward(self, model_mngr):
        '''
        Finds all file-system instances and adds the fsck_pass property
        depending on the storage-profile type, file-system type and
        mount_point value.

        :param model_mngr: The model manager to which to add the new property.
        :type model_mngr: litp.core.model_manager.ModelManager
        '''

        self.mutate_matched_items(model_mngr, self.do_mutate_fwd, 'forward')

    def mutate_backward(self, model_mngr):
        '''
        Finds all file-system instances and removes the fsck_pass property
        depending on the storage-profile type and file-system type.

        :param model_mngr: The model manager from which to remove the property.
        :type model_mngr: litp.core.model_manager.ModelManager
        '''

        self.mutate_matched_items(model_mngr, self.do_mutate_bwd, 'backward')

    def do_mutate_fwd(self, model_mngr, fs):
        if fs.mount_point == self.ROOT_FS_MOUNT_POINT:
            model_mngr.update_item(fs.vpath , **{self.new_prop_name: '1'})
        else:
            model_mngr.update_item(fs.vpath , **{self.new_prop_name: '2'})

    def do_mutate_bwd(self, model_mngr, fs):
        # Is this even supported?
        pass

    def mutate_matched_items(self, model_mngr, mutate_handler_fn, direction):

        preamble = 'FileSystemOperation.mutate_matched_items: ' + \
                   'mutate direction: ' + direction + ', '

        for infra in model_mngr.find_modelitems('infrastructure'):

            for profile in infra.storage.storage_profiles:

                if profile.volume_driver != 'lvm':
                    continue

                for fs in [fs for vg in profile.volume_groups
                              for fs in vg.file_systems
                           if fs.type == 'ext4' and
                              hasattr(fs, 'mount_point') and fs.mount_point]:
                    mutate_handler_fn(model_mngr, fs)
                    log.trace.info(preamble + "item: " + fs.get_vpath())


class Migration(BaseMigration):
    '''
    Migrates Infrastructure file-system items regarding fsck_pass property
    '''

    version = '1.28.1'
    operations = [FileSystemOperation()]

