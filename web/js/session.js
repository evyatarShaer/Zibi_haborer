// sessionStorage as JSON, never throwing (private mode, blocked storage).
export function load(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key));
  } catch (e) {
    return null;
  }
}

export function save(key, value) {
  try {
    if (value === null) sessionStorage.removeItem(key);
    else sessionStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    // storage unavailable: drafts and the story flag are conveniences only
  }
}
