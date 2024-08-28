litp create -t os-profile -p /software/profiles/rhel_6_4 -o name=sample-profile version=rhel6 path=/var/www/html/6.4/os/x86_64/ arch=x86_64 breed=redhat
litp create -t system -p /infrastructure/systems/system_ms -o system_name=MS1VM

litp create -t system -p /infrastructure/systems/system_1 -o system_name=MN1VM
litp create -t disk -p /infrastructure/systems/system_1/disks/disk_0 -o name=hd0 size=28G bootable=true uuid=ATA_VBOX_HARDDISK_VBe2bee164-af9c23e3
litp create -t disk -p /infrastructure/systems/system_1/disks/lun_0 -o name=lun_0 size=40G bootable=false uuid=30000000fc85c928

litp create -t system -p /infrastructure/systems/system_2 -o system_name=MN2VM
litp create -t disk -p /infrastructure/systems/system_2/disks/disk_0 -o name=hd0 size=28G bootable=true uuid=ATA_VBOX_HARDDISK_VBf9ea7964-e6d13a01
litp create -t disk -p /infrastructure/systems/system_2/disks/lun_0 -o name=lun_0 size=40G bootable=false uuid=30000000fc85c928

litp create -t network -p /infrastructure/networking/networks/mgmt -o name=mgmt subnet=10.10.10.0/24 litp_management=true
litp create -t storage-profile -p /infrastructure/storage/storage_profiles/profile_1
litp create -t volume-group -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg_1 -o volume_group_name=vg_root
litp create -t file-system -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg_1/file_systems/root -o type=ext4 mount_point=/ size=4G snap_size=100
litp create -t file-system -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg_1/file_systems/swap -o type=swap mount_point=swap size=2G
litp create -t physical-device -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg_1/physical_devices/disk_0 -o device_name=hd0

litp inherit -p /ms/system -s /infrastructure/systems/system_ms

litp create -t deployment -p /deployments/d1
litp create -t cluster -p /deployments/d1/clusters/c1
litp create -t node -p /deployments/d1/clusters/c1/nodes/node1 -o hostname=node1
litp inherit -p /deployments/d1/clusters/c1/nodes/node1/system -s /infrastructure/systems/system_1
litp inherit -p /deployments/d1/clusters/c1/nodes/node1/os -s /software/profiles/rhel_6_4

litp create -t network-interface -p /deployments/d1/clusters/c1/nodes/node1/network_interfaces/nic0 -o network_name=mgmt ipaddress=10.10.10.101

litp inherit -p /deployments/d1/clusters/c1/nodes/node1/storage_profile -s /infrastructure/storage/storage_profiles/profile_1
litp create -t node -p /deployments/d1/clusters/c1/nodes/node2 -o hostname=node2
litp inherit -p /deployments/d1/clusters/c1/nodes/node2/system -s /infrastructure/systems/system_2
litp inherit -p /deployments/d1/clusters/c1/nodes/node2/os -s /software/profiles/rhel_6_4

litp create -t network-interface -p /deployments/d1/clusters/c1/nodes/node2/network_interfaces/nic0 -o network_name=mgmt ipaddress=10.10.10.102
litp inherit -p /deployments/d1/clusters/c1/nodes/node2/storage_profile -s /infrastructure/storage/storage_profiles/profile_1