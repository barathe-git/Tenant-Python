# Setup Guide - Tenant Management System

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- MySQL 5.7+ or MySQL 8.0+
- pip (Python package manager)

### 2. Database Setup

1. **Create MySQL Database:**
   ```sql
   CREATE DATABASE tenant_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Run SQL Script (Optional):**
   ```bash
   mysql -u root -p tenant_management < create_tables.sql
   ```
   
   Note: Tables will be created automatically on first backend run if you skip this step.

### 3. Environment Configuration

1. **Create `.env` file** (copy from `.env.template`):
   ```bash
   # On Windows (PowerShell)
   Copy-Item .env.template .env
   
   # On Linux/Mac
   cp .env.template .env
   ```

2. **Edit `.env` file** with your database credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password_here
   DB_NAME=tenant_management
   ```

### 4. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 5. Create Upload Directory

```bash
mkdir uploads
```

### 6. Run the Application

#### Option A: Run Backend and Frontend Separately

**Terminal 1 - Backend:**
```bash
# Run from project root
python -m backend.main
```
Or use the provided script:
```bash
# Windows
run_backend.bat

# Linux/Mac
chmod +x run_backend.sh
./run_backend.sh
```
Backend will run on: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

**Terminal 2 - Frontend:**
```bash
# Make sure virtual environment is activated first!
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Then run Streamlit
streamlit run frontend/app.py
```

Or use the provided script (automatically activates venv):
```bash
# Windows
run_frontend.bat

# Linux/Mac
chmod +x run_frontend.sh
./run_frontend.sh
```

Frontend will open in browser at: `http://localhost:8501`

#### Option B: Using Uvicorn Directly (from project root)

**Backend:**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
streamlit run frontend/app.py
```

### 7. Access the Application

- **Frontend UI:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## Troubleshooting

### Database Connection Issues

1. **Check MySQL is running:**
   ```bash
   # Windows
   net start MySQL80
   
   # Linux/Mac
   sudo systemctl status mysql
   ```

2. **Verify credentials in `.env` file**

3. **Test connection:**
   ```bash
   mysql -u root -p -e "USE tenant_management; SHOW TABLES;"
   ```

### Port Already in Use

If port 8000 or 8501 is already in use:

1. **Change ports in `.env`:**
   ```env
   API_PORT=8001
   FRONTEND_PORT=8502
   ```

2. **Or stop the process using the port:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -ti:8000 | xargs kill
   ```

### Import Errors

If you see import errors:

1. **Ensure virtual environment is activated**
2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### PDF Upload Issues

1. **Check `uploads/` directory exists and has write permissions**
2. **Verify file size is under 10MB**
3. **Ensure file is a valid PDF**

## Development Mode

### Backend Auto-reload

The backend uses `--reload` flag for auto-reload on code changes.

### Frontend Auto-reload

Streamlit automatically reloads on file changes.

## Production Deployment

### Backend

1. Remove `--reload` flag
2. Use a production ASGI server like Gunicorn with Uvicorn workers
3. Set up proper CORS origins
4. Use environment variables for sensitive data
5. Set up SSL/HTTPS

### Frontend

1. Deploy to Streamlit Cloud, Heroku, or similar
2. Configure API_BASE_URL in Streamlit secrets
3. Set up proper authentication

## Next Steps

1. Add your first owner
2. Add buildings for the owner
3. Add tenants with agreement PDFs
4. View dashboard for statistics and expiring agreements

## Support

For issues or questions, please check:
- README.md for detailed documentation
- API documentation at `/docs` endpoint
- GitHub issues (if applicable)

