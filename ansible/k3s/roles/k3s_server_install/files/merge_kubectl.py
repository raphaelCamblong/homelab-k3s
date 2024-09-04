#!/usr/bin/env python3
import yaml
import subprocess
import os

imported_config = '../exported_k3s_config'
kube_config_path = "/Users/raphael/.kube/config"

def modify_kube_config(ip, namespace):
    # Load the kubeconfig file
    with open(imported_config, 'r') as f:
        config = yaml.safe_load(f)

    # Modify the server URL
    config['clusters'][0]['cluster']['server'] = f"https://{ip}:6443"

    # Modify the context name
    config['clusters'][0]['cluster']['name'] = namespace
    config['clusters'][0]['name'] = namespace

    config['contexts'][0]['context']['cluster'] = namespace
    config['contexts'][0]['context']['user'] = namespace
    config['contexts'][0]['name'] = namespace
    config['current-context'] = namespace

    config['users'][0]['name'] = namespace

    # Write the modified config back to the file
    with open(kube_config_path, 'w') as f:
        yaml.dump(config, f)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Error: Missing arguments.")
        print("Usage: python script.py <ip> <namespace>")
        sys.exit(1)

    ip = sys.argv[1]
    namespace = sys.argv[2]

    modify_kube_config(ip, namespace)