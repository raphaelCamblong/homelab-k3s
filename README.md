## Grafana.com dashboard ids:

| Dashboard                          | ID    |
|:-----------------------------------|:------|
| k8s-addons-prometheus.json         | 19105 |
| k8s-system-api-server.json         | 15761 |
| k8s-system-coredns.json            | 15762 |
| k8s-views-global.json              | 15757 |
| k8s-views-namespaces.json          | 15758 |
| k8s-views-nodes.json               | 15759 |
| k8s-views-pods.json                | 15760 |


## GOOD TO KNOW
- hostnamectl set-hostname "worker-0" *Optional*
- ssh-copy-id raphael@ip
- ssh access and sudo no passwd access:
(sudo visudo)
append to the end"{{USER}} ALL=(ALL) NOPASSWD:ALL"
