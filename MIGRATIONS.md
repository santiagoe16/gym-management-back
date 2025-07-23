# Database Migrations with Alembic

This project uses Alembic for database migrations, allowing you to make changes to the database schema in a controlled and versioned way.

## 🚀 Quick Start

### Initialize the Database
```bash
python migrate.py init
```

### Create a New Migration
```bash
python migrate.py create "add_new_column_to_users"
```

### Apply Migrations
```bash
python migrate.py upgrade
```

### Rollback Last Migration
```bash
python migrate.py downgrade
```

## 📋 Available Commands

### Using the Helper Script (`migrate.py`)
- `python migrate.py init` - Initialize database with current schema
- `python migrate.py create <message>` - Create a new migration
- `python migrate.py upgrade` - Apply pending migrations
- `python migrate.py downgrade` - Rollback last migration
- `python migrate.py history` - Show migration history
- `python migrate.py current` - Show current migration
- `python migrate.py status` - Show migration status

### Direct Alembic Commands
- `alembic revision --autogenerate -m "message"` - Create migration
- `alembic upgrade head` - Apply all pending migrations
- `alembic upgrade +1` - Apply next migration
- `alembic downgrade -1` - Rollback last migration
- `alembic downgrade base` - Rollback all migrations
- `alembic current` - Show current migration
- `alembic history` - Show migration history
- `alembic show <revision>` - Show specific migration

## 🔧 Workflow

### 1. Making Schema Changes
1. Modify your SQLModel models in `app/models/`
2. Create a migration: `python migrate.py create "description_of_changes"`
3. Review the generated migration file in `alembic/versions/`
4. Apply the migration: `python migrate.py upgrade`

### 2. Example Workflow
```bash
# 1. Add a new field to User model
# Edit app/models/user.py

# 2. Create migration
python migrate.py create "add_phone_number_to_users"

# 3. Review the generated migration
# Check alembic/versions/xxxx_add_phone_number_to_users.py

# 4. Apply migration
python migrate.py upgrade
```

## 📁 File Structure

```
alembic/
├── __init__.py
├── env.py                 # Alembic environment configuration
├── script.py.mako        # Migration script template
└── versions/             # Migration files
    ├── __init__.py
    └── xxxx_migration_name.py

alembic.ini              # Alembic configuration
migrate.py               # Helper script
MIGRATIONS.md            # This file
```

## ⚠️ Important Notes

### Before Creating Migrations
1. **Backup your database** before applying migrations in production
2. **Test migrations** in a development environment first
3. **Review generated migrations** before applying them

### Migration Best Practices
1. **Use descriptive names** for migrations
2. **One change per migration** when possible
3. **Test both upgrade and downgrade** operations
4. **Never modify existing migration files** that have been applied

### Environment Variables
Make sure your `.env` file contains the correct database credentials:
```
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=your_port
DB_NAME=your_database
```

## 🐛 Troubleshooting

### Common Issues

1. **"Target database is not up to date"**
   ```bash
   python migrate.py upgrade
   ```

2. **"Can't locate revision identified by"**
   ```bash
   python migrate.py current
   python migrate.py history
   ```

3. **Migration conflicts**
   - Check migration history: `python migrate.py history`
   - Resolve conflicts manually in migration files
   - Consider rolling back: `python migrate.py downgrade`

### Reset Database (Development Only)
```bash
# Drop and recreate database
# Then run:
python migrate.py init
```

## 🔄 Migration Examples

### Adding a New Table
1. Create model in `app/models/`
2. `python migrate.py create "add_products_table"`
3. `python migrate.py upgrade`

### Adding a Column
1. Add field to existing model
2. `python migrate.py create "add_price_to_products"`
3. `python migrate.py upgrade`

### Modifying a Column
1. Change field definition in model
2. `python migrate.py create "modify_product_price_type"`
3. `python migrate.py upgrade`

### Removing a Column
1. Remove field from model
2. `python migrate.py create "remove_old_column"`
3. `python migrate.py upgrade`

## 📚 Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/) 