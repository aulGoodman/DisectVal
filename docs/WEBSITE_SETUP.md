# DisectVal Website Setup Guide

This guide explains how to set up a website for DisectVal to distribute downloads and sync user accounts.

## Recommended Hosting Options

### Option 1: Vercel + Supabase (Recommended for Beginners)
**Cost:** Free tier available  
**Tech:** Next.js, React, Supabase (PostgreSQL)

1. **Create a Vercel Account**: https://vercel.com
2. **Create a Supabase Account**: https://supabase.com
3. **Clone/Fork the website template** (we'll create one)
4. **Deploy to Vercel** with one click

### Option 2: GitHub Pages + Firebase
**Cost:** Free  
**Tech:** Static HTML/React, Firebase Auth

### Option 3: Custom VPS (Full Control)
**Cost:** $5-20/month  
**Tech:** Any stack you prefer

---

## Website Features to Implement

### 1. User Authentication
```
- Login/Register with email
- OAuth (Discord, Google)
- Sync with desktop app via API tokens
```

### 2. Download Versions Manager
```
- Upload different .exe versions
- Mark versions as: Stable, Beta, Dev
- Control who can download which versions
- Track download counts
```

### 3. User Dashboard
```
- View gameplay statistics (synced from app)
- Manage subscription tier
- Access download history
```

---

## Database Schema (Supabase/PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'user', -- user, tester, admin, developer
    access_tier TEXT DEFAULT 'free', -- free, ad_free, pro
    is_tester BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Download versions
CREATE TABLE versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_url TEXT NOT NULL,
    release_type TEXT DEFAULT 'stable', -- stable, beta, dev
    required_tier TEXT DEFAULT 'free',
    changelog TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User downloads
CREATE TABLE downloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    version_id UUID REFERENCES versions(id),
    downloaded_at TIMESTAMP DEFAULT NOW()
);

-- Feature access
CREATE TABLE feature_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    feature_id TEXT NOT NULL,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints for Desktop App Sync

### Authentication
```
POST /api/auth/login
POST /api/auth/register
POST /api/auth/token (get API token for desktop app)
```

### User Sync
```
GET  /api/user/profile
POST /api/user/sync-stats
```

### Downloads
```
GET  /api/downloads/versions
GET  /api/downloads/:versionId/url
```

---

## Quick Start with Vercel + Supabase

### Step 1: Set up Supabase
1. Go to https://supabase.com and create account
2. Create new project
3. Run the SQL schema above in SQL Editor
4. Get your API URL and anon key

### Step 2: Create Next.js Project
```bash
npx create-next-app@latest disectval-web
cd disectval-web
npm install @supabase/supabase-js
```

### Step 3: Deploy to Vercel
1. Push to GitHub
2. Connect to Vercel
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

## Desktop App Integration

The desktop app already has sync capabilities. Configure the API URL in settings:

```python
# In config/settings.py - TrainingSettings has sync_url field
sync_url: str = "https://your-website.vercel.app"
```

---

## File Storage for Downloads

### Option A: Vercel Blob Storage
```javascript
// Easy to use, integrated with Vercel
import { put } from '@vercel/blob';

const blob = await put('DisectVal-v1.0.0.exe', file, {
  access: 'public',
});
```

### Option B: Supabase Storage
```javascript
// Built into Supabase
const { data, error } = await supabase.storage
  .from('downloads')
  .upload('DisectVal-v1.0.0.exe', file);
```

### Option C: GitHub Releases (Recommended)
- Host .exe files as GitHub Release assets
- Free and reliable
- Use GitHub API to list versions
- Already integrated with this repository

---

## Security Considerations

1. **API Tokens**: Use short-lived tokens with refresh mechanism
2. **Rate Limiting**: Implement on all API endpoints
3. **Download Verification**: Sign .exe files and verify checksums
4. **Role Checks**: Always verify user role server-side

---

## Domain Setup

1. Buy a domain (Namecheap, Cloudflare, etc.)
2. Point DNS to Vercel/your hosting
3. Enable HTTPS (automatic with Vercel)

---

## Building Executables for Website Distribution

Use the GitHub Actions workflow to build executables:

1. Go to **Actions** tab in GitHub
2. Run **"Build Windows Executables"** workflow
3. Download artifacts or let it commit to repo
4. Upload to your website storage or use GitHub Releases

The workflow builds:
- `Setup.exe` - Initial setup wizard
- `Dev.exe` - Developer version
- `UserVersion.exe` - Standard user version

---

## Next Steps

1. Choose your hosting option
2. Set up the database
3. Build the website frontend
4. Implement the API endpoints
5. Add the sync code to desktop app
6. Test user flow end-to-end

For questions or help, contact the developer.
