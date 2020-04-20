# Enhanced ansible inventory
Enhanced ansible inventory script which adds support for dynamic groups and keepass like vault. This is a python script which reads a yml inventory and produces a json inventory.

It wraps around your inventory.yml and enhances it.

```
ansible-playbook -i inventory.yml ...
```

becomes

```
ansible-playbook -i inventory.py ...
```

## Dynamic groups

- dfilter_* are expanded into new groups and groups of gropus. This allows to have a list of host to which to add:
```
- dfilter_app: web
- dfilter_env: prod
```
this will automatically create the groups: *app_web* and *env_prod* which will contain the given hosts. This will simplify a lot how to handle the groups of machines.

## Support for keepass

It adds support to handle both ansible vault and keepass entries. Since handling vault passwords directly in inventory is a bit complicated requiring to manually encrypt and decrypt the passwords I wanted to keep using the existing keepass file with all the passwords which editable in a simpler way.

For example:

```
oracle_dia_password: !keepass db/app_test/password
db_schema: !keepass db/app_test/username
```

## Example

```
all:
  children:
    vmware_1:
      hosts:
        web_test_host:
          ansible_host: 172.20.0.10
          dfilter_env: test
          dfilter_app: apache

        app_test_host:
          ansible_host: 172.20.0.11
          dfilter_env: test
          dfilter_app: 
            - appx
            - appy

        db_host:
          ansible_host: 172.20.0.12
          dfilter_env: 
            - test
            - prod
          dfilter_app: db
          db_user: !keepass db/username
          db_pass: !keepass db/password

    vmware_2:
      hosts:
        web_prod_host:
          ansible_host: 172.20.0.20
          dfilter_env: prod
          dfilter_app: apache

        app_prod_host:
          ansible_host: 172.20.0.21
          dfilter_env: prod
          dfilter_app: appx
  vars:
    - secret: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          39353234643736383839613763663836303932353861303939346638373331393866353232623666
          6362636462393461306363373565623864393332396461320a383464363762316165303738303830
          64373532656166623535666335363762336233646333326563306637613562343861386334383536
          3664663531316532660a653861646266373530343136383038633836323163353831623363656466
          63326462356539333035316637323162376234303662373165396438653535386435
```

becomes:

```
{
    "app_apache": {
        "hosts": [
            "web_test_host", 
            "web_prod_host"
        ]
    }, 
    "all": {
        "hosts": [
            "app_test_host", 
            "web_test_host", 
            "db_host", 
            "app_prod_host", 
            "web_prod_host"
        ], 
        "children": [
            "vmware_1", 
            "vmware_2"
        ], 
        "vars": [
            {
                "secret": {
                    "__ansible_vault": "$ANSIBLE_VAULT;1.1;AES256\n39353234643736383839613763663836303932353861303939346638373331393866353232623666\n6362636462393461306363373565623864393332396461320a383464363762316165303738303830\n64373532656166623535666335363762336233646333326563306637613562343861386334383536\n3664663531316532660a653861646266373530343136383038633836323163353831623363656466\n63326462356539333035316637323162376234303662373165396438653535386435\n"
                }
            }
        ]
    }, 
    "_meta": {
        "hostvars": {
            "app_test_host": {
                "dfilter_env": "test", 
                "ansible_host": "172.20.0.11", 
                "dfilter_app": [
                    "appx", 
                    "appy"
                ]
            }, 
            "app_prod_host": {
                "dfilter_env": "prod", 
                "ansible_host": "172.20.0.21", 
                "dfilter_app": "appx"
            }, 
            "web_test_host": {
                "dfilter_env": "test", 
                "ansible_host": "172.20.0.10", 
                "dfilter_app": "apache"
            }, 
            "db_host": {
                "dfilter_env": [
                    "test", 
                    "prod"
                ], 
                "db_user": {
                    "__ansible_vault": "$ANSIBLE_VAULT;1.1;AES256\n61393533626135386135336439626361653835613935616634616131643963393532633966376333\n6266313639333935356636666234386263313539393464640a323164653439363235346435343232\n66356264623737613634623936373639396162623961656361653632363263356663633163663738\n3364666339303638620a353739323132633032363639646430626432663138383433353265663632\n3461\n"
                }, 
                "ansible_host": "172.20.0.12", 
                "dfilter_app": "db", 
                "db_pass": {
                    "__ansible_vault": "$ANSIBLE_VAULT;1.1;AES256\n37326431363432376365306561356630323863626166346361616533656333363564366234346265\n6632633464616563656164336639636333333130633564380a646363343431333933653966616266\n66346534393330376134316239623861373463636631643539346665383262653030373937323832\n6261663532343761640a636334663265633237663930346665383534643134616638393330373565\n63323863646565383335376466616337306165333836666265343539353363353935\n"
                }
            }, 
            "web_prod_host": {
                "dfilter_env": "prod", 
                "ansible_host": "172.20.0.20", 
                "dfilter_app": "apache"
            }
        }
    }, 
    "app_db": {
        "hosts": [
            "db_host"
        ]
    }, 
    "app": {
        "children": [
            "app_appx", 
            "app_appy", 
            "app_apache", 
            "app_db"
        ]
    }, 
    "app_appy": {
        "hosts": [
            "app_test_host"
        ]
    }, 
    "app_appx": {
        "hosts": [
            "app_test_host", 
            "app_prod_host"
        ]
    }, 
    "env_test": {
        "hosts": [
            "app_test_host", 
            "web_test_host", 
            "db_host"
        ]
    }, 
    "env": {
        "children": [
            "env_test", 
            "env_prod"
        ]
    }, 
    "env_prod": {
        "hosts": [
            "db_host", 
            "app_prod_host", 
            "web_prod_host"
        ]
    }, 
    "vmware_1": {
        "hosts": [
            "app_test_host", 
            "web_test_host", 
            "db_host"
        ]
    }, 
    "vmware_2": {
        "hosts": [
            "app_prod_host", 
            "web_prod_host"
        ]
    }
}
```

Using the inventory:

```
ansible-playbook -i ./inventory.py  test.yml --vault-id=default@vault.pass

PLAY [localhost] ***************************************************************

TASK [debug] *******************************************************************
ok: [localhost] => {}

MSG:

[u'myusername', u'changeThisDBPass', u'changeThisSecretAlso']

PLAY RECAP *********************************************************************
localhost                  : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

## Dependencies

- ansible python libraries
- pykeepass

## Files structure

The following file structure is hardcoded at this moment which I think is still flexible enough for most cases. All files are relative to inventory.py
- inventory.py
- inventory.yml - yaml inventory to be enhanced
- vault.pass - ansible vault pass file
- keepass.vault.kdbx - keepass pass file
- keepass.vault.pass - keepass pass file, similar format to ansible vault file

> VERY IMPORTANT: never store real .pass files in a git. Add this to .gitignore

```
#don't store this in git
vault.pass
keepass.vault.pass
```
-