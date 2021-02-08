#!/usr/bin/python
##

# Ansible is an open source software project and is licensed under the GNU General Public License version 3, 
# as detailed in the Ansible source code: https://github.com/ansible/ansible/blob/devel/COPYING

DOCUMENTATION = '''
---

module: ovmm_vm
short_description: This is the Infrastructure Lifecycle module for Oracle VM and Oracle Private Cloud Appliance. It manages creation, deletion, cloning start and stop of Virtual Machines inside Oracle-VM, and additional
description:
  - Module to manage Virtual Machine definitions inside Oracle-VM
notes:
    - This module works with OVM 3.3 and 3.4 and Oracle PCA 2.3.1 +
    - Author: v.babich@sigma-it.ru
requirements:
    - requests package
    - json package
options:
    state:
        description:
            - The desired state of the Virtual Machine
                - present - Create a new VM if it doesn't exist. The VM of desired config, along with Virtual NICs attached to specified networks and virtual disks will be created using play.yml playbook
                - absent - Delete an existing VM with its Virtual Disks
                - start - Start a VM if it is stopped on OVM
                - stop - Gracefully Stop a running VM on OVM
                - import - Import ISO/OVF/OVA files to OVM repository
                - clone_assembly - Cloning VM from assembly or Virtual Appliance
                - clone_template - Cloning VM from VM-template
                - eject - Delete disk mappings from VM
    name:
        description:
            - The virtual-machine name, inside oracle-vm the vm-name is
            - not unique. It uses the vm-id as the unique identifier.
        required: False
    ovm_user:
        description:
            - The OVM admin-user used to connect to the OVM-Manager. It is required for authentication if certificate authentication for Oracle VM is not enabled.
        required: True 
    ovm_pass:
        description:
            - The password of the OVM admin-user. Required if certificate authentication is not enabled
        required: True
    ovm_hostname:
        description:
            - The hostname/IP address for Oracle-VM. For Oracle PCA, this is the VIP of the Management Nodes.
        required: True
    ovm_port:
        description:
	    - The port number that OVM listens on
        required: True
    server_pool:
        description:
            - The Oracle-VM server-pool where to create/find the
            - Virtual Machine. It is required when a new VM needs to be created.
        required: False
    repository:
        description:
            - The Oracle-VM storage repository where to store the Oracle-VM
            - definition. Needs to be specified when a new VM needs to be created.
        required: False
    networks:
        description:
	    - The networks for the Virtual NICs to be attached to a new VM. The networks are supplied as a list. If a VM needs multiple VNICs on the same network, that network name should be entered multiple times.
	required: False
    disks:
        description:
	    - The specs of virtual disks to be attached to the new VM. These have to be specified as a list of lists [['diskname1', disk1_size in bytes, 'Repository_name'], [['diskname2', disk2_size in bytes, 'Repository_name'],...]
        required: False
    memory:
        description:
            - The amount of memory in MB for the VM
    vcpu_cores:
        description:
            - The number of physical CPU cores to be assigned to the VM
    max_vcpu_cores:
        description:
            - The max number of processors that can be assigned to VM. This number depends on domain object_type
                - XEN_PVM- 256
                - XEN_HVM- 128
    operating_system:
        description:
            - The OS of the virtual machine
    vm_domain_type:
        description:
            - The domain type specifies the Virtual-Machine
            - virtualization mode.
        required: False
        default: "XEN_HVM_PV_DRIVERS"
        choices: [ XEN_HVM, XEN_HVM_PV_DRIVERS, XEN_PVM, LDOMS_PVM, UNKNOWN ]
    vmTemplate:
        description:
            - Virtual template name in OVM repository
    assembly:
        description:
            - OVA or OVF template name in OVM repository
    vmCloneDefinition:
        description:
            - Clone definition name for vmTemplate
    appliance_url:
        description:
            - HTTP/HTTPS urls for import OVA/OVF/ISO files to OVM repository
    map_disk:
        description:
            - Disk name in repository ISO, for mapping ISO file to VM
    boot_order:
        description:
            - Boot order for VM. Params: [PXE,DISK,CDROM]
    vmrootpassword:
        description:
            - Root password for preconfigured ovmd daemon
    ipv4_addr:
        description:
            - Ipv4 address format x.x.x.x for preconfigured ovmd daemon
    ipv4_netmask:
        description:
            - Ipv4 netmask format x.x.x.x for preconfigured ovmd daemon
    ipv4_gateway:
        description:
            - Ipv4 gateway format x.x.x.x for preconfigured ovmd daemon
    ipv4_dns_servers:
        description:
            - Ipv4 dns servers, use it as list:
    ipv4_bootp:
        description:
            - Ipv4 address configuration. Params: [static,dhcp]
'''

