import { useEffect, useState } from "react";
import { compareHybridModes, getSamplePack, ingestSamplePack, resolveCustomUrl, samplePackDownloadUrl } from "./api";

const modes = ["semantic", "keyword", "exact", "balanced"];
const modeLabels: Record<string, string> = {
  semantic: "Visual meaning",
  keyword: "Tags and captions",
  exact: "Literal match",
  balanced: "Fused ranking",
};

type SampleCase = {
  id: string;
  query: string;
  recommended_mode: string;
  what_to_notice: string;
  expected_effect: string;
  expected_top_by_mode?: Record<string, string>;
};

type SamplePack = {
  cases: SampleCase[];
  manifest?: {
    images?: unknown[];
  };
};

function formatWeights(weights: any) {
  return `V ${Math.round(weights.vector * 100)} / S ${Math.round(weights.sparse * 100)} / F ${Math.round(weights.fulltext * 100)} / M ${Math.round(weights.metadata * 100)}`;
}

function formatError(error: string) {
  if (error.includes("Compare failed: 400")) {
    return "The query was rejected by the custom route.";
  }
  if (error.includes("Sample ingest failed") || error.includes("Compare failed")) {
    return "Search failed. Check SeekDB and embedding credentials, then run it again.";
  }
  return error;
}

function formatImageId(imageId: string | undefined) {
  if (!imageId) return "";
  return imageId.split("_").join(" ");
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

export default function SampleLab() {
  const [pack, setPack] = useState<SamplePack | null>(null);
  const [selectedCase, setSelectedCase] = useState<SampleCase | null>(null);
  const [compareData, setCompareData] = useState<any>(null);
  const [status, setStatus] = useState("Sample pack ready for inspection.");
  const [error, setError] = useState("");
  const imageCount = pack?.manifest?.images?.length ?? 0;

  useEffect(() => {
    getSamplePack()
      .then((data) => {
        setPack(data);
        setSelectedCase(data.cases[0]);
      })
      .catch((err) => setError(String(err)));
  }, []);

  async function onIngestSamplePack() {
    setError("");
    setStatus("Indexing starter pack");
    try {
      const result = await ingestSamplePack();
      setStatus(`Indexed ${result.indexed} starter images.`);
      if (selectedCase) {
        await onRunCase(selectedCase);
      }
    } catch (err) {
      setError(String(err));
      setStatus("Starter pack ingest failed.");
    }
  }

  async function onRunCase(caseItem = selectedCase) {
    if (!caseItem) return;
    setError("");
    setSelectedCase(caseItem);
    setStatus(`Running ${caseItem.recommended_mode} case`);
    try {
      setCompareData(await compareHybridModes(caseItem.query, 4));
      setStatus(caseItem.expected_effect);
    } catch (err) {
      setError(String(err));
      setStatus("Comparison failed.");
    }
  }

  return (
    <section className="sample-lab">
      <header className="workspace-panel workspace-panel--lab">
        <div>
          <p className="section-kicker">Guided lab</p>
          <h2>Run the same image pack through four retrieval modes.</h2>
          <p>
            Each case is tuned to make one signal win. The ranking lanes show why
            hybrid search is useful when words, pixels, and labels disagree.
          </p>
        </div>
        <div className="sample-lab__actions">
          <button onClick={onIngestSamplePack}>Index starter pack</button>
          <a href={samplePackDownloadUrl()}>Download pack</a>
        </div>
      </header>

      <div className="lab-status">
        <span>{status}</span>
        <strong>{pack?.cases?.length ?? 0} cases</strong>
        <strong>{imageCount} images</strong>
      </div>
      {error && (
        <div className="error-panel" role="alert">
          <strong>{formatError(error)}</strong>
          <span>{error}</span>
        </div>
      )}

      <div className="sample-lab__layout">
        <aside className="case-list">
          {(pack?.cases ?? []).map((caseItem: any) => (
            <button
              className={selectedCase?.id === caseItem.id ? "active" : ""}
              key={caseItem.id}
              onClick={() => onRunCase(caseItem)}
            >
              <strong>{caseItem.recommended_mode}</strong>
              <span>{caseItem.query}</span>
            </button>
          ))}
        </aside>

        <div className="case-result">
          {selectedCase && (
            <div className="case-brief">
              <span className="mode-pill">{modeLabels[selectedCase.recommended_mode] ?? selectedCase.recommended_mode}</span>
              <h3>{selectedCase.query}</h3>
              <p>{selectedCase.what_to_notice}</p>
            </div>
          )}

          <div className="mode-board">
            {modes.map((mode) => {
              const trace = compareData?.[mode];
              const topHit = trace?.hits?.[0];
              const expectedWinner = selectedCase?.expected_top_by_mode?.[mode];
              return (
                <article className={mode === selectedCase?.recommended_mode ? "mode-card recommended" : "mode-card"} key={mode}>
                  <header>
                    <span>{modeLabels[mode]}</span>
                    <strong>{mode}</strong>
                  </header>
                  {expectedWinner && (
                    <div className="expected-winner">
                      <span>Expected top</span>
                      <strong>{formatImageId(expectedWinner)}</strong>
                    </div>
                  )}
                  <div className="weight-rail">
                    <span className={`weight-rail__bar weight-rail__bar--${mode}`} />
                  </div>
                  <small>{trace?.weights ? formatWeights(trace.weights) : "Waiting for a search run"}</small>
                  {topHit ? (
                    <div className="top-hit">
                      <img src={resolveCustomUrl(topHit.image_url)} alt="" />
                      <div>
                        <strong>{topHit.file_name}</strong>
                        <p>{topHit.caption}</p>
                        <EvidenceTerms terms={topHit.matched_terms} />
                      </div>
                    </div>
                  ) : (
                    <p className="empty-lane">Index the sample pack, then select a case.</p>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
