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
import hooks.nova_cc_utils as ncc_utils


def set_authenticate_parameters():
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
