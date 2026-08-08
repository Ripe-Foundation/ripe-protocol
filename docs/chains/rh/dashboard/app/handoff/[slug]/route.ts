import handoffJson from "./handoff.generated.json";

type HandoffDocument = {
  source: string;
  content: string;
};

const handoff = handoffJson as Record<string, HandoffDocument>;

export async function GET(
  _request: Request,
  context: { params: Promise<{ slug: string }> },
) {
  const { slug } = await context.params;
  const document = handoff[slug];

  if (!document) {
    return new Response("Handoff document not found.\n", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  return new Response(document.content, {
    headers: {
      "Cache-Control": "private, max-age=300",
      "Content-Disposition": `inline; filename="${slug}"`,
      "Content-Type": "text/plain; charset=utf-8",
      "X-Handoff-Source": document.source,
    },
  });
}
