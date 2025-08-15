# NursePrep Pro - Vercel Deployment Guide

## Pre-Deployment Checklist

### 1. Database Setup (Required First)
Since Vercel doesn't support local MongoDB, you need a cloud database:

**Option A: MongoDB Atlas (Recommended - Free tier available)**
1. Go to https://cloud.mongodb.com
2. Create account and new cluster
3. Get connection string (format: `mongodb+srv://username:password@cluster.mongodb.net/database_name`)
4. Whitelist Vercel's IP ranges (or use 0.0.0.0/0 for all IPs)

**Option B: Alternative providers**
- DigitalOcean Managed MongoDB
- AWS DocumentDB
- CosmosDB (Azure)

### 2. Stripe Live Keys Setup
1. In your Stripe Dashboard, go to Developers > API Keys
2. Copy your Live Secret Key (starts with `sk_live_`)
3. Set up webhooks endpoint: `https://yourdomain.com/api/webhooks/stripe`
4. Copy webhook signing secret

### 3. Domain Configuration
1. Add your Namecheap domain to Vercel project
2. Configure DNS to point to Vercel

## Deployment Steps

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login to Vercel
```bash
vercel login
```

### Step 3: Deploy from Project Root
```bash
vercel
```

### Step 4: Configure Environment Variables
In Vercel Dashboard > Project Settings > Environment Variables, add:

**Production Variables:**
- `MONGO_URL`: Your MongoDB connection string
- `DB_NAME`: Your database name (e.g., "nurseprep_prod")
- `STRIPE_API_KEY`: Your live Stripe secret key (sk_live_...)
- `CORS_ORIGINS`: Your domain (e.g., "https://nurseprep.com")
- `REACT_APP_BACKEND_URL`: Your domain (e.g., "https://nurseprep.com")

### Step 5: Update Frontend Build Command
The build script in package.json is already configured for Vercel.

### Step 6: Configure Custom Domain
1. In Vercel Dashboard > Project Settings > Domains
2. Add your Namecheap domain
3. Update DNS records as instructed

### Step 7: Set up Stripe Webhooks
1. Go to Stripe Dashboard > Webhooks
2. Create endpoint: `https://yourdomain.com/api/webhooks/stripe`
3. Select events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`
4. Copy webhook signing secret and add as `STRIPE_WEBHOOK_SECRET` environment variable

### Step 8: Test Deployment
1. Visit your live domain
2. Test user registration
3. Test payment flow with small amount
4. Test all app features

## Post-Deployment Checklist

### 1. Switch Stripe to Live Mode
- Update Stripe keys from test to live
- Test with real payment (small amount)

### 2. Monitor Application
- Check Vercel Function logs
- Monitor Stripe webhook delivery
- Test mobile PWA installation

### 3. DNS and SSL
- Ensure HTTPS is working
- Test domain propagation globally

### 4. Performance Optimization
- Enable Vercel Analytics (optional)
- Monitor Core Web Vitals
- Test app performance on mobile

## Troubleshooting

### Common Issues:
1. **Database Connection**: Ensure MongoDB cluster allows connections from anywhere (0.0.0.0/0)
2. **API Routes**: All backend routes must start with `/api/`
3. **CORS Issues**: Set CORS_ORIGINS to your exact domain
4. **Build Failures**: Check build logs in Vercel dashboard

### Support Resources:
- Vercel Documentation: https://vercel.com/docs
- MongoDB Atlas Guide: https://docs.atlas.mongodb.com
- Stripe Webhooks: https://stripe.com/docs/webhooks

## Estimated Timeline:
- Database setup: 15-30 minutes
- Vercel deployment: 10-15 minutes  
- Domain configuration: 5-10 minutes
- Stripe webhook setup: 10 minutes
- Testing: 15-30 minutes

**Total: 55-95 minutes**