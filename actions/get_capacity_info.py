#!/usr/bin/python
import os
import sys
from novaclient import client
from keystoneauth1 import session

_path = os.path.dirname(os.path.realpath(__file__))
_root = os.path.abspath(os.path.join(_path, '..'))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)

_add_path(_root)

#sys.path.append('../')
import charmhelpers.core.hookenv as hookenv
#import hooks.nova_cc_utils as ncc_utils
import charmhelpers.contrib.openstack.keystone as keystone
from charmhelpers.core.hookenv import (
    log,
    ERROR,
)
from charmhelpers.contrib.openstack.context import IdentityServiceContext
config =  hookenv.config()

ram_allocation_ratio = config['ram-allocation-ratio']
cpu_allocation_ratio = config['cpu-allocation-ratio']

av = 0




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

def get_apiversion_and_endpoint():
    context = IdentityServiceContext()()
    if not context:
        msg = "Identity service context cannot be generated"
        log(msg, level=ERROR)
        raise ValueError(msg)


    if int(context['api_version']) == 2:
      api_version = 2
      endpoint = '%s://%s:%s/v%s' % (context['service_protocol'],
                               context['service_host'],
                               context['service_port'],
                               float(context['api_version']))
    else:
      api_version = 3
      endpoint = '%s://%s:%s/v%s' % (context['service_protocol'],
                               context['service_host'],
                               context['service_port'],
                               context['api_version'])
    novaapi = client.Client('2.2', session=get_keystone_session(endpoint, api_version, context))
    return novaapi
def get_keystone_session(endpoint, api_version, context):
    av = context['api_version']
    hookenv.action_set({'get-capacity-info': endpoint})
    from keystoneclient import session
    if api_version == 2:
      from keystoneclient.auth.identity import v2
      auth = v2.Password(auth_url=endpoint, username=context['admin_user'], password=context['admin_password'], tenant_name=context['admin_tenant_name'])
    if api_version == 3:
      from keystoneclient.auth.identity import v3
      auth = v3.Password(project_name=context['admin_tenant_name'], project_domain_name='Default', auth_url=endpoint, username=context['admin_user'], password=context['admin_password'], user_domain_name='Default')
    return session.Session(auth=auth)
def main():
   nova = get_apiversion_and_endpoint()
   capacityoutput = []
   flavorcapacityoutput = []
   hypervisors = nova.hypervisors.list()
   flavors = nova.flavors.list()
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
   hookenv.action_set({'get-capacity-info': s.join(flavorcapacityoutput)})
main()

