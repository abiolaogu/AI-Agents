# Database Migrations

This directory contains Alembic database migrations for the AI Agents Orchestration Engine.

## Prerequisites

Install Alembic and async PostgreSQL driver:

```bash
pip install alembic asyncpg
```

## Configuration

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_agents
```

## Usage

### Apply All Migrations

```bash
cd services/orchestration_engine
alembic upgrade head
```

### Rollback Last Migration

```bash
alembic downgrade -1
```

### Rollback to Specific Revision

```bash
alembic downgrade 20250107_0001
```

### View Current Revision

```bash
alembic current
```

### View Migration History

```bash
alembic history
```

### Create New Migration (Manual)

```bash
alembic revision -m "add_new_table"
```

### Create New Migration (Auto-generate from Models)

```bash
alembic revision --autogenerate -m "add_new_table"
```

Note: Auto-generate works by comparing the current database schema with your SQLAlchemy models. Make sure your models are imported in `env.py`.

## Migration Files

Migration files are stored in `versions/` directory with the naming format:
`YYYYMMDD_HHMM_revision_slug.py`

Each migration contains:
- `upgrade()`: Apply the migration
- `downgrade()`: Rollback the migration

## Best Practices

1. **Test migrations locally** before applying to production
2. **Backup database** before running migrations in production
3. **Review auto-generated migrations** before running them
4. **Keep migrations small** and focused on single changes
5. **Never modify** already-applied migrations
6. **Use transactions** for data migrations

## Production Deployment

For production, run migrations as part of your deployment process:

```bash
# In your deployment script or Kubernetes job
alembic upgrade head
```

Or use the provided entrypoint script that runs migrations before starting the app:

```bash
# In Dockerfile or docker-compose
command: ["sh", "-c", "alembic upgrade head && uvicorn orchestration_engine.main:app --host 0.0.0.0 --port 8000"]
```

## Troubleshooting

### "Target database is not up to date"

Run migrations to bring database up to date:
```bash
alembic upgrade head
```

### "Can't locate revision"

Ensure all migration files are present and the revision chain is not broken.

### "Table already exists"

If starting fresh, you can stamp the database as current without running migrations:
```bash
alembic stamp head
```

### Connection Issues

Verify your `DATABASE_URL` is correct and the database is accessible.
