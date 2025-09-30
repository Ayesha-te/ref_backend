# Nexocart Deployment Guide

This guide covers deploying the Nexocart platform with optimizations for Neon database connections.

## 🔧 Database Connection Fixes Applied

### 1. Idle Transaction Timeouts
- ✅ **ATOMIC_REQUESTS = True** - Django wraps every request in a proper transaction
- ✅ **SSL Mode Required** - Prevents unexpected disconnects on Neon free tier
- ✅ **Connection Max Age** - Set to 600 seconds for connection pooling

### 2. Gunicorn Configuration
- ✅ **Sync Workers** - Prevents async connection leaks
- ✅ **Low Worker Count** - 2-4 workers to stay within Neon's ~50 connection limit
- ✅ **Max Requests Limit** - Workers restart after 200 requests to prevent memory leaks

### 3. Neon Sleep Mode Handling
- ✅ **DB Retry Middleware** - Automatically retries failed connections after DB wake-up
- ✅ **Proper Error Handling** - Logs connection issues for debugging

## 🚀 Deployment Options

### Option 1: Render.com (Recommended)

1. **Connect your repository** to Render
2. **Use the provided render.yaml** - It's already configured with optimal settings
3. **Set environment variables**:
   ```
   DATABASE_URL=your-neon-connection-string
   DJANGO_SECRET_KEY=your-secret-key
   ```

### Option 2: Manual Deployment

1. **Install dependencies**:
   ```bash
   cd ref_backend
   pip install -r requirements.txt
   ```

2. **Set environment variables** (copy from .env.example):
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
   export DJANGO_SECRET_KEY="your-secret-key"
   export DJANGO_DEBUG="0"
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. **Start with Gunicorn**:
   ```bash
   gunicorn core.wsgi:application --config gunicorn.conf.py
   ```

## 🔍 Health Monitoring

### Check Database Health
```bash
python manage.py check_db_health --test-queries
```

### Monitor Logs
The middleware logs connection retries and failures:
```
INFO core.middleware Database connection failed (attempt 1), retrying in 1 second
```

## ⚙️ Configuration Files

- **gunicorn.conf.py** - Optimized Gunicorn settings for Neon
- **core/middleware.py** - DB retry middleware for sleep mode
- **core/settings.py** - Updated with ATOMIC_REQUESTS and SSL settings
- **render.yaml** - Complete Render deployment configuration

## 🐛 Troubleshooting

### Connection Errors
1. Check if DATABASE_URL includes `?sslmode=require`
2. Verify worker count is low (2-4 workers max)
3. Check logs for retry attempts

### Performance Issues
1. Run health check: `python manage.py check_db_health --test-queries`
2. Monitor connection count in Neon dashboard
3. Consider upgrading from Neon free tier if needed

### Sleep Mode Issues
- First request after 5+ minutes might be slow (normal)
- Middleware automatically retries failed connections
- Check logs for "Database connection failed" messages

## 📊 Monitoring

### Key Metrics to Watch
- Database connection count (should stay under 50 for Neon free)
- Response times (first request after sleep will be slower)
- Error rates (should be low with retry middleware)

### Neon Dashboard
- Monitor active connections
- Check for connection spikes
- Review query performance

## 🔒 Security Notes

- Always use SSL connections (`sslmode=require`)
- Keep DJANGO_DEBUG=0 in production
- Use strong SECRET_KEY
- Regularly rotate database credentials

## 📈 Scaling Considerations

When you outgrow Neon free tier:
1. Upgrade to Neon Pro for more connections
2. Consider connection pooling solutions like PgBouncer
3. Implement read replicas for heavy read workloads
4. Monitor and optimize slow queries