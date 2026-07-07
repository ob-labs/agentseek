import { useEffect, useState } from "react";
import { compareHybridModes, getSamplePack, ingestSamplePack, resolveCustomUrl, samplePackDownloadUrl } from "./api";

const modes = ["semantic", "keyword", "exact", "balanced"];

export default function SampleLab() {
  const [pack, setPack] = useState<any>(null);
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [compareData, setCompareData] = useState<any>(null);
  const [status, setStatus] = useState("Load the starter pack, then run a guided case.");
  const [error, setError] = useState("");

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
      <header className="sample-lab__header">
        <div>
          <p className="eyebrow">Guided lab</p>
          <h1>See hybrid search change the ranking</h1>
        </div>
        <div className="sample-lab__actions">
          <button onClick={onIngestSamplePack}>Index starter pack</button>
          <a href={samplePackDownloadUrl()}>Download pack</a>
        </div>
      </header>

      {error && <p className="error">{error}</p>}
      <p className="status">{status}</p>

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

        <main className="case-result">
          {selectedCase && (
            <div className="case-brief">
              <h2>{selectedCase.query}</h2>
              <p>{selectedCase.what_to_notice}</p>
              <button onClick={() => onRunCase()}>Run this case</button>
            </div>
          )}

          {compareData && (
            <div className="mode-board">
              {modes.map((mode) => {
                const trace = compareData[mode];
                const topHit = trace?.hits?.[0];
                return (
                  <article className={mode === selectedCase?.recommended_mode ? "mode-card recommended" : "mode-card"} key={mode}>
                    <header>
                      <strong>{mode}</strong>
                      <span>V {Math.round(trace.weights.vector * 100)} / S {Math.round(trace.weights.sparse * 100)} / F {Math.round(trace.weights.fulltext * 100)}</span>
                    </header>
                    {topHit && (
                      <div className="top-hit">
                        <img src={resolveCustomUrl(topHit.image_url)} alt="" />
                        <div>
                          <strong>{topHit.file_name}</strong>
                          <p>{topHit.caption}</p>
                        </div>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </main>
      </div>
    </section>
  );
}