EXAMPLES = '''
    - name: Create a Virtual Machine
      ovmm_vm:
        state: present
        name: ST_vm33
        ovm_user: admin
        ovm_pass: xxxx
        ovm_host: dhcp-10-211-54-xx
        ovm_port: 7002
        server_pool: SP1
        repository: MyRepo
        memory: 4096
        vcpu_cores: 4
        boot_order: PXE
        networks: ['VMnet', 'VMnet']
        disks: [['disk1', 1073741824, 'MyRepo'], ['disk2', 1073741824, 'MyRepo']]

'''

RETURN = '''

'''

################################################################
try:
    import json
    import requests
    requests.packages.urllib3.disable_warnings()
    import logging
    try:
        # for Python 3
        from http.client import HTTPConnection
    except ImportError:
        from httplib import HTTPConnection
    HTTPConnection.debuglevel = 1

    #enable logging for request calls (put, post, delete) to make it easier to debug in case of an error
    logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
    logging.getLogger().setLevel(logging.DEBUG)
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.DEBUG)
    urllib3_logger.propagate = True

    import time
except ImportError:
    requests_exists=False

 
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
disable_warnings()	
    


def auth(ovm_user, ovm_pass):
    """ Set authentication-credentials.
    Oracle-VM usually generates a self-signed certificate,
    Set Accept and Content-Type headers to application/json to
    tell Oracle-VM we want json, not XML. The Basic Authorization sends Oracle VM username and password with each request for authentication. If certificate based authenitication is set up, user name and password are not needed.
    """
    session = requests.Session()
    session.auth = (ovm_user, ovm_pass)
#    session.cert ='/root/mycerts/OVMSignedCertificate.pem'
    session.verify=False #Path to certificate on the OVM Manager host. Default path is '/u01/app/oracle/ovm-manager-3/domains/ovm_domain/security/ovmca.pem'  
    session.headers.update({
        'Accept': 'application/json',
        'Content-Type': 'application/json' })
    return session 

def monitor_job(restsession, baseUri, job_id):
    while True:
        response = restsession.get(
            baseUri+'/Job/'+job_id)
        job = response.json()
        if job['summaryDone']:
            if job['jobRunState'] == 'FAILURE':
                raise Exception('Job failed: %s' % job.error)
            elif job['jobRunState'] == 'SUCCESS':
                if 'resultId' in job.keys():
                    return job['resultId']
                break
            elif job['jobRunState'] == 'RUNNING':
                continue
            else:
                break

#Function to make sure each job gets completed before going to the next step in code execution
def wait_for_job(joburi,restsession):
    while True:
        time.sleep(1)
        r=restsession.get(joburi)
        job=r.json()
        if job['summaryDone']:
            print('{name}: {runState}'.format(name=job['name'], runState=job['jobRunState']))
            if job['jobRunState'].upper() == 'FAILURE':
                raise Exception('Job failed: {error}'.format(error=job['error']))
            elif job['jobRunState'].upper() == 'SUCCESS':
                if 'resultId' in job:
                    return job['resultId']
                break
            else:
                break

def get_VM_from_name(restsession,baseUri, module):
    uri='{base}/Vm/id'.format(base=baseUri)
    r=restsession.get(uri)
    for obj in r.json():
        if 'name' in obj.keys():
            if obj['name']==module.params['name']:
                return obj
        raise Exception('Failed to find object named {name}'.format(name=obj_name))

def get_id_from_name(restsession,baseUri, resource, resource_name):
    uri='{base}/{res}/id'.format(base=baseUri, res=resource)
    r=restsession.get(uri)
    for obj in r.json():
        if 'name' in obj.keys(): 
            if obj['name']==resource_name:
                return obj
    raise Exception('Failed to find id for {name}'.format(name=resource_name))

