# Database Migrations Guide

This document explains how to use the migration system for the Gym Management application.

## Overview

The application uses **Alembic** for database migrations, which allows you to:
- Track database schema changes
- Apply changes safely across environments
- Rollback changes if needed
- Keep database schema in sync with your models

## Quick Start

### 1. Check Migration Status
```bash
python migrate.py status
```

### 2. Create a New Migration
When you make changes to your models, create a migration:
```bash
python migrate.py create "Add new user field"
```

### 3. Apply Migrations
```bash
python migrate.py upgrade
```

## Migration Commands

### Using the Helper Script
```bash
# Check current status
python migrate.py status

# Create a new migration
python migrate.py create "Description of changes"

# Apply all pending migrations
python migrate.py upgrade

# Rollback last migration
python migrate.py downgrade

# Show migration history
python migrate.py history

# Reset database (WARNING: Deletes all data!)
python migrate.py reset
```

### Using Alembic Directly
```bash
# Check current revision
alembic current

# Show migration heads
alembic heads

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show history
alembic history
```

## Migration Workflow

### 1. Development Workflow
1. **Make changes** to your SQLModel classes in `app/models/`
2. **Create migration**: `python migrate.py create "Description"`
3. **Review** the generated migration file in `alembic/versions/`
4. **Apply migration**: `python migrate.py upgrade`
5. **Test** your changes

### 2. Production Deployment
1. **Backup** your database
2. **Apply migrations**: `python migrate.py upgrade`
3. **Verify** the application works correctly

## Migration Files

Migration files are stored in `alembic/versions/` and follow this naming pattern:
```
{revision_id}_{description}.py
```

Example: `d71850c56b46_initial_migration.py`

### Migration File Structure
```python
"""Description of the migration

Revision ID: d71850c56b46
Revises: 62577725e0b0
Create Date: 2025-07-25 13:03:29.278995

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd71850c56b46'
down_revision = '62577725e0b0'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Migration commands here
    pass

def downgrade() -> None:
    # Rollback commands here
    pass
```

## Best Practices

### 1. Migration Naming
- Use descriptive names: `add_user_email_field` not `update_1`
- Use present tense: `add_user_email_field` not `added_user_email_field`
- Be specific about what changes

### 2. Migration Content
- **Always review** auto-generated migrations
- **Test migrations** on a copy of your data
- **Keep migrations small** and focused
- **Include rollback logic** in `downgrade()`

### 3. Database Changes
- **Never modify** existing migration files after they've been applied
- **Create new migrations** for additional changes
- **Test rollbacks** before applying to production

## Troubleshooting

### Common Issues

#### 1. "Revision not found" Error
```bash
# Check current revision
alembic current

# Check available revisions
alembic history

# If needed, stamp the current revision
alembic stamp head
```

#### 2. "Table already exists" Error
This usually means the database is ahead of your migrations:
```bash
# Check what tables exist
alembic current

# Stamp the current state
alembic stamp head
```

#### 3. "No changes detected" when creating migration
- Make sure your models are imported in `app/models/__init__.py`
- Check that your model changes are actually different from the database
- Verify the database connection is working

### Recovery Procedures

#### Reset Migration State
If your migration state gets corrupted:
```bash
# WARNING: This will delete all data!
python migrate.py reset
```

#### Manual Migration Fix
If you need to manually fix migration state:
```bash
# Mark current revision
alembic stamp <revision_id>

# Or mark as up to date
alembic stamp head
```

## Environment Configuration

The migration system uses these environment variables:
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password  
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name

Make sure these are set in your `.env` file.

## Model Changes

When you modify your SQLModel classes:

1. **Add fields**: Just add them to your model class
2. **Remove fields**: Add them to the migration's `downgrade()` method
3. **Change field types**: Create a migration that handles the conversion
4. **Add indexes**: They'll be auto-detected
5. **Add relationships**: Make sure foreign keys are properly defined

## Example: Adding a New Field

1. **Modify your model**:
```python
class User(SQLModel, table=True):
    # ... existing fields ...
    phone_number: Optional[str] = Field(default=None, index=True)
```

2. **Create migration**:
```bash
python migrate.py create "Add phone number to users"
```

3. **Review the generated migration**:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    op.drop_column('users', 'phone_number')
```

4. **Apply the migration**:
```bash
python migrate.py upgrade
```

## Support

If you encounter issues with migrations:
1. Check the migration logs
2. Verify your database connection
3. Review the generated migration files
4. Test on a copy of your data first 