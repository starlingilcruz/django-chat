# AWS Elastic Beanstalk Deployment Guide

This guide covers deploying the Open Chat application to AWS Elastic Beanstalk with automated CI/CD via GitHub Actions.

## Architecture

```
GitHub → CI/CD Pipeline → AWS Elastic Beanstalk
                            ├─ Application Load Balancer (WebSocket support)
                            ├─ EC2 Instances (Daphne ASGI server)
                            ├─ RDS PostgreSQL
                            └─ ElastiCache Redis
```

## Prerequisites

- AWS Account
- AWS CLI installed locally
- EB CLI installed: `pip install awsebcli`
- GitHub repository with admin access

---

## Step 1: Create AWS Resources

### 1.1 Create RDS PostgreSQL Database

```bash
aws rds create-db-instance \
  --db-instance-identifier open-chat-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.1 \
  --master-username openchat \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-XXXXX \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --port 5432 \
  --publicly-accessible
```

**Or via AWS Console:**
1. Go to RDS → Create database
2. Choose PostgreSQL 16
3. Template: Free tier (or Production)
4. DB instance identifier: `open-chat-db`
5. Master username: `openchat`
6. Set a secure password
7. Instance: `db.t3.micro`
8. Storage: 20 GB
9. Enable automated backups
10. Create database

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

**Or via AWS Console:**
1. Go to ElastiCache → Redis → Create
2. Cluster name: `open-chat-redis`
3. Engine: Redis 7.0
4. Node type: `cache.t3.micro`
5. Number of replicas: 0 (for dev) or 1-2 (for prod)
6. Create

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

## Step 3: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | From IAM user |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | From IAM user |
| `AWS_REGION` | `us-east-1` | Your AWS region |
| `EB_APPLICATION_NAME` | `open-chat` | From EB init |
| `EB_ENVIRONMENT_NAME` | `open-chat-prod` | From EB create |

### 3.1 Create IAM User for GitHub Actions

```bash
# Create IAM user
aws iam create-user --user-name github-actions-deployer

# Attach policies
aws iam attach-user-policy \
  --user-name github-actions-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess-AWSElasticBeanstalk

# Create access key
aws iam create-access-key --user-name github-actions-deployer
```

Save the `AccessKeyId` and `SecretAccessKey` - you'll need these for GitHub Secrets.

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

### Manual Deployment (First Time)

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

### Automated Deployment (CI/CD)

Once GitHub secrets are configured, simply push to `master`:

```bash
git add .
git commit -m "Deploy to production"
git push origin master
```

**What happens:**
1. ✅ GitHub Actions runs tests
2. ✅ If tests pass, creates deployment package
3. ✅ Deploys to Elastic Beanstalk
4. ✅ Runs migrations
5. ✅ Collects static files
6. ✅ Starts Daphne server

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

## Costs Estimation

### Development Environment:
- **EC2 (t3.small):** ~$15/month
- **RDS (db.t3.micro):** ~$15/month
- **ElastiCache (cache.t3.micro):** ~$12/month
- **ALB:** ~$20/month
- **Total:** ~$62/month

### Production Environment:
- **EC2 (t3.medium x 2):** ~$60/month
- **RDS (db.t3.small):** ~$30/month
- **ElastiCache (cache.t3.small):** ~$25/month
- **ALB:** ~$20/month
- **Total:** ~$135/month

---

## Troubleshooting

### Deployment Fails

```bash
# Check logs
eb logs

# Check events
eb events

# Common issues:
# 1. Wrong environment variables
# 2. Database connection failed
# 3. Redis connection failed
```

### WebSocket Connection Issues

1. Verify ALB is configured for WebSockets (see `.ebextensions/04_alb.config`)
2. Check sticky sessions are enabled
3. Verify allowed origins in production settings

### Database Connection Errors

```bash
# Test database connection
eb ssh
source /var/app/venv/*/bin/activate
cd /var/app/current
python manage.py dbshell
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

## Security Checklist

- ✅ Use strong `DJANGO_SECRET_KEY`
- ✅ Set `DEBUG=False` in production
- ✅ Configure `ALLOWED_HOSTS` properly
- ✅ Use HTTPS (SSL certificate)
- ✅ Enable RDS encryption
- ✅ Use security groups to restrict access
- ✅ Enable CloudWatch logging
- ✅ Regular backups enabled
- ✅ Use IAM roles with least privilege

---

## Support

For issues or questions:
- Check EB logs: `eb logs`
- Check CloudWatch logs in AWS Console
- Review GitHub Actions workflow logs
