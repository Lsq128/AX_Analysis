import { type NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * SSE proxy — Next.js rewrites buffer long-lived streams, so /events is handled
 * here and piped through without waiting for the upstream body to finish.
 */
export async function GET(
  req: NextRequest,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params;
  const apiUrl = process.env.API_PROXY_URL || "http://localhost:8000";
  const upstreamUrl = `${apiUrl}/api/v1/analyses/${encodeURIComponent(id)}/events`;

  const headers = new Headers();
  const authorization = req.headers.get("authorization");
  const userId = req.headers.get("x-user-id");
  if (authorization) headers.set("authorization", authorization);
  if (userId) headers.set("x-user-id", userId);
  headers.set("accept", "text/event-stream");

  const upstream = await fetch(upstreamUrl, {
    headers,
    signal: req.signal,
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    const detail = await upstream.text().catch(() => upstream.statusText);
    return new Response(detail || "SSE upstream failed", {
      status: upstream.status || 502,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
