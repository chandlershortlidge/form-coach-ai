const BASE_URL = 'https://fitness-form-coach-t32qh37koa-ew.a.run.app';

export async function fetchSessions(limit = 20) {
  const res = await fetch(`${BASE_URL}/sessions?limit=${limit}`);
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function fetchSession(sessionId) {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function analyze({ sessionId, userQuery, userVideo, userAudio, onStatus, onPreview, onResponse }) {
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

  if (!res.ok) {
    const text = await res.text();
    console.error('[api] error body:', text);
    throw new Error(`Server error: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n').filter(line => line.startsWith('data: '));

    for (const line of lines) {
      const data = JSON.parse(line.slice(6));

      if (data.type === 'status' && onStatus) {
        onStatus(data.message);
      }
      if (data.type === 'preview' && onPreview) {
        onPreview(data.classification_raw);
      }
      if (data.type === 'response' && onResponse) {
        onResponse(data.response, data.transcription);
      }
    }
  }
}