#Fuction for import iso/ovf/ova file to ovm-repository
def import_repofile(restsession, baseUri, module):
    
    app_url = module.params['appliance_url'].lower()
    payload_urls = module.params['appliance_url']
    repoId = get_id_from_name(restsession, baseUri, 'Repository', module.params['repository'])['value']

    if app_url.endswith('.iso'):
        import_type='importVirtualDisk'
        uri = '{base}/Repository/{repoid}/{repoim}?diskType=VIRTUAL_CDROM'.format(
            base=baseUri,
            repoid=repoId,
            repoim=import_type,
        )
    elif app_url.endswith('.ova') or app_url.endswith('.ovf'):
        import_type='importAssembly'
        uri = '{base}/Repository/{repoid}/{repoim}'.format(
            base=baseUri,
            repoid=repoId,
            repoim=import_type,
        )
    else:
        #Exit with unknown type
        module.exit_json(msg="Unknown file type", changed=False)

    data = {'urls': [payload_urls]}
    response = restsession.put(uri, data=json.dumps(data))
    job = response.json()
    monitor_job(restsession, baseUri, job['id']['value'])
    module.exit_json(msg="File imported", changed=True)


def get_VM_Info_by_Id(module, baseUri, VMId, restsession):
    uri='{base}/Vm/{VMId}'.format(base=baseUri, VMId=VMId)
    info=restsession.get(uri)
    infoJson=json.loads(info.text)
    return infoJson


def vmExists(module, restsession, baseUri):
    uri='{base}/Vm/id'.format(base=baseUri)
    vmResult=restsession.get(uri)
    for obj in vmResult.json():
        if 'name' in obj.keys():
            if obj['name']==module.params['name']:
                return True
    return False


def get_VirtDisk_Info_by_DiskMap_ID(restsession, baseUri, module, VMDiskMapID):
    uri='{base}/VmDiskMapping/{VMDiskMapID}/VirtualDisk'.format(base=baseUri, VMDiskMapID=VMDiskMapID)
    virtdiskinfo=restsession.get(uri)
    virtdiskinfoJson=json.loads(virtdiskinfo.text)
    return virtdiskinfoJson


def delVmDiskMap(restsession, baseUri, module, VMDiskMapID):
    id=get_id_from_name(restsession,baseUri,'Vm',module.params['name'])['value']
    vminfo=get_VM_Info_by_Id(module, baseUri, id, restsession)
    uri='{base}/Vm/{VMId}/VmDiskMapping/{VMDiskMapId}'.format(base=baseUri, VMId=id, VMDiskMapId=VMDiskMapID)

    delVmDiskMapResult=restsession.delete(uri)
    delVmDiskMapJson=json.loads(delVmDiskMapResult.text)
    wait = wait_for_job(delVmDiskMapJson['id']['uri'], restsession)


def delVirtualDisk(restsession, baseUri, module, virtualDisk):
    
    uri='{base}/Repository/{repo_id}/VirtualDisk/{VirtualDiskID}'.format(base=baseUri, repo_id=virtualDisk['repositoryId']['value'], VirtualDiskID=virtualDisk['id']['value'])
    delVirtualDiskRes=restsession.delete(uri)
    delVirtualDiskJson=json.loads(delVirtualDiskRes.text)
    wait = wait_for_job(delVirtualDiskJson['id']['uri'], restsession)

def startVM(restsession, module, baseUri):
    vminfo=get_VM_Info_by_Id(module, baseUri, get_id_from_name(restsession,baseUri,'Vm', module.params['name'])['value'], restsession)

    if vminfo["vmRunState"]=='STOPPED':
        uri='{base}/Vm/{id}/start'.format(base=baseUri, id=vminfo['id']['value'])
        startVM=restsession.put(uri)
        jsonstartVM=json.loads(startVM.text)
        wait = wait_for_job(jsonstartVM['id']['uri'], restsession)
        module.exit_json(msg="VM started", changed=True)
    
    else:
        module.exit_json(msg="VM already running", changed=False)
	 

