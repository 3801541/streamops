# StreamOps 🎬

> Mini-projet DevOps simulant le cycle de vie d'une plateforme de streaming.  
> Stack : **FastAPI · Docker · GitHub Actions · Terraform · Helm · ArgoCD · EKS · Prometheus · Grafana**

---

## Architecture

```
Dev push
   │
   ▼
GitHub Actions ──► lint + tests ──► Docker build ──► push ECR
                                                         │
                                          bump image tag in values.yaml
                                                         │
                                                         ▼
                                                    ArgoCD détecte le diff
                                                         │
                                          helm template + kubectl apply
                                                         │
                                                         ▼
                                              EKS (Kubernetes)
                                         ┌────────────────────────┐
                                         │  Deployment (pods)      │
                                         │  Service + Ingress      │
                                         │  HPA (autoscaling)      │
                                         └────────────────────────┘
                                                         │
                                                    /metrics
                                                         │
                                                         ▼
                                           Prometheus ──► Grafana
                                                  └──► Alertmanager ──► Slack
```

---

## Structure du projet

```
streamops/
├── app/                              # Application FastAPI
│   ├── main.py                       # API + métriques Prometheus
│   ├── test_main.py                  # Tests pytest
│   ├── Dockerfile
│   └── requirements.txt
├── terraform/                        # Infrastructure as Code (AWS)
│   ├── main.tf                       # EKS, VPC, ECR, RDS
│   ├── variables.tf
│   └── outputs.tf
├── charts/streamops/                 # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml                   # Valeurs par défaut
│   ├── values-staging.yaml           # Surcharge staging
│   ├── values-prod.yaml              # Surcharge prod
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── hpa.yaml
│       └── serviceaccount.yaml
├── argocd/
│   ├── application.yaml              # App StreamOps (GitOps)
│   └── monitoring-app.yaml           # Stack monitoring (GitOps)
├── monitoring/
│   ├── values.yaml                   # Config Prometheus + Grafana + Alertmanager
│   └── grafana-dashboard-configmap.yaml
└── .github/workflows/
    └── ci-cd.yaml                    # Pipeline GitHub Actions
```

---

## Pipeline CI/CD

Le pipeline GitHub Actions comporte 3 jobs :

| Job | Déclencheur | Actions |
|-----|-------------|---------|
| `test` | Tout push / PR | ruff lint · pytest · helm lint |
| `build-push` | Push sur `main` ou `staging` | Docker build → ECR push |
| `deploy` | Après `build-push` | Bump du tag dans `values-{env}.yaml` → commit → ArgoCD auto-sync |

Le flow GitOps est entièrement automatisé : un `git push` sur `main` déclenche un déploiement en prod sans aucune intervention manuelle.

---

## Déploiement local (sans AWS)

### Prérequis
```bash
# Kubernetes léger en local
brew install k3d helm argocd
```

### 1. Créer le cluster local
```bash
k3d cluster create streamops --port "8080:80@loadbalancer"
```

### 2. Installer ArgoCD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl port-forward svc/argocd-server -n argocd 8443:443
# Mot de passe initial :
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 3. Appliquer les Applications ArgoCD
```bash
kubectl apply -f argocd/application.yaml
kubectl apply -f argocd/monitoring-app.yaml
```

ArgoCD synchronise automatiquement le repo et déploie tout.

### 4. Accéder aux services
```bash
# API
kubectl port-forward svc/streamops -n streamops 8000:80
curl http://localhost:8000/health
curl http://localhost:8000/streams

# Grafana
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# → http://localhost:3000  (admin / changeme)
```

---

## Terraform (infra AWS)

```bash
cd terraform
terraform init
terraform plan -var="environment=staging" -var="db_password=secret"
terraform apply
```

Les ressources créées : VPC · subnets privés/publics · NAT Gateway · EKS cluster · ECR · RDS PostgreSQL.

---

## API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/streams` | Liste tous les flux |
| GET | `/streams/{id}` | Détail d'un flux |
| GET | `/metrics` | Métriques Prometheus |

---

## Monitoring

- **Prometheus** scrape automatiquement tous les pods annotés `prometheus.io/scrape: "true"`
- **Grafana** expose un dashboard custom *StreamOps Overview* : RPS, latence P95, error rate, CPU/mémoire par pod
- **Alertmanager** envoie les alertes sur Slack (warning + critical sur des canaux séparés)

Alertes configurées :
- `HighRequestLatency` — P95 > 500ms pendant 2 min
- `PodCrashLooping` — redémarrages détectés sur 15 min
- `HighCPUUsage` — CPU > 80% pendant 5 min

---

## Secrets GitHub Actions requis

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | Clé d'accès IAM (droits ECR + EKS) |
| `AWS_SECRET_ACCESS_KEY` | Secret IAM correspondant |

---

## Technologies

| Catégorie | Outil |
|-----------|-------|
| CI/CD | GitHub Actions |
| GitOps | ArgoCD |
| IaC | Terraform |
| Container | Docker |
| Registry | Amazon ECR |
| Orchestration | Kubernetes (EKS) |
| Packaging K8s | Helm |
| Monitoring | Prometheus + Grafana |
| Alerting | Alertmanager + Slack |
| Cloud | AWS (eu-west-3) |
