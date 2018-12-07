#!/usr/bin/python
import os
import sys
from novaclient import client
from keystoneauth1 import session
from keystoneauth1.identity import v3

_path = os.path.dirname(os.path.realpath(__file__))
_root = os.path.abspath(os.path.join(_path, '..'))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)

_add_path(_root)

import charmhelpers.core.hookenv as hookenv
#import hooks.nova_cc_utils as ncc_utils
import charmhelpers.contrib.openstack.keystone as keystone


keystone = keystone.get_keystone_manager_from_identity_service_context()
sess = keystone.sess
nova = client.Client('2',session=sess)
config =  hookenv.config()

ram_allocation_ratio = config['ram-allocation-ratio']
cpu_allocation_ratio = config['cpu-allocation-ratio']



def can_host_flavor(hypervisor, flavor, ram_allocation_ratio, cpu_allocation_ratio):
    count = 0
    free_mem = hypervisor.memory_mb * ram_allocation_ratio - hypervisor.memory_mb_used
    free_vcpu = hypervisor.vcpus * cpu_allocation_ratio - hypervisor.vcpus_used
    while True:
        if free_mem >= flavor.ram and free_vcpu >= flavor.vcpus:
            count += 1
            free_mem -= flavor.ram
            free_vcpu -= flavor.vcpus
        else:
            return count



def main():
   capacityoutput = []
   flavorcapacityoutput = []
   hypervisors = get_hypervisor_list()
   flavors = get_flavor_list()
   ram_allocation_ratio = 16
   cpu_allocation_ratio = 16
   s = ''
   for flavor in flavors:
     totalinstances_per_flavor = 0
     for hypervisor in hypervisors:
       totalinstances =  can_host_flavor(hypervisor, flavor, ram_allocation_ratio, cpu_allocation_ratio)
       totalinstances_per_flavor += totalinstances
       if not  hypervisor.hypervisor_hostname in capacityoutput:
         capacityoutput += ['\n', hypervisor.hypervisor_hostname,':\n']
       capacityoutput.append('\t can host {} instances of flavor {}\n'.format(totalinstances, flavor.name))

     flavorcapacityoutput.append('Total capacity of flavor {} is {} \n'.format(flavor.name,totalinstances_per_flavor))
   flavorcapacityoutput += capacityoutput
   print(s.join(flavorcapacityoutput))



'''def set_authenticate_parameters():
  username =  ncc_utils.auth_token_config['admin_user']
  password = ncc_utils.auth_token_config['admin_password']
  project_name = ncc_utils.auth_token_config('admin_tenant_name')
  api_version = ncc_utils.auth_token_config('api_version') or '2.0'
  project_domain_name = 'default'
  user_domain_name = 'default'
  ks_auth_host = ncc_utils.auth_token_config('auth_host')
  auth_host =  ks_auth_host
  auth_port = ncc_utils.auth_token_config('auth_port')
  uth_protocol = ncc_utils.auth_token_config('auth_protocol')
  service_protocol = ncc_utils.auth_token_config('service_protocol')
  service_port = ncc_utils.auth_token_config('service_port')
  ks_url = '%s://%s:%s/v%s' % (auth_protocol,
                                 auth_host,
                                 auth_port,
                                 api_version) 
'''
