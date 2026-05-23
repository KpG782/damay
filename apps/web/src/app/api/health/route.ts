import { NextResponse } from "next/server";
import { fetchHealthz } from "@/lib/api";

export const dynamic = "force-dynamic";

/**
 * Local health endpoint used by the Dockerfile HEALTHCHECK. Proxies the
 * backend's deep check and falls back to a degraded local-only OK if the API
 * is unreachable — the web app itself is healthy as long as this route 200s.
 */
export async function GET() {
  try {
    const { data, isLive } = await fetchHealthz();
    return NextResponse.json(
      { web: "ok", api: isLive ? data.status : "unreachable", checks: data.checks },
      { status: 200 }
    );
  } catch {
    return NextResponse.json({ web: "ok", api: "unreachable" }, { status: 200 });
  }
}
