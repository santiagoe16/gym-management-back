# Gym Management Backend

A comprehensive backend API for gym management system built with FastAPI, SQLModel, and MySQL. Features include real-time WebSocket communication for fingerprint device integration, automated gym access control, and comprehensive user management.

## 🏗️ Project Structure

```
gym-management-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          # Authentication endpoints
│   │       │   ├── users.py         # User management endpoints
│   │       │   └── websocket.py     # WebSocket endpoints for fingerprint devices
│   │       └── api.py               # Main API router
│   ├── core/
│   │   ├── config.py                # Application settings
│   │   ├── database.py              # Database configuration
│   │   ├── deps.py                  # Dependency injection
│   │   ├── security.py              # Security utilities
│   │   ├── websocket_service.py     # WebSocket connection management
│   │   ├── encryption_service.py    # Fingerprint data encryption
│   │   └── init_db.py               # Database initialization
│   └── models/
│       ├── user.py                  # User models and roles
│       └── auth.py                  # Authentication models
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata
├── runtime.txt                      # Python version specification
├── railway.toml                     # Railway deployment config
└── env.example                      # Environment variables template
```

## 👥 User Roles & Permissions

### 🔐 Admin Role
- **Login Access**: ✅ Yes
- **Permissions**:
  - Full system access
  - Create, read, update, delete all users
  - Create, read, update, delete all plans
  - Create, read, update, delete all products
  - Manage inventory and stock levels
  - Sell products (reduces inventory)
  - View and modify all sales records
  - Manage trainers and regular users
  - System configuration
  - View all data and reports

### 🏋️ Trainer Role
- **Login Access**: ✅ Yes
- **Permissions**:
  - View all users (read-only)
  - Create regular users with plans
  - View trainer list
  - View regular users list
  - View all plans (read-only)
  - View all products (read-only)
  - Sell products (reduces inventory)
  - View their own sales records
  - Cannot create/delete plans or products
  - Cannot create trainers or admins
  - Cannot modify sales records

### 👤 User Role
- **Login Access**: ❌ No (Cannot login to system)
- **Purpose**: Regular gym members
- **Access**: None (managed by Admin/Trainer)
- **Plan Tracking**: Each user has assigned plans with expiration dates

### 📝 User Types and Password Requirements

- **Admin & Trainer Users**: Require passwords for login access
- **Regular Users (Members)**: No passwords needed - they don't log into the system

### 🆔 User Identification Features

- **Document ID**: Unique identifier for each user (ID card, passport, etc.)
- **Phone Number**: Contact information for all users
- **Search by Document ID**: Quick user lookup for gym staff
- **Search by Phone**: Find users by phone number (partial match)

### 🏢 Multi-Gym Support

- **Gym Management**: Create and manage multiple gym locations
- **Gym Isolation**: Each gym has its own users, plans, products, and sales
- **Role-Based Access**: Trainers can only access their assigned gym
- **Admin Oversight**: Admins can manage all gyms and view cross-gym data
- **Gym Filtering**: All endpoints support filtering by gym ID

### 📏 Body Measurements Tracking

- **Comprehensive Measurements**: Height, weight, and all key body part circumferences
- **Progress Tracking**: Automatic calculation of changes and percentages over time
- **Date Tracking**: All measurements include timestamps for progress analysis
- **Role-Based Access**: Admin and trainers can record and view measurements
- **Gym Isolation**: Trainers can only access measurements from their gym
- **Progress Reports**: Detailed progress summaries with start/current values and changes

## 🚀 Quick Start

### 📋 Example User Creation

#### Create Admin/Trainer (with password)
```json
POST /api/v1/users/admin-trainer
{
  "email": "trainer2@gym.com",
  "full_name": "John Trainer",
  "document_id": "TRAINER002",
  "phone_number": "+1234567892",
  "role": "trainer",
  "password": "securepassword123"
}
```

#### Create Regular User (no password)
```json
POST /api/v1/users/regular
{
  "email": "member1@gym.com",
  "full_name": "Jane Member",
  "document_id": "MEMBER001",
  "phone_number": "+1234567893",
  "role": "user"
}
```

#### Create Regular User with Plan
```json
POST /api/v1/users/with-plan
{
  "email": "member2@gym.com",
  "full_name": "Bob Member",
  "document_id": "MEMBER002",
  "phone_number": "+1234567894",
  "role": "user",
  "gym_id": 1,
  "plan_id": 1,
  "purchased_price": 29.99
}
```

