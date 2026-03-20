const BASE_URL = 'http://localhost:8000';

export async function analyze({ sessionId, userQuery, userVideo, userAudio }) {
  const form = new FormData();

  if (userQuery) form.append('user_query', userQuery);
  if (userVideo) form.append('user_video', userVideo);
  if (userAudio) form.append('user_audio', userAudio, 'recording.webm');

  const url = new URL(`${BASE_URL}/analyze`);
  url.searchParams.set('session_id', sessionId);

  const res = await fetch(url, {
    method: 'POST',
    body: form,
  });

  console.log('[api] response status:', res.status, 'ok:', res.ok);

  if (!res.ok) {
    const text = await res.text();
    console.error('[api] error body:', text);
    throw new Error(`Server error: ${res.status}`);
  }

  const data = await res.json();
  console.log('[api] parsed JSON:', data);
  return data;
}

export async function preview({ sessionId, userVideo }) {
  const form = new FormData();
  form.append('user_video', userVideo);

  const url = new URL(`${BASE_URL}/preview`);
  url.searchParams.set('session_id', sessionId);

  const res = await fetch(url, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) throw new Error(`Preview error: ${res.status}`);
  return res.json();
}
