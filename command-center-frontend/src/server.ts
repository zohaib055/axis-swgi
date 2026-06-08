import "./lib/error-capture";

import { consumeLastCapturedError } from "./lib/error-capture";
import { renderErrorPage } from "./lib/error-page";

type ServerEntry = {
  fetch: (request: Request, env: unknown, ctx: unknown) => Promise<Response> | Response;
};

let serverEntryPromise: Promise<ServerEntry> | undefined;

async function getServerEntry(): Promise<ServerEntry> {
  if (!serverEntryPromise) {
    serverEntryPromise = import("@tanstack/react-start/server-entry").then(
      (m) => ((m as { default?: ServerEntry }).default ?? (m as unknown as ServerEntry)),
    );
  }
  return serverEntryPromise;
}

function brandedErrorResponse(): Response {
  return new Response(renderErrorPage(), {
    status: 500,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

function isCatastrophicSsrErrorBody(body: string, responseStatus: number): boolean {
  let payload: unknown;
  try {
    payload = JSON.parse(body);
  } catch {
    return false;
  }

  if (!payload || Array.isArray(payload) || typeof payload !== "object") {
    return false;
  }

  const fields = payload as Record<string, unknown>;
  const expectedKeys = new Set(["message", "status", "unhandled"]);
  if (!Object.keys(fields).every((key) => expectedKeys.has(key))) {
    return false;
  }

  return (
    fields.unhandled === true &&
    fields.message === "HTTPError" &&
    (fields.status === undefined || fields.status === responseStatus)
  );
}

function envValue(env: unknown, key: string): string {
  if (env && typeof env === "object" && key in env) {
    const value = (env as Record<string, unknown>)[key];
    return typeof value === "string" ? value : "";
  }
  return typeof process !== "undefined" ? process.env[key] ?? "" : "";
}

async function proxyCommandCenter(request: Request, env: unknown): Promise<Response> {
  const commandCenterUrl = envValue(env, "SWGI_COMMAND_CENTER_URL").replace(/\/$/, "");
  const apiToken = envValue(env, "SWGI_API_TOKEN");

  if (!commandCenterUrl) {
    return Response.json(
      { detail: "Command Center proxy is not configured" },
      { status: 503 },
    );
  }

  const incoming = new URL(request.url);
  const upstreamPath = incoming.pathname.replace(/^\/api\/command-center/, "") || "/";
  const upstream = new URL(`${commandCenterUrl}${upstreamPath}${incoming.search}`);
  const headers = new Headers(request.headers);
  const browserAuth = request.headers.get("authorization");
  if (browserAuth) {
    headers.set("authorization", browserAuth);
  } else if (apiToken && upstreamPath !== "/v1/auth/login") {
    headers.set("authorization", `Bearer ${apiToken}`);
  } else {
    headers.delete("authorization");
  }
  headers.set("accept", "application/json");
  headers.delete("cookie");
  headers.delete("host");

  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();

  return fetch(upstream, {
    method: request.method,
    headers,
    body,
  });
}

// h3 swallows in-handler throws into a normal 500 Response with body
// {"unhandled":true,"message":"HTTPError"} — try/catch alone never fires for those.
async function normalizeCatastrophicSsrResponse(response: Response): Promise<Response> {
  if (response.status < 500) return response;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return response;

  const body = await response.clone().text();
  if (!isCatastrophicSsrErrorBody(body, response.status)) {
    return response;
  }

  console.error(consumeLastCapturedError() ?? new Error(`h3 swallowed SSR error: ${body}`));
  return brandedErrorResponse();
}

export default {
  async fetch(request: Request, env: unknown, ctx: unknown) {
    try {
      const url = new URL(request.url);
      if (url.pathname.startsWith("/api/command-center/")) {
        return await proxyCommandCenter(request, env);
      }
      const handler = await getServerEntry();
      const response = await handler.fetch(request, env, ctx);
      return await normalizeCatastrophicSsrResponse(response);
    } catch (error) {
      console.error(error);
      return brandedErrorResponse();
    }
  },
};