#### Create New Gym
```json
POST /api/v1/gyms/
{
  "name": "Downtown Gym",
  "address": "456 Downtown Ave, City, State 12345",
  "is_active": true
}
```

#### Filter Users by Gym
```
GET /api/v1/users/?gym_id=1
```

#### Search Users by Document ID in Specific Gym
```
GET /api/v1/users/search/document/MEMBER001?gym_id=1
```

#### Create Body Measurement
```json
POST /api/v1/measurements/
{
  "user_id": 3,
  "height": 175.5,
  "weight": 75.2,
  "chest": 95.0,
  "shoulders": 120.0,
  "biceps_left": 32.5,
  "biceps_right": 32.8,
  "forearms_left": 28.0,
  "forearms_right": 28.2,
  "abdomen": 82.0,
  "hips": 95.0,
  "thighs_left": 58.0,
  "thighs_right": 58.5,
  "calves_left": 36.0,
  "calves_right": 36.2,
  "notes": "Good progress on upper body, focus on core strength",
  "measurement_date": "2024-01-15T10:30:00"
}
```

#### Get User Progress
```
GET /api/v1/measurements/user/3/progress?start_date=2024-01-01&end_date=2024-01-31
```

#### Get Latest Measurement
```
GET /api/v1/measurements/user/3/latest
```

#### Get All User Measurements
```
GET /api/v1/measurements/user/3
```

#### Search User by Document ID
```
GET /api/v1/users/search/document/MEMBER001
```

#### Search Users by Phone
```
GET /api/v1/users/search/phone/+123456
```

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp env.example .env
# Edit .env with your database and JWT settings
```

### 3. Database Setup
```bash
# Option 1: Automatic setup (requires root access)
python setup_database.py

# Option 2: Manual setup
mysql -u root -p
CREATE DATABASE gym_management;
CREATE USER 'gym_user'@'localhost' IDENTIFIED BY 'gym_password';
GRANT ALL PRIVILEGES ON gym_management.* TO 'gym_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Check database connection
python check_database.py

