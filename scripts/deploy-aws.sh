#!/bin/bash
# AWS ECS Production Deployment Orchestrator Script for React Frontend

set -e # Exit immediately if a command exits with a non-zero status

# --- Variables (Modify or set in environment) ---
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-"123456789012"}
ECR_REPO_NAME="procurement-frontend"
ECS_CLUSTER_NAME="procurement-cluster"
ECS_SERVICE_NAME="procurement-frontend-service"
IMAGE_TAG=${1:-"latest"}

echo "========================================================="
echo "Starting Production Deployment to AWS ECS Fargate"
echo "========================================================="

# 1. Navigate to frontend root
cd "$(dirname "$0")/../frontend"

# 2. Build local Docker image
echo "Building frontend Docker image: $ECR_REPO_NAME:$IMAGE_TAG"
docker build -t "$ECR_REPO_NAME:$IMAGE_TAG" -f Dockerfile .

# 3. Authenticate Docker to AWS ECR
echo "Authenticating Docker to AWS Elastic Container Registry..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# 4. Tag and Push image to ECR
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG"
echo "Tagging image for ECR: $ECR_URI"
docker tag "$ECR_REPO_NAME:$IMAGE_TAG" "$ECR_URI"

echo "Pushing image to AWS ECR..."
docker push "$ECR_URI"

# 5. Update ECS Service (Force New Deployment)
echo "Triggering rolling update on ECS Service: $ECS_SERVICE_NAME..."
aws ecs update-service \
    --cluster "$ECS_CLUSTER_NAME" \
    --service "$ECS_SERVICE_NAME" \
    --force-new-deployment \
    --region "$AWS_REGION"

echo "========================================================="
echo "Deployment successfully triggered in AWS ECS Fargate!"
echo "========================================================="
