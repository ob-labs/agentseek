import { ChangeEvent, FormEvent, useState } from "react";
import { compareHybridModes, resolveCustomUrl, uploadArchive } from "./api";

const modes = ["semantic", "keyword", "exact", "balanced"];

export default function HybridCompare() {
  const [query, setQuery] = useState("similar shoes with visible blue logo");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      setData(await compareHybridModes(query, 5));
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
      <div className="compare__toolbar">
        <form className="compare__form" onSubmit={onSubmit}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
          <button type="submit">Compare</button>
        </form>
        <label className="upload-control">
          Upload archive
          <input type="file" accept=".zip,.tar,.gz,.bz2,.xz" onChange={onUpload} />
        </label>
      </div>
      {uploadStatus && <p className="status">{uploadStatus}</p>}
      {error && <p className="error">{error}</p>}
      {data && (
        <div className="compare__grid">
          {modes.map((mode) => {
            const trace = data[mode];
            return (
              <article className="mode" key={mode}>
                <header>
                  <strong>{mode}</strong>
                  <span>
                    V {Math.round(trace.weights.vector * 100)} / S {Math.round(trace.weights.sparse * 100)} / F {Math.round(trace.weights.fulltext * 100)}
                  </span>
                </header>
                {(trace.hits ?? []).map((hit: any) => (
                  <div className="result" key={hit.image_id}>
                    <img src={resolveCustomUrl(hit.image_url)} alt="" />
                    <div>
                      <strong>{hit.file_name}</strong>
                      <p>{hit.caption}</p>
                      <small>fused {hit.fused_score?.toFixed?.(3) ?? "n/a"}</small>
                    </div>
                  </div>
                ))}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
