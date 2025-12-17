# Universal Restrictor Helm Chart

Deploy Universal Restrictor on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner (for audit logs)

## Installation

### Quick Start
```bash
# Add secrets
kubectl create secret generic restrictor-secrets \
  --from-literal=API_KEYS="sk-prod-key1:tenant1:pro" \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-xxx"

# Install
helm install restrictor ./helm/universal-restrictor \
  --set secrets.apiKeys="sk-prod-key1:tenant1:pro" \
  --set secrets.anthropicApiKey="sk-ant-xxx"
```

### With External Redis
```bash
helm install restrictor ./helm/universal-restrictor \
  --set redis.enabled=true \
  --set redis.external=true \
  --set redis.externalUrl="redis://redis.example.com:6379/0"
```

### With Ingress
```bash
helm install restrictor ./helm/universal-restrictor \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=restrictor.example.com \
  --set ingress.hosts[0].paths[0].path=/
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `2` |
| `image.repository` | Image repository | `universal-restrictor` |
| `image.tag` | Image tag | `latest` |
| `config.rateLimit` | Requests per minute | `60` |
| `config.logFormat` | Log format (text/json) | `json` |
| `config.enableDocs` | Enable Swagger UI | `false` |
| `config.corsOrigins` | CORS origins | `""` |
| `secrets.apiKeys` | API keys | `""` |
| `secrets.anthropicApiKey` | Claude API key | `""` |
| `redis.enabled` | Enable Redis | `true` |
| `redis.external` | Use external Redis | `false` |
| `redis.externalUrl` | External Redis URL | `""` |
| `ingress.enabled` | Enable ingress | `false` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Min replicas | `2` |
| `autoscaling.maxReplicas` | Max replicas | `10` |
| `audit.enabled` | Enable audit log PVC | `true` |
| `audit.size` | Audit log storage size | `5Gi` |

## Uninstall
```bash
helm uninstall restrictor
```

## Upgrade
```bash
helm upgrade restrictor ./helm/universal-restrictor --values myvalues.yaml
```
