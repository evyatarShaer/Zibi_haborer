// The local API (api/src/borer_api/app.py). Each call resolves to {status, data};
// a network error gives status 0.
async function call(method, path, body) {
  try {
    const r = await fetch(path, {
      method,
      headers: body ? { "content-type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    return { status: r.status, data: await r.json().catch(() => ({})) };
  } catch (e) {
    return { status: 0, data: {} };
  }
}

export const postHearing = (body) => call("POST", "/hearing", body);
export const getHearing = (id) => call("GET", `/hearing/${encodeURIComponent(id)}`);
