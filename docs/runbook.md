# On-call runbook

Run these commands from the repository root. This is a local demo setup, not a production recovery procedure.
Keep the shell open so its environment is available to subsequent commands.

## Prepare the environment

Use Python 3.12 or newer:

```bash
python3 -m venv .venv
```

```bash
. .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

Success: the virtual environment activates and pip completes without an error. If setup fails, install Python 3.12
or newer and the project dependencies, then repeat these commands. Gap: the repository does not specify an offline
dependency installation or a production environment setup.

## Start the database

```bash
docker compose up -d db
```

```bash
docker compose ps
```

Success: the database container is running and becomes healthy. If Docker cannot start it, start Docker and repeat
the commands; if it is not healthy, inspect its output:

```bash
docker compose logs db
```

Gap: the repository does not specify remedies for database startup errors or a production database connection.
The following connection is only for the local demo database configured in `compose.yaml`:

```bash
export DATABASE_URL="postgresql+psycopg://incidentdesk:$(docker compose exec -T db printenv POSTGRES_PASSWORD)@localhost:5432/incidentdesk"
```

Success: the command sets the URL for this shell using the local container's password. If another shell is used, run
it again there. If Docker reports that the container is not running, start the database before setting the URL again.

## Load the demo data

```bash
incidentdesk seed
```

Success: the command prints JSON with `services` and `incidents` counts. If it fails to connect, repeat the database
startup and URL commands above. If it fails because demo records already exist, do not repeat it against that database.
Gap: the repository does not provide a non-destructive procedure for reloading an already seeded database.
Do not use the CLI's reset option on data you need to keep: it drops every table.

## Run and check the service

```bash
incidentdesk serve
```

Success: Uvicorn reports that it is running on `http://127.0.0.1:8000`. Leave it running and use a second terminal
for this check:

```bash
curl -fsS http://127.0.0.1:8000/health
```

Success: the response contains `"status":"ok"` and a version. If the check fails, check the service terminal for
the error, confirm the database is healthy using the database commands above, and restart the service. If the port
is already in use, stop the conflicting service before restarting. Gap: the repository does not specify a production
service restart or escalation procedure.

## Run the tests

**Warning:** database tests drop and recreate tables. Use only a disposable local database, never a database whose
contents must be preserved. In a shell with the local URL set as above:

```bash
scripts/test.sh
```

Success: pytest reports a passing summary twice, once in UTC and once in Asia/Singapore. If the summary includes
database tests skipped because the URL is unset, start the disposable database, set the URL and rerun. If tests fail,
use the failure details printed by pytest; Gap: the repository does not specify an on-call escalation procedure for
test failures. To restore the demo data after database tests, **only on the disposable local database**, run:

```bash
incidentdesk seed --reset
```

This drops every table before loading the demo data. Success: it prints JSON with `services` and `incidents` counts.
If it fails to connect, repeat the database startup and URL commands above.

## List SLA breaches

In a shell with the database URL set:

```bash
incidentdesk sla
```

Success: each breach of an open incident is printed with its key, target and check time in UTC; no output means
there are no breaches to print. If the command fails to connect, repeat the database startup and URL commands above.
Gap: the repository does not specify how an on-call engineer should remediate or escalate a breach.

## Print a daily report

In a shell with the database URL set, this example prints the report for 14 October 2026:

```bash
incidentdesk report 2026-10-14
```

Success: JSON contains `day`, `opened`, `by_priority` and `still_open`; the day is in the service time zone.
For another day, run the same command with that calendar date in ISO format. If the date is invalid, use a valid
date; if the connection fails, repeat the database startup and URL commands above.
