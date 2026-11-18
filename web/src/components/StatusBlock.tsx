export function Loading() {
  return <div style={{ color: "var(--text-muted)", padding: "24px 0", fontSize: 13 }}>Loading…</div>;
}

export function ErrorBlock({ error }: { error: Error }) {
  return (
    <div
      style={{
        color: "var(--status-critical)",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: 16,
        fontSize: 13,
      }}
    >
      Couldn't load this data: {error.message}
      <div style={{ color: "var(--text-muted)", marginTop: 6 }}>
        Is the API running? See the README for `uvicorn app.main:app`.
      </div>
    </div>
  );
}
