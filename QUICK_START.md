# Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Database
1. Create `.env` file (copy from `.env.template`)
2. Update database credentials:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=tenant_management
   ```

### Step 3: Create Database
```sql
CREATE DATABASE tenant_management;
```

### Step 4: Run Backend
```bash
# From project root directory
python -m backend.main
```
Or use the script:
```bash
# Windows
run_backend.bat

# Linux/Mac
./run_backend.sh
```
✅ Backend running at: http://localhost:8000

### Step 5: Run Frontend (New Terminal)

**Important:** Make sure your virtual environment is activated first!

```bash
# Activate virtual environment (if not already activated)
# Windows:
.venv\Scripts\activate
# or
venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
# or
source venv/bin/activate

# Then run Streamlit
streamlit run frontend/app.py
```

Or use the script (it will activate venv automatically):
```bash
# Windows
run_frontend.bat

# Linux/Mac
chmod +x run_frontend.sh
./run_frontend.sh
```

✅ Frontend running at: http://localhost:8501

## 📋 First Steps

1. **Add Owner** → Navigate to "Owners" → Fill form → Submit
2. **Add Building** → Navigate to "Buildings" → Select owner → Fill form → Submit
3. **Add Tenant** → Navigate to "Tenants" → Select owner & building → Upload PDF → Submit
4. **View Dashboard** → See statistics and expiring agreements

## 🎯 Key Features

- ✅ Complete CRUD for Owners, Buildings, Tenants
- ✅ PDF Agreement Management
- ✅ Dashboard with Statistics
- ✅ Expiring Agreement Alerts (30 days)
- ✅ Beautiful Modern UI
- ✅ Search & Filter Functionality

## 🔧 Troubleshooting

**Backend won't start?**
- Check MySQL is running
- Verify `.env` credentials
- Check port 8000 is available

**Frontend won't connect?**
- Ensure backend is running first
- Check API URL in sidebar settings
- Verify CORS settings

**PDF upload fails?**
- Check `uploads/` directory exists
- Verify file is PDF format
- Check file size < 10MB

## 📚 More Info

- See `README.md` for detailed documentation
- See `SETUP.md` for comprehensive setup guide
- API docs: http://localhost:8000/docs

