# ovm_guest

ovm_guest Ansible-module

- ovmm_vm
  state:
    - [present](#creation-vm)
    - [absent](#deleting-vm)
    - [start](#starting-vm)
    - [stop](#stopping-vm)
    - [import](#import-file)
    - [clone_assembly](#cloning-vm)
    - [clone_template](#cloning-vm)
    - [eject](#eject-disk)

## Import file
**Import iso, ovf, ova files to repository**

Example for [import OVA file](./examples/importOV.yml)  
Example for [import ISO file](./examples/importISO.yml)  

The module checks for the presence of an uploaded file in the repository; if this file is present, the download is ignored.  
The check is done in the appExists function.  
On ovm, the file will be located:
   * <b> Repositories-> repo-> Assemblies </b> (For older ovm 3.3 versions)
   * <b> Repositories-> repo-> Virtual Appliances </b> (For newer ovm 3.4 versions) 

## Creation Vm
**Create virtual machine**

Example for [create VM](./examples/createVm.yml)    

The parameter <b>boot_order</b> can take the following values:  
- CDROM
- PXE
- Disk

The parameter <b>networks</b> takes the value of ovm network objects.  
For create two or more network cards you need to use the next format:  

networks: ['ovm_network1', 'ovm_network2']  
or
```
networks:
  - ovm_network1
  - ovm_network2
```

The parameter <b>disks</b> takes the following values:  
0 - The name of the disk being created in the repository  
1 - Disk size in GiB. In module - (disk_size * (2**30))  
2 - Ovm repository  

For create two or more disks you need to use the next format:    
disks: [["vmdiskname-root", 30, "ovm_repository"]]  
or  
```
disks:
  - ["vmdiskname-root", 30, "ovm_repository"]
  - ["vmdiskname-u1", 50, "ovm_repository"]
```

The parameter <b>map_disk</b> is used for map iso disk.  

## Deleting Vm
Example for [delete vm](./examples/deleteVm.yml)  

## Cloning Vm
Example for [clone from template](./examples/cloneFromTemp.yml)  

## Starting Vm
Example for [start vm](./examples/startVm.yml)  

## Stopping Vm
Example for [stop vm](./examples/stopVm.yml)  

## Eject Disk
Example for [ejecting disk](./examples/ejectIso.yml)  