def stopVM(restsession, module, baseUri):
    
    vminfo=get_VM_Info_by_Id(module, baseUri, get_id_from_name(restsession,baseUri,'Vm',module.params['name'])['value'], restsession)

    if vminfo["vmRunState"]=='RUNNING':
        uri='{base}/Vm/{id}/stop'.format(base=baseUri, id=vminfo['id']['value'])
        stopVM=restsession.put(uri)
        jsonstopVM=json.loads(stopVM.text)
        wait = wait_for_job(jsonstopVM['id']['uri'], restsession)
        module.exit_json(msg="VM stopped", changed = True)

    else:
        module.exit_json(msg="VM is already stopped", changed = False)


def configVm(restsession, module, baseUri, newVmId):

    if module.params['map_disk']:
        uri = '{base}/Vm/{vmid}/VmDiskMapping'.format(base=baseUri, vmid=newVmId['value'])
        md_id = get_id_from_name(restsession, baseUri, 'VirtualDisk', module.params['map_disk'])
        data={
            "virtualDiskId": {
                "type": "com.oracle.ovm.mgr.ws.model.VirtualDisk",
                "value": md_id['value']
            },
            "diskTarget": 3,
        }
        map_disk = restsession.post(uri, data=json.dumps(data))
        map_job = map_disk.json()
        map_stat = wait_for_job(map_job['id']['uri'],restsession)

    # Create a Virtual Disk of the specified config
    disklist=module.params['disks']

    for i in range(len(disklist)):
       repo_id=get_id_from_name(restsession, baseUri, 'Repository', disklist[i][2])['value']
       disk_size = int(disklist[i][1]) * (2**30)
       Data3={
             'name': disklist[i][0],
             'size': disk_size,
             }
       payload={
               'sparse': True
               }
       uri3='{base}/Repository/{repoid}/VirtualDisk'.format(base=baseUri, repoid=repo_id)
       createdisk=restsession.post(uri3, data=json.dumps(Data3), params = payload)
       jsoncreatedisk=createdisk.json()
       diskid = wait_for_job(jsoncreatedisk['id']['uri'], restsession)


    # Create a VmDiskMapping to represent association of VirtualDisk to Vm

       uri4='{base}/Vm/{vmid}/VmDiskMapping'.format(base=baseUri, vmid=newVmId['value'])
       Data4={
             'virtualDiskId': diskid,
             'diskTarget': i,
             }
       createVmDiskMap=restsession.post(uri4, data=json.dumps(Data4))
       createVmDiskMapJson=createVmDiskMap.json()
       VmDiskMapId = wait_for_job(createVmDiskMapJson['id']['uri'], restsession)


    # Create a VNic on the desired network
    netlist=module.params['networks']
    for net in range(len(netlist)):
       networkid=get_id_from_name(restsession, baseUri, 'Network', netlist[net])
       Data={
         'networkId': networkid,
       }

       uri2 ='{base}/Vm/{vmId}/VirtualNic'.format(base=baseUri, vmId=newVmId['value'])
       addNic=restsession.post(uri2, data=json.dumps(Data))
       jsonaddNic=addNic.json()
       wait = wait_for_job(jsonaddNic['id']['uri'], restsession)


    module.exit_json(msg="VM created", changed=True)

#Function for modify VM attributes
def modifyVm(restsession, module, baseUri, newVmId):
    jsonVmInfo = get_VM_Info_by_Id(module, baseUri, newVmId, restsession)
    uri='{base}/Vm/{vmid}'.format(base=baseUri, vmid=newVmId)

    Data={
        'name': module.params['name'],
        'description': module.params['description'],
        'vmDomainType': module.params['vm_domain_type'],
        'memory': module.params['memory'],
        'memoryLimit': module.params['max_memory'],
        'cpuCount': module.params['vcpu_cores'],
        'cpuCountLimit': module.params['max_vcpu_cores'],
        'bootOrder': module.params['boot_order'],
    }
    
    for key,value in Data.items():
        jsonVmInfo[key] = value

    modifyvm = restsession.put(uri, data=json.dumps(jsonVmInfo))
    modifyvmjson = modifyvm.json()
    # wait for the job to complete
    wait_for_job(modifyvmjson['id']['uri'], restsession)

