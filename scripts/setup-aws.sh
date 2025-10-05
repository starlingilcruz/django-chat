#!/bin/bash

# Django Chat - AWS Setup Script
# This script helps set up the AWS infrastructure for deployment

set -e

echo "🚀 Django Chat - AWS Setup"
echo "======================================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   pip install awscli"
    exit 1
fi

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI is not installed. Please install it first:"
    echo "   pip install awsebcli"
    exit 1
fi

# Get user input
read -p "Enter AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter RDS Master Password: " -s RDS_PASSWORD
echo ""

read -p "Enter Application Name (default: django-chat): " APP_NAME
APP_NAME=${APP_NAME:-django-chat}

read -p "Enter Environment Name (default: django-chat-prod): " ENV_NAME
ENV_NAME=${ENV_NAME:-django-chat-prod}

echo ""
echo "📋 Configuration:"
echo "  Region: $AWS_REGION"
echo "  App: $APP_NAME"
echo "  Environment: $ENV_NAME"
echo ""
read -p "Continue? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "1️⃣  Creating RDS PostgreSQL Database..."
echo ""

RDS_ID="${APP_NAME}-db"
aws rds create-db-instance \
  --db-instance-identifier $RDS_ID \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.10 \
  --master-username openchat \
  --master-user-password "$RDS_PASSWORD" \
  --allocated-storage 20 \
  --backup-retention-period 7 \
  --port 5432 \
  --region $AWS_REGION \
  --no-publicly-accessible || echo "RDS instance may already exist"

echo "✅ RDS creation initiated (this may take 5-10 minutes)"
echo ""

echo "2️⃣  Creating ElastiCache Redis..."
echo ""

REDIS_ID="${APP_NAME}-redis"
aws elasticache create-cache-cluster \
  --cache-cluster-id $REDIS_ID \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --port 6379 \
  --region $AWS_REGION || echo "Redis cluster may already exist"

echo "✅ Redis creation initiated (this may take 5-10 minutes)"
echo ""

echo "3️⃣  Initializing Elastic Beanstalk..."
echo ""

eb init -p python-3.11 $APP_NAME --region $AWS_REGION

echo "✅ EB initialized"
echo ""

echo "⏳ Waiting for RDS to be available..."
aws rds wait db-instance-available \
  --db-instance-identifier $RDS_ID \
  --region $AWS_REGION

RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier $RDS_ID \
  --region $AWS_REGION \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "✅ RDS is ready: $RDS_ENDPOINT"
echo ""

echo "⏳ Waiting for Redis to be available..."
aws elasticache wait cache-cluster-available \
  --cache-cluster-id $REDIS_ID \
  --region $AWS_REGION || true

REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id $REDIS_ID \
  --region $AWS_REGION \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

echo "✅ Redis is ready: $REDIS_ENDPOINT"
echo ""

echo "4️⃣  Creating Elastic Beanstalk Environment..."
echo ""

DJANGO_SECRET=$(openssl rand -base64 32)

eb create $ENV_NAME \
  --instance-type t3.small \
  --region $AWS_REGION

echo ""
echo "5️⃣  Setting environment variables..."
echo ""

eb use $ENV_NAME
eb setenv \
  DJANGO_SECRET_KEY="$DJANGO_SECRET" \
  DEBUG=False \
  ALLOWED_HOSTS=".elasticbeanstalk.com" \
  POSTGRES_HOST=$RDS_ENDPOINT \
  POSTGRES_DB=openchat \
  POSTGRES_USER=openchat \
  POSTGRES_PASSWORD=$RDS_PASSWORD \
  POSTGRES_PORT=5432 \
  REDIS_URL=redis://$REDIS_ENDPOINT:6379/0 \
  DJANGO_SETTINGS_MODULE=openchat.settings.prod

echo ""
echo "🎉 Setup Complete!"
echo "======================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Add these secrets to GitHub (Settings → Secrets):"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION: $AWS_REGION"
echo "   - EB_APPLICATION_NAME: $APP_NAME"
echo "   - EB_ENVIRONMENT_NAME: $ENV_NAME"
echo ""
echo "2. Create IAM user for GitHub Actions:"
echo "   aws iam create-user --user-name github-actions-deployer"
echo "   aws iam attach-user-policy --user-name github-actions-deployer --policy-arn arn:aws:iam::aws:policy/AdministratorAccess-AWSElasticBeanstalk"
echo "   aws iam create-access-key --user-name github-actions-deployer"
echo ""
echo "3. Deploy:"
echo "   git push origin master"
echo ""
echo "4. Check deployment:"
echo "   eb status"
echo "   eb logs"
echo ""
echo "5. Open app:"
echo "   eb open"
echo ""
