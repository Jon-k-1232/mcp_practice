# MCP Rally Server

A minimal Model Context Protocol-style server that connects to CA Rally (Agile Central), fetches
defect data, and surfaces analytics around potential root causes and trends.

## Features

-  FastAPI service exposing `/defects` and `/defects/analysis` endpoints requiring a `workspace`
   query parameter plus convenient filters for state and ISO8601 date ranges.
-  New `/artifacts/transcript` endpoint that takes a standup transcript, identifies referenced
   Rally work items by formatted ID, updates their status/blocked flags automatically, and logs the
   transcript snippet as a Rally conversation post.
-  Manual artifact update endpoint for posting ad-hoc comments (and optional state/blocker changes)
   to any Rally work item by formatted ID.
-  Configurable through environment variables loaded from `.env`.
-  Modular code structure splitting auth, client, and analytics logic.
-  Heuristic analysis to highlight leading contributors and suspected causes.

## Getting Started

1. **Create a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -e .
   ```

3. **Configure Rally credentials**

   Update the `.env` file with your Rally details:

   -  `RALLY_API_KEY` – Rally personal API key.
   -  `RALLY_BASE_URL` – Rally instance base URL (defaults to `https://rally1.rallydev.com`).
   -  `RALLY_PAGE_SIZE` – Page size for Rally queries (defaults to `2000`).

4. **Run the server**

   ```bash
   python scripts/run_server.py
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000) with an OpenAPI UI at
   `/docs`.

## Branching Strategy

-  `master` – Production copy used for releases and long-term archival.
-  `production` – Tracks the code that is currently deployed.
-  `develop` – Integration branch for active development.
-  Personal work should branch off `develop` using your name followed by a short slug, e.g.
   `git checkout -b jane-update-transcript` from `develop`.

## Environment Configuration

-  `.env` lives at the project root (`mcp_practice/.env`) and is loaded automatically by the app.
-  At minimum set:

   ```env
   RALLY_API_KEY=your_api_key_here
   RALLY_BASE_URL=https://rally1.rallydev.com
   RALLY_PAGE_SIZE=2000
   ```

-  When working on multiple environments, keep separate `.env` files (e.g. `.env.dev`, `.env.prod`)
   and point `load_config` to the desired file via the `env_file` argument (see `src/mcp_rally/config.py`).

## Project Layout

-  `src/mcp_rally/config.py` – Loads environment configuration.
-  `src/mcp_rally/auth/` – Authentication helpers (e.g., Rally API headers).
-  `src/mcp_rally/api/` – FastAPI routers for defects and transcript processing.
-  `src/mcp_rally/deps.py` – Shared dependency providers (Rally client/config instances).
-  `src/mcp_rally/rally_client.py` – Handles REST calls to Rally.
-  `src/mcp_rally/analysis/defects.py` – Aggregates and analyzes defect data.
-  `src/mcp_rally/server.py` – Application factory that wires routers into FastAPI.
-  `scripts/run_server.py` – Convenience launcher for the server.
-  `terraform/` – Infrastructure-as-code for dev and prod AWS environments.

## Terraform Deployment

-  Update `terraform/dev/terraform.tfvars` (and the prod equivalent) with your VPC, subnet,
   certificate, and container image details before applying.
-  From the desired environment directory run:

  ```bash
  cd terraform/dev
  terraform init
  terraform plan
  terraform apply
  ```

-  Push your Docker image to the provisioned ECR repo using the value output as `ecr_repository_url`.

### Example API Call

Fetch closed defects updated in May 2024 for a given workspace:

```bash
curl "http://localhost:8000/defects?workspace=TeamWorkspace&state=closed&updated_after=2024-05-01T00:00:00Z&updated_before=2024-05-31T23:59:59Z"
```

### Standup Transcript Endpoint

Submit a meeting transcript, providing the workspace (and optional project) scope:

```bash
curl -X POST "http://localhost:8000/artifacts/transcript" \
  -H "Content-Type: application/json" \
  -d '{
        "workspace": "/workspace/123456789",
        "project": "/project/987654321",
        "transcript": "US12345 is in progress and should wrap tomorrow. DE54321 is blocked by the database migration."
      }'
```

The response summarizes which artifacts were updated and which references (if any) were skipped
because the type is unsupported or the transcript did not contain actionable status cues. Each
successful update also adds the matching transcript snippet to the Rally item's discussion thread.

### Manual Artifact Update Endpoint

Record a one-off status/comment update for a specific artifact:

```bash
curl -X POST "http://localhost:8000/artifacts/manual" \
  -H "Content-Type: application/json" \
  -d '{
        "workspace": "/workspace/123456789",
        "formatted_id": "US12345",
        "state": "In-Progress",
        "comment": "Jon is the best and is wrapping this up today."
      }'
```

The server updates any provided state/blocked fields and posts the supplied comment to the Rally
discussion thread for that item.

## Next Steps

-  Add persistence or caching for frequent analyses.
-  Expand analytics heuristics with organization-specific insights.
-  Write automated tests against mocked Rally responses.