# Initialize database and create default users
python -m app.core.init_db
```

### 4. Run Development Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔑 Default Users

After running `init_db.py`, these users are created:

### Default Gym
- **Name**: Main Gym
- **Address**: 123 Main Street, City, State 12345

### Admin User
- **Email**: admin@gym.com
- **Password**: admin123
- **Document ID**: ADMIN001
- **Phone**: +1234567890
- **Role**: Admin
- **Gym**: Main Gym

### Trainer User
- **Email**: trainer@gym.com
- **Password**: trainer123
- **Document ID**: TRAINER001
- **Phone**: +1234567891
- **Role**: Trainer
- **Gym**: Main Gym

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login (Admin/Trainer only) - Returns access token and user role
- `GET /api/v1/auth/me` - Get current user info

### Gym Management
- `GET /api/v1/gyms/` - Get all gyms (All authenticated users)
- `GET /api/v1/gyms/active` - Get active gyms (All authenticated users)
- `POST /api/v1/gyms/` - Create gym (Admin only)
- `GET /api/v1/gyms/{gym_id}` - Get specific gym (All authenticated users)
- `PUT /api/v1/gyms/{gym_id}` - Update gym (Admin only)
- `DELETE /api/v1/gyms/{gym_id}` - Delete gym (Admin only)

### User Management
- `GET /api/v1/users/` - Get all users (Admin/Trainer) - Supports gym filtering
- `POST /api/v1/users/admin-trainer` - Create admin/trainer user with password (Admin only)
- `POST /api/v1/users/with-plan` - Create regular user with plan (Admin/Trainer)
- `GET /api/v1/users/search/document/{document_id}` - Search user by document ID (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/users/search/phone/{phone_number}` - Search users by phone number (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/users/{user_id}` - Get specific user (Admin/Trainer)
- `PUT /api/v1/users/{user_id}` - Update user (Admin/Trainer - with restrictions)
- `DELETE /api/v1/users/{user_id}` - Delete user (Admin only)
- `GET /api/v1/users/trainers/` - Get all trainers (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/users/users/` - Get all regular users (Admin/Trainer) - Supports gym filtering

### Plan Management
- `GET /api/v1/plans/` - Get all plans (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/plans/active` - Get active plans (Admin/Trainer) - Supports gym filtering
- `POST /api/v1/plans/` - Create plan (Admin only)
- `GET /api/v1/plans/{plan_id}` - Get specific plan (Admin/Trainer)
- `PUT /api/v1/plans/{plan_id}` - Update plan (Admin only)
- `DELETE /api/v1/plans/{plan_id}` - Delete plan (Admin only)

### User Plans Management
- `GET /api/v1/user-plans/` - Get all user plans (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/user-plans/user/{user_id}` - Get all plans for specific user (Admin/Trainer)
- `GET /api/v1/user-plans/user/{user_id}/active` - Get active plan for specific user (Admin/Trainer)
- `POST /api/v1/user-plans/` - Create user plan (Admin/Trainer)
- `PUT /api/v1/user-plans/{user_plan_id}` - Update user plan (Admin/Trainer - with restrictions)
- `DELETE /api/v1/user-plans/{user_plan_id}` - Delete user plan (Admin only)

### Product Management
- `GET /api/v1/products/` - Get all products (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/products/active` - Get active products (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/products/low-stock` - Get products with low stock (Admin/Trainer) - Supports gym filtering
- `POST /api/v1/products/` - Create product (Admin only)
- `GET /api/v1/products/{product_id}` - Get specific product (Admin/Trainer)
- `PUT /api/v1/products/{product_id}` - Update product (Admin only)
- `DELETE /api/v1/products/{product_id}` - Delete product (Admin only)
- `PUT /api/v1/products/{product_id}/stock` - Update stock quantity (Admin only)

### Sales Management
- `POST /api/v1/sales/` - Create sale (Admin/Trainer - both can sell products)
- `GET /api/v1/sales/` - Get all sales with filters (Admin sees all, Trainer sees own) - Supports gym filtering
- `GET /api/v1/sales/daily` - Get sales for specific date (Admin sees all, Trainer sees own) - Supports gym filtering
- `GET /api/v1/sales/summary` - Get sales summary (Admin sees all, Trainer sees own) - Supports gym filtering
- `GET /api/v1/sales/{sale_id}` - Get specific sale (Admin sees all, Trainer sees own)
- `PUT /api/v1/sales/{sale_id}` - Update sale (Admin only)
- `DELETE /api/v1/sales/{sale_id}` - Delete sale (Admin only)

### Body Measurements Management
- `GET /api/v1/measurements/` - Get all measurements with filters (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/measurements/user/{user_id}` - Get all measurements for specific user (Admin/Trainer)
- `GET /api/v1/measurements/user/{user_id}/latest` - Get latest measurement for user (Admin/Trainer)
- `GET /api/v1/measurements/user/{user_id}/progress` - Get progress summary for user (Admin/Trainer)
- `POST /api/v1/measurements/` - Create new measurement (Admin/Trainer)
- `GET /api/v1/measurements/{measurement_id}` - Get specific measurement (Admin/Trainer)
- `PUT /api/v1/measurements/{measurement_id}` - Update measurement (Admin/Trainer)
- `DELETE /api/v1/measurements/{measurement_id}` - Delete measurement (Admin/Trainer)

### Attendance Management
- `GET /api/v1/attendance/` - Get all attendance records with filters (Admin/Trainer) - Supports gym filtering
- `GET /api/v1/attendance/user/{user_id}` - Get attendance records for specific user (Admin/Trainer)
- `GET /api/v1/attendance/user/{user_id}/summary` - Get attendance summary for user (Admin/Trainer)
- `GET /api/v1/attendance/daily/{date}` - Get daily attendance records (Admin/Trainer)
- `POST /api/v1/attendance/` - Create attendance record (Admin/Trainer)
- `PUT /api/v1/attendance/{attendance_id}` - Update attendance record (Admin/Trainer)
- `DELETE /api/v1/attendance/{attendance_id}` - Delete attendance record (Admin only)

### WebSocket System
- `GET /ws/health` - WebSocket connection health check
- `WS /ws/user/{user_id}` - User WebSocket endpoint for fingerprint device communication
- `WS /ws/gym/{gym_id}` - Gym WebSocket endpoint for fingerprint device management

#### WebSocket Architecture
The system implements a real-time communication layer for fingerprint device integration:

**Connection Types:**
- **User Connections** (`/ws/user/{user_id}`): Individual user connections for fingerprint device communication
- **Gym Connections** (`/ws/gym/{gym_id}`): Gym-level connections for fingerprint device management and user enrollment

**Message Flow:**
1. **Device Authentication**: Fingerprint devices connect to gym endpoints and authenticate with admin/trainer credentials
2. **User Enrollment**: Devices can enroll new users by capturing and storing fingerprint templates
3. **Real-time Communication**: Bidirectional communication between devices, gym systems, and user applications
4. **Fingerprint Storage**: Secure storage of encrypted fingerprint data in the database

**Supported Message Types:**
- `login` - Device authentication with gym credentials
- `fingerprint_connected` - Establish connection between user and gym systems
- `user` - User identification and enrollment requests
- `store_fingerprint` - Store captured fingerprint templates
- `finger1_captured` - Fingerprint capture confirmation
- `download_templates` - Download user fingerprint templates for device
- `user_found` / `user_not_found` - User identification results
- `enrollment_completed` - User enrollment completion confirmation

**Security Features:**
- **Role-based Access**: Only admin/trainer users can authenticate devices
- **Encryption**: Fingerprint data is encrypted before storage
- **Connection Validation**: All connections are validated and monitored
- **Error Handling**: Comprehensive error handling with detailed error messages

**Use Cases:**
- **Gym Access Control**: Fingerprint-based entry systems
- **User Enrollment**: New member fingerprint registration
- **Attendance Tracking**: Automated check-in/check-out
- **Device Management**: Centralized fingerprint device administration

## 🚀 Railway Deployment

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login and Deploy
```bash
railway login
railway init
railway up
```

### 3. Set Environment Variables
```bash
railway variables set DATABASE_URL="your-mysql-url"
railway variables set SECRET_KEY="your-secret-key"
```

## 🔧 Configuration

### Environment Variables
- `DB_USER` - Database username (default: gym_user)
- `DB_PASSWORD` - Database password (default: gym_password)
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 3306)
- `DB_NAME` - Database name (default: gym_management)
- `SECRET_KEY` - JWT secret key
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: None - no expiration)
- `DEBUG` - Debug mode (default: True)

## 🛡️ Security Features

- **JWT Authentication** - Secure token-based auth with no expiration
- **Password Hashing** - bcrypt password encryption
- **Role-Based Access Control** - Granular permissions
- **CORS Support** - Cross-origin resource sharing
- **Input Validation** - Pydantic model validation
- **Persistent Sessions** - Users stay logged in until explicit logout

## 🔒 Trainer Restrictions

### User Management
Trainers can update regular user information with restrictions:
- **Regular Users Only**: Cannot update admin or trainer accounts
- **Same Gym**: Can only update users in their own gym
- **Limited Fields**: Cannot change user role or gym assignment
- **Data Validation**: Email and document ID uniqueness enforced

### User Plan Modifications
Trainers can only modify user plans under specific conditions:
- **Expired Plans**: When the current plan has expired
- **Plan Upgrades**: When upgrading to a plan with longer duration or higher price
- **Gym Isolation**: Trainers can only manage users in their own gym

### Regular User Creation
- Regular users must always be created with a plan
- No standalone user creation without plans
- Ensures all users have active memberships

## 📊 Database Schema

### Gyms Table
- `id` - Primary key
- `name` - Unique gym name
- `address` - Gym address
- `is_active` - Gym status
- `created_at` - Gym creation timestamp
- `updated_at` - Last update timestamp

### Users Table
- `id` - Primary key
- `email` - Unique email address
- `full_name` - User's full name
- `document_id` - Unique document ID number for user identification
- `phone_number` - User's phone number
- `gym_id` - Foreign key to gyms table
- `role` - User role (admin/trainer/user)
- `hashed_password` - Encrypted password (optional, only for admin/trainer users)
- `is_active` - Account status
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Plans Table
- `id` - Primary key
- `name` - Plan name (unique)
- `price` - Plan price (only admin can change)
- `duration_days` - Plan duration in days
- `gym_id` - Foreign key to gyms table
- `is_active` - Plan availability status
- `created_at` - Plan creation timestamp
- `updated_at` - Last update timestamp

### User Plans Table
- `id` - Primary key
- `user_id` - Foreign key to users table
- `plan_id` - Foreign key to plans table
- `purchased_price` - Actual price paid (cannot be changed once set)
- `purchased_at` - Purchase timestamp
- `expires_at` - Plan expiration date
- `created_by_id` - Admin/Trainer who created this plan assignment
- `is_active` - Plan assignment status
- `created_at` - Assignment creation timestamp
- `updated_at` - Last update timestamp

### Products Table
- `id` - Primary key
- `name` - Product name (unique)
- `price` - Product price
- `quantity` - Number of items in inventory
- `gym_id` - Foreign key to gyms table
- `is_active` - Product availability status
- `created_at` - Product creation timestamp
- `updated_at` - Last update timestamp

### Sales Table
- `id` - Primary key
- `product_id` - Foreign key to products table
- `quantity` - Number of items sold
- `unit_price` - Price per unit at time of sale
- `total_amount` - Total amount for this sale
- `sold_by_id` - Foreign key to users table (admin or trainer who made sale)
- `gym_id` - Foreign key to gyms table
- `sale_date` - Date and time of sale
- `created_at` - Sale creation timestamp
- `updated_at` - Last update timestamp

### Measurements Table
- `id` - Primary key
- `user_id` - Foreign key to users table (user being measured)
- `recorded_by_id` - Foreign key to users table (admin/trainer who recorded)
- `height` - Height in cm
- `weight` - Weight in kg
- `chest` - Chest circumference in cm
- `shoulders` - Shoulder width in cm
- `biceps_left`, `biceps_right` - Biceps circumference in cm
- `forearms_left`, `forearms_right` - Forearm circumference in cm
- `abdomen` - Abdomen/waist circumference in cm
- `hips` - Hip circumference in cm
- `thighs_left`, `thighs_right` - Thigh circumference in cm
- `calves_left`, `calves_right` - Calf circumference in cm
- `notes` - Additional notes about measurements
- `measurement_date` - Date when measurements were taken
- `created_at` - Measurement creation timestamp
- `updated_at` - Last update timestamp

### Attendance Table
- `id` - Primary key
- `user_id` - Foreign key to users table (user who attended)
- `attendance_date` - Date when user attended the gym
- `check_in_time` - Time when user checked in
- `check_out_time` - Time when user checked out (optional)
- `recorded_by_id` - Foreign key to users table (admin/trainer who recorded)
- `notes` - Additional notes about the attendance
- `created_at` - Attendance creation timestamp
- `updated_at` - Last update timestamp

## 🔄 Development Workflow

1. **Feature Development**: Add new endpoints in `app/api/v1/endpoints/`
2. **Model Changes**: Update models in `app/models/`
3. **Database Migrations**: Use Alembic for schema changes
4. **Testing**: Add tests for new functionality
5. **Deployment**: Push to Railway for automatic deployment

## 📝 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 WebSocket System Documentation

### Overview
The WebSocket system provides real-time communication between fingerprint devices, gym management systems, and user applications. It enables automated gym access control, user enrollment, and attendance tracking.

### Connection Endpoints

#### 1. User WebSocket (`/ws/user/{user_id}`)
**Purpose**: Individual user connections for fingerprint device communication
**Authentication**: User ID validation
**Use Case**: User applications connecting to receive real-time updates

**Connection Example:**
```javascript
const userSocket = new WebSocket(`ws://localhost:8000/ws/user/123`);
```

#### 2. Gym WebSocket (`/ws/gym/{gym_id}`)
**Purpose**: Gym-level connections for fingerprint device management
**Authentication**: Admin/trainer login required
**Use Case**: Fingerprint devices connecting to gym systems

**Connection Example:**
```javascript
const gymSocket = new WebSocket(`ws://localhost:8000/ws/gym/1`);
```

### Message Protocol

#### Authentication Message
```json
{
  "type": "login",
  "login_data": {
    "email": "trainer@gym.com",
    "password": "trainer123"
  }
}
```

**Response:**
```json
{
  "type": "connected"
}
```

#### Fingerprint Connection
```json
{
  "type": "fingerprint_connected",
  "gym_id": "1"
}
```

**Response:**
```json
{
  "type": "fingerprint_connection_stablished",
  "gym_id": "1"
}
```

#### User Enrollment
```json
{
  "type": "user",
  "user_id": "123"
}
```

**Response:**
```json
{
  "type": "start_enrollment",
  "user_id": "123",
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

#### Fingerprint Storage
```json
{
  "type": "store_fingerprint",
  "fingerprint_data": "base64_encoded_fingerprint_data",
  "finger": 1
}
```

**Response:**
```json
{
  "type": "fingerprint_stored",
  "message": "Huella digital almacenada exitosamente",
  "user_id": "123"
}
```

#### Template Download
```json
{
  "type": "download_templates"
}
```

**Response:**
```json
{
  "type": "template_data_set",
  "data": [
    {
      "id": "123",
      "full_name": "John Doe",
      "fingerprint1": "encrypted_data",
      "fingerprint2": "encrypted_data"
    }
  ]
}
```

### Error Handling

#### Authentication Error
```json
{
  "type": "error",
  "error": "Correo electrónico o contraseña incorrectos"
}
```

#### Connection Error
```json
{
  "type": "error",
  "error": "No se encontró la conexión del gimnasio"
}
```

#### Fingerprint Storage Error
```json
{
  "type": "store_error",
  "error": "Datos de huella digital faltantes"
}
```

### Health Monitoring

#### Health Check Endpoint
```bash
GET /ws/health
```

**Response:**
```json
{
  "active_connections": 5,
  "connected_users": ["123", "456", "789"],
  "gym_subscriptions": {
    "1": 2,
    "2": 1
  },
  "status": "healthy"
}
```

### Security Implementation

#### Fingerprint Encryption
- **Storage**: Base64 encoded fingerprint data is encrypted using AES encryption
- **Transmission**: Data is transmitted securely over WebSocket connections
- **Access Control**: Only authenticated admin/trainer users can access fingerprint data

#### Connection Validation
- **User Verification**: All user connections are validated against database records
- **Role Checking**: Device authentication requires admin/trainer privileges
- **Session Management**: Active connections are monitored and cleaned up on disconnect

### Integration Examples

#### JavaScript Client
```javascript
class FingerprintClient {
  constructor(gymId) {
    this.socket = new WebSocket(`ws://localhost:8000/ws/gym/${gymId}`);
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.socket.onopen = () => {
      console.log('Connected to gym system');
      this.authenticate();
    };

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
  }

  authenticate() {
    this.socket.send(JSON.stringify({
      type: 'login',
      login_data: {
        email: 'trainer@gym.com',
        password: 'trainer123'
      }
    }));
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connected':
        console.log('Authentication successful');
        break;
      case 'start_enrollment':
        console.log('Starting enrollment for:', message.full_name);
        break;
      case 'fingerprint_stored':
        console.log('Fingerprint stored successfully');
        break;
      case 'error':
        console.error('Error:', message.error);
        break;
    }
  }
}
```

#### Python Client
```python
import asyncio
import websockets
import json

async def fingerprint_client(gym_id):
    uri = f"ws://localhost:8000/ws/gym/{gym_id}"
    
    async with websockets.connect(uri) as websocket:
        # Authenticate
        auth_message = {
            "type": "login",
            "login_data": {
                "email": "trainer@gym.com",
                "password": "trainer123"
            }
        }
        await websocket.send(json.dumps(auth_message))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            if data.get("type") == "connected":
                print("Authentication successful")
                # Start fingerprint operations
                break

# Run client
asyncio.run(fingerprint_client(1))
```

### Troubleshooting

#### Common Issues
1. **Connection Refused**: Check if the WebSocket service is running
2. **Authentication Failed**: Verify admin/trainer credentials
3. **User Not Found**: Ensure user exists in the specified gym
4. **Fingerprint Storage Error**: Check fingerprint data format and encryption

#### Debug Mode
Enable debug logging to troubleshoot WebSocket connections:
```bash
uvicorn main:app --reload --log-level debug
```

#### Connection Monitoring
Use the health endpoint to monitor active connections:
```bash
curl http://localhost:8000/ws/health
```

### Example Login Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin"
}
```

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Check `DATABASE_URL` in `.env`
2. **JWT Errors**: Verify `SECRET_KEY` is set
3. **Import Errors**: Ensure all dependencies are installed
4. **Permission Errors**: Check user role and endpoint permissions

### Logs
```bash
# View Railway logs
railway logs

# Local development logs
uvicorn main:app --reload --log-level debug
```