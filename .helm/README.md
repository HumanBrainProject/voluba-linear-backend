# Deployment

This directory describes how voluba linear backend is deployed on ebrains infrastructure. 

## Provisioned service

The services provided by ebrains, used in the deployment:

- docker registry 
- rancher cluster

## Requirements

- helm

## Scripts

At root directory (i.e. parent of )

```bash
helm install voluba-backend .helm/voluba-linear-backend
```
