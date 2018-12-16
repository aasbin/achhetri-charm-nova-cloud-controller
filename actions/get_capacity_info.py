#!/usr/bin/python
import os
import sys
from novaclient import client
from novaclient import exceptions as novaexceptions
from keystoneauth1 import exceptions as keystoneexceptions
import yaml
_path = os.path.dirname(os.path.realpath(__file__))
_root = os.path.abspath(os.path.join(_path, '..'))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)

_add_path(_root)

import charmhelpers.core.hookenv as hookenv
import charmhelpers.contrib.openstack.keystone as keystone
from charmhelpers.fetch import apt_install
from charmhelpers.contrib.openstack.context import IdentityServiceContext
config =  hookenv.config()

ram_allocation_ratio = config['ram-allocation-ratio']
cpu_allocation_ratio = config['cpu-allocation-ratio']





def can_host_flavor(hypervisor, flavor, ram_allocation_ratio, cpu_allocation_ratio):
              count = 0
              free_mem = hypervisor.free_ram_mb * ram_allocation_ratio
              free_vcpu = hypervisor.vcpus * cpu_allocation_ratio - hypervisor.vcpus_used
              while True:
                  if free_mem >= flavor.ram and free_vcpu >= flavor.vcpus:
                      count += 1
                      free_mem -= flavor.ram
                      free_vcpu -= flavor.vcpus
                  else:
                      return count

def get_novaapi():
              context = IdentityServiceContext()()
              try:
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
                  novaapi = client.Client('2.2', session= get_auth_session(endpoint, api_version, context))
                  return novaapi
              except  Exception, e:
                  hookenv.action_fail(e.message)
                  hookenv.action_set({"error": "Did not receive the openstack-auth parameters from identity context"})
                  sys.exit(1)
                  return "unknown"
def get_auth_session(endpoint, api_version, context):
            if api_version == 2:
              try:
                    from keystoneclient.auth.identity import v2
                    from keystoneauth1 import session
              except ImportError:
                    if six.PY2:
                        apt_install(["python-keystoneclient"], fatal=True)
                    else:
                        apt_install(["python3-keystoneclient"], fatal=True)
                    from keystoneclient.auth.identity import v2
                    from keystoneauth1 import session
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
                    from keystoneauth1 import session
                    from keystoneclient.auth.identity import v3
              auth = v3.Password(auth_url=endpoint, username=context['admin_user'], password=context['admin_password'], user_domain_id=context['admin_domain_id'])
            return session.Session(auth=auth)


def main():
           nova = get_novaapi()
           try:
              hypervisors = nova.hypervisors.list()
              flavors = nova.flavors.list()
           except Exception, e:
              msg = str(e)
              hookenv.action_fail(msg)
              hookenv.action_set({"error": " error from api {} ".format(msg)})
              sys.exit(1)
           flavor_instances = {}
           totalcapacity = {}
           output = {}
           for flavor in flavors:
             totalinstances_per_flavor = 0
             flavor_name = str(flavor.name)
             for hypervisor in hypervisors:
               hostname = str(hypervisor.hypervisor_hostname)
               totalinstances =  can_host_flavor(hypervisor, flavor, ram_allocation_ratio, cpu_allocation_ratio)
               totalinstances_per_flavor += totalinstances
               flavor_instances.update({ flavor_name : totalinstances, })
               output.update({ hostname : { flavor_name : totalinstances, } }) if hostname not in output else output[hostname].update({ flavor_name : totalinstances, })
             totalcapacity.update( {str(flavor.name) : totalinstances_per_flavor, } )
             output.update({"Total Capacity" : totalcapacity, } ) 
           hookenv.action_set({'get-capacity-info': yaml.dump(output)})

main()
