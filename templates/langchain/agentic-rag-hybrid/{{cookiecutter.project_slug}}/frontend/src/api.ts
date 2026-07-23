function defaultCustomRoutesUrl(): string {
  const host = window.location.hostname || "127.0.0.1";
  return `http://${host}:2024`;
}

const customRoutesUrl = import.meta.env.VITE_CUSTOM_ROUTES_URL ?? defaultCustomRoutesUrl();

export async function compareHybridModes(query: string, topK = 5) {
  const url = new URL("/custom/compare", customRoutesUrl);
  url.searchParams.set("query", query);
  url.searchParams.set("top_k", String(topK));
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Compare failed: ${response.status}`);
  return response.json();
}

export async function getSamplePack() {
  const response = await fetch(`${customRoutesUrl}/custom/sample-pack`);
  if (!response.ok) throw new Error(`Sample pack failed: ${response.status}`);
  return response.json();
}

export async function ingestSamplePack() {
  const response = await fetch(`${customRoutesUrl}/custom/sample-pack/ingest`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Sample ingest failed: ${response.status}`);
  return response.json();
}

export function samplePackDownloadUrl() {
  return `${customRoutesUrl}/custom/sample-pack/download`;
}

export function resolveCustomUrl(path: string) {
  return new URL(path, customRoutesUrl).toString();
}

export async function uploadArchive(file: File) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${customRoutesUrl}/custom/upload-archive`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
  return response.json();
}
