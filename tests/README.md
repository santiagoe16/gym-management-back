# User Endpoints Test Suite

This directory contains comprehensive tests for the user endpoints in the Gym Management API.

## Test Files

- `conftest.py` - Pytest configuration and fixtures
- `test_users.py` - Comprehensive test suite for user endpoints
- `test_users.py` (root) - Simple manual test script

## Running Tests

### Option 1: Manual Test Script (Recommended for quick testing)

The manual test script is located in the root directory and can be run directly:

```bash
# Install dependencies if not already installed
pip install requests

# Run the test script (make sure your server is running on localhost:8000)
python test_users.py

# Or specify a different URL
python test_users.py http://your-server:8000/api/v1
```

This script will:
- Test authentication
- Create test data (gym, plan)
- Test all user endpoints
- Provide detailed output with pass/fail status

### Option 2: Pytest Suite (For automated testing)

```bash
# Install pytest dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_users.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Coverage

The test suite covers the following user endpoints:

### Authentication Tests
- ✅ Admin login
- ✅ Trainer login
- ✅ Unauthorized access

### User Management Tests
- ✅ Read all users (admin access)
- ✅ Read all users (trainer access - gym-scoped)
- ✅ Create admin user
- ✅ Create trainer user
- ✅ Create regular user with plan
- ✅ Update user
- ✅ Delete user
- ✅ Read specific user by ID

### Search Tests
- ✅ Search user by document ID
- ✅ Search users by phone number (partial match)

### Role-based Tests
- ✅ Read trainers only
- ✅ Read regular users only
- ✅ Filter users by gym

### Validation Tests
- ✅ Duplicate email validation
- ✅ Duplicate document ID validation
- ✅ Invalid plan validation
- ✅ Role-based access control
- ✅ Trainer restrictions

### Edge Cases
- ✅ Non-existent user handling
- ✅ Invalid gym/plan references
- ✅ Pagination
- ✅ Error responses

## Prerequisites

Before running the tests, ensure:

1. **Server is running**: The FastAPI server should be running on the specified URL
2. **Database is set up**: The database should be initialized with the required tables
3. **Test users exist**: The following test users should exist in the database:
   - Admin: `admin@test.com` / `adminpass123`
   - Trainer: `trainer@test.com` / `trainerpass123`

## Test Data Setup

The manual test script will automatically:
1. Create a test gym if it doesn't exist
2. Create a test plan if it doesn't exist
3. Use these for creating test users

## Expected Test Results

When all tests pass, you should see output like:

```
🚀 Starting User Endpoints Test Suite
==================================================
=== Testing Authentication ===
✅ PASS Admin Login

✅ PASS Trainer Login

=== Testing Read Users ===
✅ PASS Read Users (Admin)
   Found 3 users

=== Testing Create Admin User ===
✅ PASS Create Admin User
   Created user ID: 4

...

==================================================
📊 Test Results: 9/9 tests passed
🎉 All tests passed!
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Make sure the server is running
2. **Authentication failed**: Check that test users exist in the database
3. **Database errors**: Ensure the database is properly initialized
4. **Import errors**: Install required dependencies

### Debug Mode

To see more detailed error information, you can modify the test script to print full response details:

```python
# In test_users.py, add this to see full responses
print(f"Response: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Body: {response.text}")
```

## Adding New Tests

To add new tests:

1. For manual testing: Add new test methods to the `UserEndpointTester` class
2. For pytest: Add new test functions to `tests/test_users.py`

Follow the existing patterns for consistency. 