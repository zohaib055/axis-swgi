# Command Center Migrations

Alembic migrations manage the Postgres schema for SWGI Command Center.

Run from `swgi-command-center/`:

```bash
DATABASE_URL=postgresql://swgi:swgi@localhost:5432/swgi_command_center \
  alembic upgrade head
```