'''
Function for set up additional params for Vm after startup
Attention! For using this params you need:
    - Os type OL-Linux with uek kernel
    - additional packages: libovmapi xenstoreprovider ovmd python-simplejson xenstoreprovider
    - configure ovm-template-initialconfig
For additional information see this: 
    - https://www.oracle.com/technetwork/server-storage/vm/ovm-templates-wp-2027191.pdf
'''
def configVM_afterStartup(restsession, module, baseUri, newVmId):
    uri='{base}/Vm/{vmid}/sendMessage'.format(base=baseUri,vmid=newVmId)

    dns_to_line = module.params["ipv4_dns_servers"]
    dns_servers = ",".join(str(x) for x in dns_to_line)

    #All params in payload depends on your ovm-chkconfig configuration!
    #You can change this depends on your config
    payload=[
	    {
        "key": "com.oracle.linux.network.hostname",
	    "value": module.params["name"]
	    },
	    {
	    "key": "com.oracle.linux.network.device.0",
	    "value": "eth0"
	    },
	    {
	    "key": "com.oracle.linux.network.onboot.0",
   	    "value": "yes"
	    },
	    {
	    "key": "com.oracle.linux.network.bootproto.0",
   	    "value": module.params["ipv4_bootp"]
	    },
	    {
	    "key": "com.oracle.linux.network.ipaddr.0",
   	    "value": module.params["ipv4_addr"]
	    },
	    {
	    "key": "com.oracle.linux.network.netmask.0",
   	    "value": module.params["ipv4_netmask"]
	    },
	    {
	    "key": "com.oracle.linux.network.gateway.0",
   	    "value": module.params["ipv4_gateway"]
	    },
	    {
	    "key": "com.oracle.linux.network.dns-servers.0",
   	    "value": dns_servers
	    },
	]

    configvm = restsession.put(uri, data=json.dumps(payload))
    configvmjson = configvm.json()
    wait = wait_for_job(configvmjson['id']['uri'], restsession)
    
    #Sleep after sent first params
    time.sleep(10)

    payload_pass=[
            {
            "key": "com.oracle.linux.root-password",
            "value": module.params["vmrootpassword"]
            },
            ]
    result = restsession.put(uri, data=json.dumps(payload_pass))
    resultjson = result.json()
    wait = wait_for_job(resultjson['id']['uri'], restsession)
    time.sleep(50)

#Function for cloning Vm from template
def cloneVM_template(restsession, module, baseUri):
    vm_id = get_id_from_name(restsession, baseUri, 'Vm', module.params['vmTemplate'])['value']
    uri = '{base}/Vm/{vmid}/clone'.format(base=baseUri, vmid=vm_id)
    
    sp_id = get_id_from_name(restsession, baseUri, 'ServerPool', module.params['server_pool'])['value']
    clonedef_id = get_id_from_name(restsession, baseUri, 'VmCloneDefinition', module.params['vmCloneDefinition'])['value']
    data={
         'vmCloneDefinitionId': clonedef_id,
         'serverPoolId': sp_id,
         'createTemplate': False,
         }

    clonetemplate = restsession.put(uri, params=data)
    clonetemplatejson = clonetemplate.json()
    newvmid = wait_for_job(clonetemplatejson['id']['uri'], restsession)

    modifyVm(restsession, module, baseUri, newvmid['value'])

    uri2 = '{base}/Vm/{id}/start'.format(base=baseUri, id=newvmid['value'])
    startVM = restsession.put(uri2)
    jsonstartVM = startVM.json()
    wait = wait_for_job(jsonstartVM['id']['uri'], restsession)

    configVM_afterStartup(restsession, module, baseUri, newvmid['value'])
 
    module.exit_json(msg="VM created and started with id {vmID}".format(vmID=newvmid['value']), changed=True)

#Function for cloning Vm from assembly(appliance)
def createVM_assembly(restsession, module, baseUri):
    repo_id = get_id_from_name(restsession, baseUri, 'Repository', module.params['repository'])
    sp_id = get_id_from_name(restsession, baseUri, 'ServerPool', module.params['server_pool'])['value']

    assembly_id = get_id_from_name(restsession, baseUri, 'Assembly', module.params['assembly'])['value']

    assembly = restsession.get('{base}/Assembly/{id}'.format(base=baseUri,id=assembly_id))
    assemblyjson = assembly.json()
    for i in assemblyjson['assemblyVmIds']:
        uri='{base}/AssemblyVm/{id}/createVm'.format(base=baseUri,id=i['value'])
        r = restsession.put(uri)
        job = r.json()
        # wait for the job to complete
        vmid = wait_for_job(job['id']['uri'], restsession)
        print("vmid =%s\n",vmid)
        
    modifyVm(restsession, module, baseUri, vmid['value'])
    module.exit_json(msg="VM created with id {vmID}".format(vmID=vmid), changed=True)

