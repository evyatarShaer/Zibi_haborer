// The case API (api/src/borer_api/routes.py). Each call resolves to {status, data};
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

const enc = encodeURIComponent;
export const openCase = (body) => call("POST", "/api/case", body);
export const getMine = (side, token) => call("GET", `/api/${side}/${enc(token)}`);
export const openB = (token) => call("POST", `/api/b/${enc(token)}/open`);
export const submitB = (token, text) => call("POST", `/api/b/${enc(token)}/submit`, { text_b: text });
export const postAppeal = (side, token) => call("POST", `/api/${side}/${enc(token)}/appeal`);
export const getBrain = (side, token, n) => call("GET", `/api/${side}/${enc(token)}/brain/${n}`);
export const getPublic = (id) => call("GET", `/api/c/${enc(id)}`);
export const postReport = (id) => call("POST", `/api/c/${enc(id)}/report`);
