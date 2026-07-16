import { ChangeEvent, FormEvent, useState } from "react";
import { compareHybridModes, resolveCustomUrl, uploadArchive } from "./api";

const modes = ["semantic", "keyword", "exact", "balanced"];
const modeLabels: Record<string, string> = {
  semantic: "Visual meaning",
  keyword: "Tags and captions",
  exact: "Literal match",
  balanced: "Fused ranking",
};

function formatWeights(weights: any) {
  return `V ${Math.round(weights.vector * 100)} / S ${Math.round(weights.sparse * 100)} / F ${Math.round(weights.fulltext * 100)} / M ${Math.round(weights.metadata * 100)}`;
}

function formatError(error: string) {
  if (error.includes("Compare failed: 400")) {
    return "Enter a non-empty query before comparing.";
  }
  if (error.includes("Compare failed") || error.includes("Upload failed")) {
    return "Search failed. Check SeekDB and embedding credentials, then try again.";
  }
  return error;
}

function EvidenceTerms({ terms }: { terms?: string[] }) {
  const visibleTerms = (terms ?? []).filter(Boolean).slice(0, 6);
  if (!visibleTerms.length) {
    return <div className="evidence-terms evidence-terms--empty">No lexical evidence</div>;
  }
  return (
    <div className="evidence-terms" aria-label="Matched evidence terms">
      {visibleTerms.map((term) => (
        <span key={term}>{term}</span>
      ))}
    </div>
  );
}

export default function HybridCompare() {
  const [query, setQuery] = useState("blue shoe with visible logo");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const text = query.trim();
    if (!text) {
      setError("Enter a query before comparing.");
      return;
    }
    try {
      setData(await compareHybridModes(text, 5));
    } catch (err) {
      setError(String(err));
    }
  }

  async function onUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    setUploadStatus("Uploading archive");
    try {
      const result = await uploadArchive(file);
      setUploadStatus(`Indexed ${result.indexed} image(s) from upload.`);
    } catch (err) {
      setError(String(err));
      setUploadStatus("Upload failed.");
    }
  }

  return (
    <section className="compare">
      <header className="workspace-panel workspace-panel--compare">
        <div>
          <p className="section-kicker">Compare modes</p>
          <h2>One query, four ranking strategies.</h2>
          <p>Use this view when you want to see which signal changed the order.</p>
        </div>
      </header>

      <div className="compare__toolbar">
        <form className="compare__form" onSubmit={onSubmit}>
          <input
            aria-label="Search query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit">Compare</button>
        </form>
        <label className="upload-control">
          Upload archive
          <input type="file" accept=".zip,.tar,.gz,.bz2,.xz" onChange={onUpload} />
        </label>
      </div>
      {uploadStatus && <p className="status">{uploadStatus}</p>}
      {error && (
        <div className="error-panel" role="alert">
          <strong>{formatError(error)}</strong>
          <span>{error}</span>
        </div>
      )}
      <div className="compare__grid">
        {modes.map((mode) => {
          const trace = data?.[mode];
          return (
            <article className="mode" key={mode}>
              <header>
                <span>{modeLabels[mode]}</span>
                <strong>{mode}</strong>
              </header>
              <div className="weight-rail">
                <span className={`weight-rail__bar weight-rail__bar--${mode}`} />
              </div>
              <small>{trace?.weights ? formatWeights(trace.weights) : "Run Compare to populate"}</small>
              {(trace?.hits ?? []).map((hit: any, index: number) => (
                <div className="result result--compare" key={hit.image_id}>
                  <div className="result__media">
                    <img src={resolveCustomUrl(hit.image_url)} alt={hit.caption ?? hit.file_name} />
                    <span className="result__rank">#{index + 1}</span>
                  </div>
                  <div className="result__body">
                    <div className="result__headline">
                      <strong className="result__file">{hit.file_name}</strong>
                      <small className="result__score">fused {hit.fused_score?.toFixed?.(3) ?? "n/a"}</small>
                    </div>
                    <p className="result__caption">{hit.caption}</p>
                    <EvidenceTerms terms={hit.matched_terms} />
                  </div>
                </div>
              ))}
              {!trace && <p className="empty-lane">Results will appear here after a DB-backed search.</p>}
            </article>
          );
        })}
      </div>
    </section>
  );
}
