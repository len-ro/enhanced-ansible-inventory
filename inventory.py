#!/usr/bin/env python

import yaml, json, sys, os

"""
    Generates a dynamic json inventory from static inventory.yml. It adds dynamic groups based on dfilter_abc variables in hosts.
    If a host has a dfilter_abc with value xyz then it will be added to subgroup xyz of group abc.
    See: https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html
"""

initial_inventory = {}
inventory = {}
hostvars = {}
dynamic_groups = {}

def get_existing_or_dynamic_group(group_name):
    #print('Get %s' % group_name, file=sys.stderr )
    if group_name in initial_inventory:
        group = initial_inventory[group_name]
        dynamic_groups[group_name] = group;
        return dynamic_groups[group_name]
    elif group_name in dynamic_groups:
        return dynamic_groups[group_name]
    else:
        dynamic_groups[group_name] = {}
        return dynamic_groups[group_name]

def parse_group(grp_name, data_yml):
    inventory[grp_name] = {'hosts': []}
    for key in data_yml:
        if key == 'children':
            inventory[grp_name]['children'] = []
            for child_grp_name in data_yml['children']:
                inventory[grp_name]['children'].append(parse_group(child_grp_name, data_yml['children'][child_grp_name]))
        elif key == 'hosts':
            if isinstance(data_yml['hosts'], dict):
                for host_name in data_yml['hosts']:
                    if host_name in inventory['all']['hosts']:
                        print('Duplicated HOST %s' % host_name)
                        sys.exit(-1)
                    inventory['all']['hosts'].append(host_name)
                    inventory[grp_name]['hosts'].append(host_name)
                    host_yml = data_yml['hosts'][host_name]
                    hostvars[host_name] = host_yml
                    for var_name in host_yml:
                        if var_name.startswith('dfilter_'):
                            dgroup_name = var_name[8:]
                            dsubgrups = host_yml[var_name]
                            if not isinstance(dsubgrups, list):
                                dsubgrups = [dsubgrups]
                            for dsubgrup in dsubgrups:
                                dsubgroup_name ="%s_%s" %(dgroup_name, dsubgrup)
                                if dsubgroup_name is not None:
                                    target_dgroup = get_existing_or_dynamic_group(dgroup_name)
                                    if 'children' not in target_dgroup:
                                        target_dgroup['children'] = []
                                    if dsubgroup_name not in target_dgroup['children']:
                                        target_dgroup['children'].append(dsubgroup_name) 

                                    target_dsubgroup = get_existing_or_dynamic_group(dsubgroup_name)
                                    if 'hosts' not in target_dsubgroup:
                                        target_dsubgroup['hosts'] = []
                                    if host_name not in target_dsubgroup['hosts']:
                                        target_dsubgroup['hosts'].append(host_name)

                                    # if not dgroup_name in dynamic_groups:
                                    #     dynamic_groups[dgroup_name] = {'children': [dsubgroup_name]}
                                    # else:
                                    #     if dsubgroup_name not in dynamic_groups[dgroup_name]['children']:
                                    #         dynamic_groups[dgroup_name]['children'].append(dsubgroup_name)
                                    # if not dsubgroup_name in dynamic_groups:
                                    #     dynamic_groups[dsubgroup_name] = {'hosts': [host_name]}
                                    # else:
                                    #     dynamic_groups[dsubgroup_name]['hosts'].append(host_name)
        else:
            inventory[grp_name][key] = data_yml[key]
    return grp_name
        
#suport for !vault, see: https://gist.github.com/sivel/6991a5abcfc41bb2872d5898213575eb
class VaultData:
    def __init__(self, value):
        self.value = value

def vault_constructor(loader, node):
    value = loader.construct_scalar(node)
    return VaultData(value)

class VaultEncoder(json.JSONEncoder):
    '''
    Simple encoder class to deal with JSON encoding of Ansible internal types
    '''
    def default(self, o):
        if isinstance(o, VaultData):
            return {'__ansible_vault': o.value}
        return json.JSONEncoder.default(self, o)

def keepass_contructor(loader, node):
    value = loader.construct_scalar(node)
    _value = value.split('/')
    path = '/'.join(_value[:-1])
    key = _value[-1]
    if keepass == None:
        init_keepass_vault()
    entry = keepass.find_entries(path=path)
    
    if isinstance(entry, list):
        if len(entry) == 0:
            entry = None
        else:
            entry = entry[0]
    if entry == None:
        result = None
    if key == 'username':
        result = entry.username
    elif key == 'title':
        result = entry.title
    elif key == 'notes':
        result = entry.notes
    elif key == 'url':
        result = entry.url
    else:
        result = entry.password
    return VaultData(vault.encrypt(result))

yaml.add_constructor(u'!vault', vault_constructor)
yaml.add_constructor(u'!keepass', keepass_contructor)
#end support for !vault

inventory_yml = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'inventory.yml')
keepass_pass = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keepass.vault.pass')
keepass_vault = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keepass.vault.kdbx')
ansible_vault_pass = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vault.pass')

keepass = None
vault = None

def init_keepass_vault():
    from pykeepass import PyKeePass

    #for keepass re-encryption as vault
    from ansible.constants import DEFAULT_VAULT_ID_MATCH
    from ansible.parsing.vault import VaultLib
    from ansible.parsing.vault import VaultSecret
    from ansible.parsing.vault import FileVaultSecret
    from ansible.parsing.dataloader import DataLoader

    global keepass
    global vault

    with open(keepass_pass, 'r') as keepass_pass_file:
        vault_pass = keepass_pass_file.read().replace('\n', '')
        keepass = PyKeePass(keepass_vault, password=vault_pass)
    
    #init ansible encryption mechanism
    #see https://github.com/ansible/ansible/blob/fd8b8742730b692a9e715a6a7a922607dcef8821/lib/ansible/parsing/vault/__init__.py
    secret = FileVaultSecret('vault.pass', loader = DataLoader())
    secret.load()
    vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, secret)])


with open(inventory_yml, 'rb') as src:
    initial_inventory = yaml.load(src, Loader=yaml.Loader)
    #print(data)
    parse_group('all', initial_inventory['all'])

inventory.update(dynamic_groups)
inventory['_meta'] = {'hostvars': hostvars}
result = json.dumps(inventory, cls=VaultEncoder, sort_keys=False, indent=4)
print(result)
    