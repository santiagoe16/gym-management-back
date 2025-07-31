# Gym Management API Tests

This directory contains all test files for the Gym Management API.

## Test File Locations

**Note**: All test files have been moved to the `tests/` folder where they belong:
- `tests/test_users.py` - User endpoint tests (pytest)
- `tests/test_gyms.py` - Gym endpoint tests (pytest) 
- `tests/test_plans.py` - Plan endpoint tests (pytest)
- `tests/conftest.py` - Pytest fixtures and configuration

## Manual Test Scripts

The manual test scripts are also in the `tests/` folder:
- `tests/test_users_manual.py` - Manual user endpoint tests
- `tests/test_gyms_manual.py` - Manual gym endpoint tests
- `tests/test_plans_manual.py` - Manual plan endpoint tests
- `tests/run_all_tests.py` - Master script to run all manual tests

## Running Tests

### Pytest Tests (Recommended)
```bash
# Run all pytest tests
pytest

# Run specific test file
pytest tests/test_users.py

# Run with verbose output
pytest -v
```

### Manual Tests
```bash
# Run all manual tests
python tests/run_all_tests.py

# Run specific manual test
python tests/test_users_manual.py
```

## Test Coverage

### User Endpoints
- ✅ Authentication (login)
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Role-based access control (Admin, Trainer, User)
- ✅ User search (by document ID, phone number)
- ✅ Plan assignment and management
- ✅ Trainer restrictions (can only view/update regular users)
- ✅ **NEW**: Plan modification via update_user endpoint

### Gym Endpoints
- ✅ CRUD operations
- ✅ Duplicate name validation
- ✅ Unauthorized access handling
- ✅ Pagination

### Plan Endpoints
- ✅ CRUD operations
- ✅ Duplicate name validation
- ✅ Trainer access restrictions
- ✅ Unauthorized access handling
- ✅ Pagination

## Recent Changes

### User Endpoint Updates
- Trainers can now only view/update regular users (not admins or other trainers)
- Regular users are automatically assigned to the current user's gym
- Plan validation is now against the current user's gym
- Added plan modification functionality via `update_user` endpoint

### Test Updates
- All test files moved to `tests/` folder
- Updated tests to reflect new trainer restrictions
- Added comprehensive plan modification tests
- Fixed function signature conflicts in `methods.py` 