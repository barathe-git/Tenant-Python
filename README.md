# Tenant Management System

A comprehensive tenant management system built with Streamlit frontend, FastAPI backend, and MySQL database.

## 🚀 Features

- **Owner Management**: Complete CRUD operations for property owners
- **Building Management**: Manage multiple buildings per owner
- **Tenant Management**: Track tenants with agreement details and PDF storage
- **PDF Viewer**: View agreement PDFs directly in the Streamlit interface
- **Dashboard**: Real-time metrics and analytics
- **Notification System**: Automated alerts for expiring agreements (30 days)
- **Beautiful UI**: Modern, responsive design with custom CSS

## 📁 Project Structure

```
tenant-mgmt/
│── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── owners.py
│   │   ├── buildings.py
│   │   ├── tenants.py
│   │   └── files.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── owner.py
│   │   ├── building.py
│   │   └── tenant.py
│   └── main.py
│── frontend/
│   ├── components/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── owner_form.py
│   │   ├── building_form.py
│   │   ├── tenant_form.py
│   │   └── pdf_viewer.py
│   └── app.py
│── utils/
│   ├── __init__.py
│   └── scheduler.py
│── static/
│   └── style.css
│── uploads/
│   ├── .gitkeep
│── requirements.txt
│── .env.template
│── README.md
│── create_tables.sql
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MySQL 5.7+ or MySQL 8.0+
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd tenant-mgmt
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Database

1. Create a MySQL database:

```sql
CREATE DATABASE tenant_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Copy `.env.template` to `.env`:

```bash
cp .env.template .env
```

3. Edit `.env` and update database credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=tenant_management
```

4. Run the SQL script to create tables:

```bash
mysql -u root -p tenant_management < create_tables.sql
```

Or use the application's auto-create feature (tables will be created automatically on first run).

### Step 5: Create Upload Directory

```bash
mkdir uploads
```

## 🚀 Running the Application

### Backend (FastAPI)

Open a terminal and run from the project root:

```bash
python -m backend.main
```

Or using uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided script:
```bash
# Windows
run_backend.bat

# Linux/Mac
chmod +x run_backend.sh
./run_backend.sh
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Frontend (Streamlit)

Open another terminal and run:

```bash
streamlit run frontend/app.py
```

The application will open in your browser at: `http://localhost:8501`

### Scheduler (Background Jobs)

The scheduler runs automatically when the backend starts. It checks for expiring agreements daily at 9:00 AM.

## 📖 Usage Guide

### 1. Owner Management

- Navigate to **Owners** in the sidebar
- Click **Add New Owner** to create a new owner
- Fill in owner details (name, phone, email, address)
- View, edit, or delete existing owners

### 2. Building Management

- Navigate to **Buildings** in the sidebar
- Select an owner from the dropdown
- Click **Add New Building**
- Enter building details (name, type, portions, location)
- Manage buildings for each owner

### 3. Tenant Management

- Navigate to **Tenants** in the sidebar
- Click **Add New Tenant**
- Select owner and building
- Fill in tenant details and upload agreement PDF
- View tenant list with search and filter options
- Click on PDF icon to view agreement

### 4. Dashboard

- View real-time statistics:
  - Total owners
  - Total buildings
  - Total tenants
  - Expiring agreements (next 30 days)
  - Building occupancy rates

## 🔧 Configuration

### Environment Variables

Edit `.env` file to configure:

- Database connection
- File upload directory
- Email settings (for notifications)
- API and frontend ports

### Customization

- **CSS Styling**: Edit `static/style.css` to customize the UI
- **Scheduler Timing**: Modify `utils/scheduler.py` to change alert frequency
- **PDF Settings**: Adjust upload limits in `backend/api/files.py`

## 🧪 Testing

Run backend tests:

```bash
pytest backend/tests/
```

## 📝 API Endpoints

### Owners
- `GET /api/owners` - List all owners
- `POST /api/owners` - Create owner
- `GET /api/owners/{id}` - Get owner by ID
- `PUT /api/owners/{id}` - Update owner
- `DELETE /api/owners/{id}` - Delete owner

### Buildings
- `GET /api/buildings` - List all buildings
- `POST /api/buildings` - Create building
- `GET /api/buildings/{id}` - Get building by ID
- `PUT /api/buildings/{id}` - Update building
- `DELETE /api/buildings/{id}` - Delete building
- `GET /api/buildings/owner/{owner_id}` - Get buildings by owner

### Tenants
- `GET /api/tenants` - List all tenants
- `POST /api/tenants` - Create tenant
- `GET /api/tenants/{id}` - Get tenant by ID
- `PUT /api/tenants/{id}` - Update tenant
- `DELETE /api/tenants/{id}` - Delete tenant
- `GET /api/tenants/building/{building_id}` - Get tenants by building
- `GET /api/tenants/expiring` - Get expiring agreements

### Files
- `POST /api/files/upload` - Upload PDF
- `GET /api/files/{file_path}` - Get PDF file

## 🐛 Troubleshooting

### Database Connection Issues

- Verify MySQL is running
- Check database credentials in `.env`
- Ensure database exists

### PDF Upload Issues

- Check `uploads/` directory exists and has write permissions
- Verify file size limits in configuration

### Port Already in Use

- Change ports in `.env` file
- Or stop the process using the port

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Support

For support, please open an issue in the repository.

