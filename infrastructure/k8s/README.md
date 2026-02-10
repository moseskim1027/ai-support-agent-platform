# Kubernetes Manifests

Production-ready Kubernetes configuration for AI Support Agent Platform deployed on AWS EKS.

## Structure

```
k8s/
├── base/                          # Base Kubernetes resources
│   ├── deployment.yaml           # Application deployment
│   ├── service.yaml              # ClusterIP service
│   ├── ingress.yaml              # ALB ingress controller
│   ├── configmap.yaml            # Configuration
│   └── hpa.yaml                  # Horizontal Pod Autoscaler
└── overlays/                      # Environment-specific configurations
    ├── staging/                   # Staging environment
    │   ├── kustomization.yaml
    │   ├── namespace.yaml
    │   └── secrets.yaml
    └── production/                # Production environment
        ├── kustomization.yaml
        ├── namespace.yaml
        └── secrets.yaml
```

## Prerequisites

1. **AWS EKS Cluster** running Kubernetes 1.28+
2. **AWS Load Balancer Controller** installed
3. **kubectl** configured with EKS cluster access
4. **kustomize** (or kubectl 1.14+)

## Deployment

### Staging

```bash
# Apply staging configuration
kubectl apply -k overlays/staging/

# Verify deployment
kubectl get all -n staging

# Check pod logs
kubectl logs -f deployment/backend -n staging

# Port forward for testing
kubectl port-forward svc/backend 8000:80 -n staging
```

### Production

```bash
# Apply production configuration
kubectl apply -k overlays/production/

# Verify deployment
kubectl get all -n production

# Check rollout status
kubectl rollout status deployment/backend -n production

# View pod logs
kubectl logs -f deployment/backend -n production --tail=100
```

## Secrets Management

**IMPORTANT**: Do not commit actual secrets to version control!

### Option 1: External Secrets Operator (Recommended)

Install External Secrets Operator and configure AWS Secrets Manager:

```bash
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

### Option 2: Manual Secret Creation

```bash
# Create secret manually
kubectl create secret generic backend-secrets \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=secret-key='...' \
  --from-literal=postgres-url='postgresql://...' \
  --from-literal=redis-url='redis://...' \
  -n production
```

## Monitoring

### View Deployment Status

```bash
kubectl get deployment backend -n production
kubectl get pods -l app=backend -n production
kubectl get hpa backend-hpa -n production
```

### Check Logs

```bash
# Tail logs from all pods
kubectl logs -f -l app=backend -n production

# View specific pod
kubectl logs -f <pod-name> -n production
```

### Access Application

```bash
# Get ingress URL
kubectl get ingress backend-ingress -n production

# Test health endpoint
curl https://api.yourdomain.com/api/health
```

## Scaling

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment backend --replicas=5 -n production

# View scaling events
kubectl get hpa backend-hpa -n production -w
```

### Auto-scaling Configuration

The HPA is configured to:
- Min replicas: 3 (production), 2 (staging)
- Max replicas: 10 (production), 5 (staging)
- Target CPU: 70%
- Target Memory: 80%

## Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n production

# Rollback to previous version
kubectl rollout undo deployment/backend -n production

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n production
```

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n production
kubectl logs <pod-name> -n production
```

### Service Not Accessible

```bash
kubectl get svc backend -n production
kubectl get ingress backend-ingress -n production
kubectl describe ingress backend-ingress -n production
```

### HPA Not Scaling

```bash
kubectl describe hpa backend-hpa -n production
kubectl top pods -n production
```

## Resource Requests and Limits

### Production
- Requests: 1Gi memory, 250m CPU
- Limits: 2Gi memory, 1000m CPU

### Staging
- Requests: 512Mi memory, 250m CPU
- Limits: 1Gi memory, 1000m CPU

## CI/CD Integration

Deployments are automated through GitHub Actions:
- **Staging**: Triggered on push to `staging` branch
- **Production**: Triggered on push to `main` branch

See `.github/workflows/cd-staging.yml` and `.github/workflows/cd-production.yml` for details.
