#!/bin/bash

shopt -s expand_aliases
interface="$1"
kube_vip_endpoint="$2"

if [ -z "$interface" ] || [ -z "$kube_vip_endpoint" ]; then
  echo "Error: Missing arguments. Please provide interface and kube-vip endpoint."
  echo "Usage: $0 <interface> <kube_vip_endpoint>"
  exit 1
fi

# Get RBAC for kube-vip
sudo curl https://kube-vip.io/manifests/rbac.yaml | sudo tee /var/lib/rancher/k3s/server/manifests/kube-vip-rbac.yaml

# Get RBAC for kube-vip
sudo k3s kubectl apply -f /var/lib/rancher/k3s/server/manifests/kube-vip-rbac.yaml

# Get kube-vip version
KVVERSION=$(curl -sL https://api.github.com/repos/kube-vip/kube-vip/releases | jq -r ".[0].name")

# Define kube-vip alias with arguments
alias kube-vip=" sudo ctr image pull ghcr.io/kube-vip/kube-vip:$KVVERSION; sudo ctr run --rm --net-host ghcr.io/kube-vip/kube-vip:$KVVERSION vip /kube-vip"

# Generate kube-vip manifest with arguments
kube-vip manifest daemonset --interface "$interface" --address "$kube_vip_endpoint" --inCluster --taint --controlplane --services --arp --leaderElection | sudo tee /var/lib/rancher/k3s/server/manifests/kube-vip.yaml

kubectl apply -f /var/lib/rancher/k3s/server/manifests/kube-vip.yaml

echo "Successfully generated kube-vip manifest for interface: $interface and endpoint: $kube_vip_endpoint"