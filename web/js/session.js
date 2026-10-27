// localStorage as JSON, never throwing (private mode, blocked storage): what this device
// has already seen is a convenience only (without it, a verdict is replayed again).
export function recall(key, fallback) {
  try {
    const v = JSON.parse(localStorage.getItem(key));
    return v === null ? fallback : v;
  } catch (e) {
    return fallback;
  }
}

export function remember(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    // storage unavailable
  }
}