def createVM(restsession, module, baseUri):
    repo_id=get_id_from_name(restsession,baseUri,'Repository', module.params['repository'])
    sp_id=get_id_from_name(restsession,baseUri,'ServerPool',module.params['server_pool'])
    Data={
        'name': module.params['name'],
        'description': 'A virtual machine created using the REST API',
        'vmDomainType': module.params['vm_domain_type'],
        'repositoryId': repo_id,
        'serverPoolId': sp_id,
        'memory': module.params['memory'],
        'memoryLimit': module.params['max_memory'],
        'cpuCount': module.params['vcpu_cores'],
        'cpuCountLimit': module.params['max_vcpu_cores'],
        'bootOrder': module.params['boot_order'],
        'osType': module.params['operating_system'],
    }
    uri = '{base}/Vm'.format(base=baseUri)

    createVMvar = restsession.post(uri, data=json.dumps(Data))
    job = createVMvar.json()
    # wait for the job to complete
    vm_id = wait_for_job(job['id']['uri'], restsession)

    configVm(restsession, module, baseUri, vm_id)

def deleteVM(restsession, module, baseUri):
    vmid=get_id_from_name(restsession, baseUri, 'Vm', module.params['name'])['value']
    vminfo=get_VM_Info_by_Id(module, baseUri, get_id_from_name(restsession, baseUri, 'Vm', module.params['name'])['value'], restsession)
    if vminfo["vmRunState"]=='RUNNING':
        vmuri='{base}/Vm/{id}/stop'.format(base=baseUri, id=vmid)
        vmstop=restsession.put(vmuri)
        jsonvmstop=json.loads(vmstop.text)
        wait = wait_for_job(jsonvmstop['id']['uri'], restsession)
    else:
        pass    
 
    #Remove the disk mapping to Vm and then remove the disk
    for obj in vminfo['vmDiskMappingIds']:
        vmDiskinfo=get_VirtDisk_Info_by_DiskMap_ID(restsession,baseUri, module, obj['value'])
        delVmDiskMap(restsession, baseUri, module, obj['value'])
        delVirtualDisk(restsession, baseUri, module, vmDiskinfo)

    uri='{base}/Vm/{VMId}'.format(base=baseUri, VMId=vmid)
    delVMRes=restsession.delete(uri)
    delVMResJson=json.loads(delVMRes.text)
    wait = wait_for_job(delVMResJson['id']['uri'], restsession)

    module.exit_json(msg="VM Deleted", changed=True)

#Function for delete Disk mapping, for example eject ISO file from Vm    
def delVmDiskMap(restsession, baseUri, module):
    
    id = get_id_from_name(restsession, baseUri, 'Vm', module.params['name'])['value']
    uri = '{base}/Vm/{vmid}/VmDiskMapping'.format(base=baseUri, vmid=id)

    vm_info = restsession.get(uri)
    disk_list = vm_info.json()
    iso_map = ""
    for i in disk_list:
        if "iso" in i['name']:
            iso_map = i['id']['value']

    if len(iso_map) == 0:
        module.exit_json(msg="Vm disk mount not found", changed=False)

    uri = '{base}/Vm/{VMId}/VmDiskMapping/{VMDiskMapId}'.format(base=baseUri, VMId=id, VMDiskMapId=iso_map)
    delVmDiskMapResult = restsession.delete(uri)
    delVmDiskMapJson = json.loads(delVmDiskMapResult.text)
    wait = wait_for_job(delVmDiskMapJson['id']['uri'], restsession)
    module.exit_json(msg="Vm disk ejected", changed=True)

#Function for check file in repository
def appExists(restsession, baseUri, module):

    app_load = module.params['appliance_url'].rsplit('/', 1)[-1]
    repoId = get_id_from_name(restsession, baseUri, 'Repository', module.params['repository'])['value']

    uri = '{base}/Repository/{repoid}'.format(base=baseUri, repoid=repoId)

    response = restsession.get(uri)
    obj = response.json()

    if app_load.endswith('.iso'):
        for i in obj['virtualDiskIds']:
            if i['name'] == app_load:
                return True
    elif app_load.endswith('.ova') or app_load.endswith('.ovf'):
        for i in obj['assemblyIds']:
            if i['name'] == app_load:
                return True
                
    return False


