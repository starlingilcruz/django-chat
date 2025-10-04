# 🚀 Deployment Setup - Quick Reference

## ✅ What Has Been Configured

Your project now includes complete CI/CD deployment to AWS Elastic Beanstalk!

### Files Added:
- ✅ `.github/workflows/ci.yml` - CI/CD pipeline with deploy job
- ✅ `.ebextensions/*` - Elastic Beanstalk configuration (5 files)
- ✅ `Procfile` - Daphne ASGI server configuration
- ✅ `.ebignore` - Files to exclude from deployment
- ✅ `DEPLOYMENT.md` - Complete deployment documentation
- ✅ `scripts/setup-aws.sh` - Automated AWS setup script

---

## 🎯 Quick Start (3 Steps)

### Step 1: Set Up AWS (15 minutes)

**Option A: Automated Script**
```bash
./scripts/setup-aws.sh
```

**Option B: Manual Setup**
```bash
# Install tools
pip install awsebcli

# Initialize
eb init -p python-3.11 open-chat --region us-east-1

# Create environment (this will fail without RDS/Redis - see DEPLOYMENT.md)
eb create open-chat-prod --instance-type t3.small
```

### Step 2: Configure GitHub Secrets (5 minutes)

Go to: **GitHub Repository → Settings → Secrets and variables → Actions**

Add these secrets:
| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | Your IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user secret key |
| `AWS_REGION` | `us-east-1` (or your region) |
| `EB_APPLICATION_NAME` | `open-chat` |
| `EB_ENVIRONMENT_NAME` | `open-chat-prod` |

### Step 3: Deploy! (Automatic)

```bash
git add .
git commit -m "Configure deployment"
git push origin master
```

**That's it!** GitHub Actions will:
1. Run all tests
2. Deploy to AWS Elastic Beanstalk
3. Run migrations
4. Collect static files

---

## 📊 Deployment Flow

```
Developer pushes to master branch
         ↓
GitHub Actions CI starts
         ↓
Run tests (pytest, ruff, black, isort)
         ↓
    Tests pass? ─── NO ──→ ❌ Stop (fix errors)
         │
        YES
         ↓
Package application (zip)
         ↓
Deploy to AWS Elastic Beanstalk
         ↓
EB creates new application version
         ↓
Run database migrations
         ↓
Collect static files
         ↓
Start Daphne ASGI server
         ↓
Health check passes? ─── NO ──→ ❌ Rollback
         │
        YES
         ↓
✅ Deployment successful!
```

---

## 🔍 Monitoring & Management

### Check Deployment Status
```bash
eb status
```

### View Logs
```bash
# Real-time logs
eb logs --stream

# All logs
eb logs --all
```

### SSH into Server
```bash
eb ssh
```

### Check Application Health
```bash
eb health
```

### Scale Application
```bash
# Scale to 2 instances
eb scale 2
```

---

## 💰 Cost Breakdown

### Development (~$62/month)
- EC2 t3.small: $15
- RDS db.t3.micro: $15
- ElastiCache cache.t3.micro: $12
- Application Load Balancer: $20

### Production (~$135/month)
- EC2 t3.medium x2: $60
- RDS db.t3.small: $30
- ElastiCache cache.t3.small: $25
- Application Load Balancer: $20

---

## 🆘 Troubleshooting

### Deployment Fails
1. Check GitHub Actions logs
2. Check EB logs: `eb logs`
3. Verify all GitHub secrets are set
4. Ensure RDS and Redis are running

### WebSocket Issues
- Verify ALB is configured (`.ebextensions/04_alb.config`)
- Check sticky sessions are enabled
- Verify allowed origins in production settings

### Database Connection Errors
- Check RDS security group allows connections
- Verify environment variables are correct
- Test connection: `eb ssh` then test DB connection

---

## 📚 Documentation

- **Full Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **AWS EB Docs:** https://docs.aws.amazon.com/elasticbeanstalk/
- **GitHub Actions:** Check `.github/workflows/ci.yml`

---

## 🔐 Security Checklist

Before going live:
- [ ] Set strong `DJANGO_SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up SSL certificate (AWS Certificate Manager)
- [ ] Enable RDS encryption
- [ ] Configure security groups properly
- [ ] Enable CloudWatch logging
- [ ] Set up automated backups

---

## 🎉 Success!

Your Open Chat application is now configured for automated deployment!

**Next push to master will deploy automatically!**
