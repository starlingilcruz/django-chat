# AWS Elastic Beanstalk Deployment Guide

This guide covers deploying the Open Chat application to AWS Elastic Beanstalk with automated CI/CD.

## Architecture

```
CI/CD Pipeline → AWS Elastic Beanstalk
                            ├─ Application Load Balancer (WebSocket support)
                            ├─ EC2 Instances (Daphne ASGI server)
                            ├─ RDS PostgreSQL
                            └─ ElastiCache Redis
```

## Prerequisites

- AWS Account
- AWS CLI installed locally
- EB CLI installed: `pip install awsebcli`
- Pipeline with admin access

---

## Step 1: Create AWS Resources

### 1.1 Create RDS PostgreSQL Database

```bash
aws rds create-db-instance \
  --db-instance-identifier open-chat-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.10 \
  --master-username openchat \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-XXXXX \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --port 5432 \
  --publicly-accessible
```

### 1.2 Create ElastiCache Redis

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id open-chat-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --port 6379
```

---

## Step 2: Initialize Elastic Beanstalk

### 2.1 Install EB CLI

```bash
pip install awsebcli
```

### 2.2 Initialize EB Application

```bash
cd /path/to/open-chat

# Initialize EB
eb init -p python-3.11 open-chat --region us-east-1

# Create environment
eb create open-chat-prod \
  --instance-type t3.small \
  --envvars \
    DJANGO_SECRET_KEY="$(openssl rand -base64 32)",\
    DEBUG=False,\
    ALLOWED_HOSTS=".elasticbeanstalk.com",\
    POSTGRES_HOST=YOUR_RDS_ENDPOINT,\
    POSTGRES_DB=openchat,\
    POSTGRES_USER=openchat,\
    POSTGRES_PASSWORD=YOUR_DB_PASSWORD,\
    REDIS_URL=redis://YOUR_REDIS_ENDPOINT:6379/0
```

### 2.3 Configure Load Balancer for WebSockets

The `.ebextensions/04_alb.config` already configures this, but verify:

```bash
# Check if ALB is configured
eb config

# Look for:
# - LoadBalancerType: application
# - Sticky sessions enabled
```

---

## Step 3: Configure Secrets

### Required Secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | From IAM user |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | From IAM user |
| `AWS_REGION` | `us-east-1` | Your AWS region |
| `EB_APPLICATION_NAME` | `open-chat` | From EB init |
| `EB_ENVIRONMENT_NAME` | `open-chat-prod` | From EB create |

### 3.1 Create IAM User for the deployment

```bash
# Create IAM user
aws iam create-user --user-name cd-deployer

# Attach policies
aws iam attach-user-policy \
  --user-name cd-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess-AWSElasticBeanstalk

# Create access key
aws iam create-access-key --user-name cd-deployer
```
---

## Step 4: Set Environment Variables in EB

```bash
# Set all environment variables
eb setenv \
  DJANGO_SECRET_KEY="$(openssl rand -base64 32)" \
  DEBUG=False \
  ALLOWED_HOSTS=".elasticbeanstalk.com,.yourdomain.com" \
  POSTGRES_HOST=YOUR_RDS_ENDPOINT \
  POSTGRES_DB=openchat \
  POSTGRES_USER=openchat \
  POSTGRES_PASSWORD=YOUR_DB_PASSWORD \
  POSTGRES_PORT=5432 \
  REDIS_URL=redis://YOUR_REDIS_ENDPOINT:6379/0 \
  DJANGO_SETTINGS_MODULE=openchat.settings.prod
```

---

## Step 5: Deploy

```bash
# Deploy to EB
eb deploy

# Check status
eb status

# View logs
eb logs

# Open in browser
eb open
```

---

## Step 6: Configure Custom Domain (Optional)

### 6.1 Get SSL Certificate

```bash
# Request certificate in AWS Certificate Manager
aws acm request-certificate \
  --domain-name chat.yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

### 6.2 Update `.ebextensions/04_alb.config`

Replace `CERTIFICATE_ID` with your ACM certificate ARN.

### 6.3 Add DNS Record

Point your domain to the EB environment URL:
```
CNAME: chat.yourdomain.com → open-chat-prod.us-east-1.elasticbeanstalk.com
```

---

## Monitoring & Maintenance

### View Logs

```bash
# Real-time logs
eb logs --stream

# Download all logs
eb logs --all
```

### SSH into Instance

```bash
eb ssh
```

### Check Application Health

```bash
# Health status
eb health

# Environment info
eb status
```

### Scale Application

```bash
# Scale to 2-4 instances
eb scale 2
```

---

## Rolling Back

```bash
# List versions
eb appversion

# Deploy previous version
eb deploy --version v1
```

---

## Cleanup

To delete all resources:

```bash
# Terminate EB environment
eb terminate open-chat-prod

# Delete RDS
aws rds delete-db-instance --db-instance-identifier open-chat-db --skip-final-snapshot

# Delete ElastiCache
aws elasticache delete-cache-cluster --cache-cluster-id open-chat-redis
```

---

## Support

For issues or questions:
- Check EB logs: `eb logs`
- Check CloudWatch logs in AWS Console
- Review pipeline workflow logs