def main():
    changed = False
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent', 'start', 'stop', 'import', 'clone_assembly', 'clone_template', 'eject']),
            name=dict(required=False),
            description=dict(required=False),
            ovm_user=dict(required=True),
            ovm_pass=dict(required=True),
            ovm_host=dict(required=True),
            ovm_port=dict(required=True),
            server_pool=dict(required=False),
            repository=dict(required=False),
            vm_domain_type=dict(default='XEN_HVM_PV_DRIVERS', choices=[
                    "XEN_HVM",
                    "XEN_HVM_PV_DRIVERS",
                    "XEN_PVM",
                    "LDOMS_PVM",
                    "UNKNOWN"]),
            vmTemplate=dict(required=False),
            assembly=dict(required=False),
            vmCloneDefinition=dict(required=False),
            appliance_url=dict(required=False),
            memory=dict(required=False, default=4096, type='int'),
            max_memory=dict(required=False, default=None, type='int'),
            vcpu_cores=dict(required=False, default=2, type='int'),
            max_vcpu_cores=dict(required=False, default=None, type='int'),
            operating_system=dict(required=False),
            networks=dict(type='list', required=False),
            map_disk=dict(required=False),
            disks=dict(required=False, type='list'),
            boot_order=dict(required=False, type='list'),
            vmrootpassword=dict(required=False),
            ipv4_addr=dict(required=False),
            ipv4_netmask=dict(required=False),
            ipv4_gateway=dict(required=False),
            ipv4_dns_servers=dict(required=False, type='list'),
            ipv4_bootp=dict(required=False, default='dhcp'),
        )
    )

    restsession=auth(module.params['ovm_user'], module.params['ovm_pass'])
    baseUri='https://{hostName}:{port}/ovm/core/wsapi/rest'.format(hostName=module.params['ovm_host'],port=module.params['ovm_port'])


    if module.params['state'] == "present":
        if not vmExists(module, restsession, baseUri):
            createVM(restsession, module, baseUri)
        else:
            id = get_id_from_name(restsession, baseUri, 'Vm', module.params['name'])['value']
            module.exit_json(msg='VM exists and has id {vmID}'.format(vmID=id), changed=False)

    elif module.params['state']=="start":
        if not vmExists(module, restsession, baseUri):
            module.exit_json(msg="VM doesn't exist", changed=False)
        else:
            startVM(restsession, module, baseUri)

    elif module.params['state']=="stop":
        if not vmExists(module, restsession, baseUri):
            module.exit_json(msg="VM doesn't exist", changed=False)
        else:
            stopVM(restsession, module, baseUri)

    elif module.params['state']=="absent":
        if vmExists(module, restsession, baseUri):
            deleteVM(restsession, module, baseUri)
        else:
            module.exit_json(msg="VM doesn't exist", changed=False)

    elif module.params['state'] == "import":
        if not appExists(restsession, baseUri, module):
            import_repofile(restsession, baseUri, module)
        else:
            module.exit_json(msg='File exists in repository', changed=False)

    elif module.params['state'] == "eject":
        if vmExists(module, restsession, baseUri):
            delVmDiskMap(restsession, baseUri, module)
        else:
            module.exit_json(msg="VM doesn't exist", changed=False)

    elif module.params['state'] == "clone_template":
        if not vmExists(module, restsession, baseUri):
            cloneVM_template(restsession, module, baseUri)
        else:
            id = get_id_from_name(restsession, baseUri, 'Vm', module.params['name'])['value']
            module.exit_json(msg='VM exists and has id {vmID}'.format(vmID=id), changed=False)
        
    elif module.params['state'] == "clone_assembly":
        if not vmExists(module, restsession, baseUri):
            createVM_assembly(restsession, module, baseUri)
        else:
            id = get_id_from_name(restsession, baseUri, 'Vm', module.params['name'])['value']
            module.exit_json(msg='VM exists and has id {vmID}'.format(vmID=id), changed=False)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()

