# SWGI Command Center Frontend

Production UI for SWGI Command Center.

## Runtime Configuration

Set these variables when connecting to the live Command Center API:

```bash
VITE_SWGI_COMMAND_CENTER_PROXY=/api/command-center
SWGI_COMMAND_CENTER_URL=https://command-center.example.com
SWGI_API_TOKEN=<optional_bootstrap_or_service_token>
```

The UI is live-only and does not fall back to mock data. `SWGI_API_TOKEN` is
server-side only and optional for service-mode proxy calls. Human users sign in
through `/v1/auth/login`; the browser forwards the returned user session token
to the backend.

## Admin Access

The frontend has a protected admin shell with backend-backed login and
role-based permissions:

- `platform_admin`
- `platform_viewer`
- `org_admin`
- `org_viewer`
- `operator`

Users and sessions are stored in Command Center Postgres. Operator and API
tokens stay separate from human user sessions.

## Local Development

```bash
bun install
bun run dev
```

If using npm instead of Bun:

```bash
npm install
npm run dev
```

## Production Build

```bash
bun run build
```

For Cloudflare deployments, keep the token as a secret:

```bash
wrangler secret put SWGI_API_TOKEN
```

Configure `SWGI_COMMAND_CENTER_URL` in the deployment environment or Wrangler
project settings.

The live API token should be supplied by the deployment environment or secret
manager. Do not commit API tokens or generated Operator install tokens.
