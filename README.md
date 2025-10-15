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

## Endpoint Usage

### Defect Insights (`GET /defects`, `GET /defects/analysis`)

Purpose: investigate defect data, track trends, and spot root causes.

1. Configure your Rally scope by supplying the `workspace` (e.g., `/workspace/123456789`).
2. Optionally add filters such as `state`, `project`, `limit`, `created_after`, `updated_after`, or a
   WSAPI `query`.
3. Call:

   ```bash
   curl "http://localhost:8000/defects?workspace=/workspace/123456789&state=In-Progress&limit=50"
   ```

4. For aggregate analytics, use the `/defects/analysis` variant with the same parameters:

   ```bash
   curl "http://localhost:8000/defects/analysis?workspace=/workspace/123456789&state=Closed"
   ```

   The response summarizes totals, state/severity distribution, leading owners/tags, weekly trend
   buckets, and heuristic root-cause cues.

### Standup Transcript Automation (`POST /artifacts/transcript`)

Purpose: feed a meeting transcript and let the server update Rally items automatically.

Steps:

1. Ensure your transcript references Rally work items by formatted ID (e.g., `US12345`, `DE54321`).
2. POST JSON containing:
   - `workspace` (`/workspace/{oid}`) and optional `project`.
   - `transcript` with the full text/summary.
3. The service parses the text, maps status keywords to valid state/blocked updates, applies them
   where the artifact type allows, and posts the snippet as a comment.
4. The response lists which artifacts were updated and which were skipped with reasons.

Example:

```bash
curl -X POST "http://localhost:8000/artifacts/transcript" \
  -H "Content-Type: application/json" \
  -d '{
        "workspace": "/workspace/123456789",
        "project": "/project/987654321",
        "transcript": "US12345 is in progress and should wrap tomorrow. DE54321 is blocked by the database migration."
      }'
```

### Manual Artifact Update (`POST /artifacts/manual`)

Purpose: post an ad-hoc comment (optionally adjusting state/blocked) to any Rally artifact.

Steps:

1. Gather the target `formatted_id` and scope identifiers.
2. Compose the comment text you want stored in the artifact’s discussion thread.
3. Optionally include `state`, `blocked`, and `blocked_reason` to change structured fields.
4. Send the request:

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

5. The server applies the field updates (when the artifact type supports them) and posts the comment
   as a Rally ConversationPost.

## AI Assistant Integration

This project exposes Rally data and actions through the Model Context Protocol (MCP) over HTTP using
FastAPI. The steps below outline how to register the server with popular MCP-capable assistants.

### Claude Desktop

1. Install the latest Claude desktop app (macOS/Windows) that supports MCP.
2. Create or edit `~/.claude/config.yaml` (macOS) or `%APPDATA%\Claude\config.yaml` (Windows).
3. Add an entry under `mcpServers`:

   ```yaml
   mcpServers:
     mcp-rally:
       command: python
       args:
         - -m
         - mcp_rally.server
       env:
         RALLY_API_KEY: "<your_api_key>"
   ```

4. Restart Claude and open the MCP panel to enable the new “mcp-rally” tool.
5. Ask Claude to run a command such as `call mcp-rally /defects ...` to verify connectivity.

### GitHub Copilot (VS Code / JetBrains)

1. Ensure you have the latest Copilot Chat extension (VS Code) or plugin (JetBrains) with MCP
   support enabled (`copilot.experimental.mcp` flag in VS Code settings).
2. Create `~/.config/github-copilot/mcp.json` (Linux/macOS) or
   `%APPDATA%\GitHub Copilot\mcp.json` (Windows).
3. Register the server:

   ```json
   {
     "servers": {
       "mcp-rally": {
         "command": "python",
         "args": ["-m", "mcp_rally.server"],
         "env": {
           "RALLY_API_KEY": "<your_api_key>"
         }
       }
     }
   }
   ```

4. Reload the IDE. In Copilot Chat, use `/tools` (VS Code) or the MCP tool picker to invoke the
   Rally server.
5. Run a sample prompt (e.g., “Use mcp-rally to analyze defects in workspace …”) to confirm the
   integration.

### ChatGPT Desktop / Web with MCP

1. Opt into MCP beta in ChatGPT settings (if available in your account).
2. Create `~/.openai/devtools/mcp.json` with:

   ```json
   {
     "mcpServers": {
       "mcp-rally": {
         "command": "python",
         "args": ["-m", "mcp_rally.server"],
         "env": {
           "RALLY_API_KEY": "<your_api_key>"
         }
       }
     }
   }
   ```

3. Restart the ChatGPT client. A new “mcp-rally” tool should appear under available integrations.
4. Trigger the tool via `/mcp-rally` (desktop) or the Tools dropdown (web) and execute an endpoint to
   ensure it responds.

> **Note:** Paths/config formats may change as MCP support evolves. Consult the latest documentation
> for each assistant if these locations differ.

## Testing Workflows

### Local Environment

1. Activate your virtual environment and run the server:

   ```bash
   python scripts/run_server.py
   ```

2. Hit `http://localhost:8000/docs` to exercise endpoints interactively.
3. Use `curl`, HTTPie, or your assistant integrations pointing to localhost to validate new logic.
4. Install dev dependencies and execute the automated test suite (FastAPI integration checks and
   transcript parsing coverage):

   ```bash
   pip install -e .[dev]
   pytest
   ```

### Production/Staging

1. Build and publish a Docker image that contains your changes.
2. Update Terraform variables in `terraform/dev` or `terraform/prod` with the new image tag and
   deploy via `terraform apply`.
3. Configure the assistant environments to point at the deployed URL (instead of localhost) by
   adjusting the `command`/`args` (e.g., run via a lightweight proxy) or by exposing the HTTP
   endpoint through your infrastructure.
4. Smoke-test endpoints using the same curl commands against the production load balancer before
   enabling them for end-users.

## Next Steps

-  Add persistence or caching for frequent analyses.
-  Expand analytics heuristics with organization-specific insights.
-  Write automated tests against mocked Rally responses.
