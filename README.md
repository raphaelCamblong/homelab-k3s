# Homelab K3s Configuration

This repository contains configuration files and serverless functions for my personal homelab running on K3s. It serves as a central location for managing deployments, monitoring configurations, and automation scripts.

## Overview

This homelab setup uses K3s, a lightweight Kubernetes distribution, 

- Kubernetes deployments
- Monitoring dashboards (Grafana)
- Serverless functions
- Infrastructure as Code (IaC) configurations

## Monitoring Dashboards

The following Grafana dashboards are configured for monitoring:

| Dashboard                          | ID    |
|:-----------------------------------|:------|
| k8s-addons-prometheus.json         | 19105 |
| k8s-system-api-server.json         | 15761 |
| k8s-system-coredns.json            | 15762 |
| k8s-views-global.json              | 15757 |
| k8s-views-namespaces.json          | 15758 |
| k8s-views-nodes.json               | 15759 |
| k8s-views-pods.json                | 15760 |
