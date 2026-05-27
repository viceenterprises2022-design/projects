# Deployment Instructions

## Docker Setup
```bash
docker-compose -f deploy/docker-compose.prod.yml up -d --build
```

## Cloud Deployments
Deploy directly onto AWS ECS or GCP Cloud Run by pointing the build system to `app/Dockerfile`.
Ensure your environment secrets (`OPENAI_API_KEY`, `ADRIAN_API_KEY`) are stored in your secret manager of choice.
