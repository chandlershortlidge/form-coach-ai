export function getSessionId() {
  let id = sessionStorage.getItem('session_id');
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem('session_id', id);
  }
  return id;
}

export function resetSessionId() {
  const id = crypto.randomUUID();
  sessionStorage.setItem('session_id', id);
  return id;
}
