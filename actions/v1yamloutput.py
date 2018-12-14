#!/usr/bin/python
import os
import sys
from novaclient import client
from keystoneauth1 import session
import yaml
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
from charmhelpers.fetch import apt_install
from charmhelpers.core.hookenv import (
    log,
    ERROR,
)
from charmhelpers.contrib.openstack.context import IdentityServiceContext
config =  hookenv.config()

ram_allocation_ratio = config['ram-allocation-ratio']
cpu_allocation_ratio = config['cpu-allocation-ratio']

av = 0

dictionary = {
    "a": [1, 2],
    "b": [4, 5] }



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
    if api_version == 2:
      try:
            from keystoneclient.auth.identity import v2
            from keystoneclient import session
      except ImportError:
            if six.PY2:
                apt_install(["python-keystoneclient"], fatal=True)
            else:
                apt_install(["python3-keystoneclient"], fatal=True)
            from keystoneclient.auth.identity import v2
            from keystoneclient import session
      auth = v2.Password(auth_url=endpoint, username=context['admin_user'], password=context['admin_password'], tenant_name=context['admin_tenant_name'])
    if api_version == 3:
      try:
            from keystoneclient import session
            from keystoneclient.auth.identity import v3
      except ImportError:
            if six.PY2:
                apt_install(["python-keystoneclient"], fatal=True)
            else:
                apt_install(["python3-keystoneclient"], fatal=True)

            from keystoneclient.auth import token_endpoint
            from keystoneclient import session
            from keystoneclient.auth.identity import v3
      auth = v3.Password(project_name=context['admin_tenant_name'], project_domain_name='Default', auth_url=endpoint, username=context['admin_user'], password=context['admin_password'], user_domain_name=context['admin_domain_id'])
    return session.Session(auth=auth)


def main():
   nova = get_apiversion_and_endpoint()
   capacityoutput = []
   flavorcapacityoutput = []
   hypervisors = nova.hypervisors.list()
   flavors = nova.flavors.list()
   output = {}
   flavordicitionary = {}
   totaldictionary = {}
   hpdic = {}
   s = ''
   for flavor in flavors:
     totalinstances_per_flavor = 0
     flavor_name = str(flavor.name)
     for hypervisor in hypervisors:
       hostname = str(hypervisor.hypervisor_hostname)
       totalinstances =  can_host_flavor(hypervisor, flavor, ram_allocation_ratio, cpu_allocation_ratio)
       totalinstances_per_flavor += totalinstances
       if not  hypervisor.hypervisor_hostname in capacityoutput:
         capacityoutput += [ hypervisor.hypervisor_hostname,' ']
       capacityoutput.append('{}:  {} '.format(flavor.name, totalinstances))
       flavordicitionary.update({ flavor_name : totalinstances, })
       hpdic.update({ hostname : { flavor_name : totalinstances, } }) if hostname not in hpdic else hpdic[hostname].update({ flavor_name : totalinstances, })
#    hpdic.update({str(hostname) : flavordicitionary})
     flavorcapacityoutput.append('Total_capacity flavor {}:  {} \n'.format(flavor.name,totalinstances_per_flavor ))
     totaldictionary.update( {str(flavor.name) : totalinstances_per_flavor, } )
     hpdic.update({"Total Capacity" : totaldictionary, } ) 
#   hpdic.update({str(hostname) : flavordicitionary})
   flavorcapacityoutput += capacityoutput
   print(s.join(flavorcapacityoutput))
   hookenv.action_set({'get-capacity-info': yaml.dump(hpdic)})
   #hookenv.action_set({'get-capacity-info': s.join(flavorcapacityoutput)})
main()

