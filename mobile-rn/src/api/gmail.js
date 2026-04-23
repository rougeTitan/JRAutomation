const BASE = 'https://gmail.googleapis.com/gmail/v1/users/me';

async function gmailFetch(accessToken, path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Gmail API error ${res.status}`);
  }
  return res.json();
}

// ── Fetch recruiter/job emails ─────────────────────────────────────────────
export async function fetchJobEmails(accessToken, maxResults = 50) {
  const query = encodeURIComponent(
    'subject:job OR subject:opportunity OR subject:hiring OR subject:position OR subject:recruiter'
  );
  const data = await gmailFetch(
    accessToken,
    `/messages?maxResults=${maxResults}&q=${query}`
  );
  if (!data.messages?.length) return [];

  const emails = await Promise.all(
    data.messages.map(m => fetchEmailDetail(accessToken, m.id))
  );
  return emails.filter(Boolean);
}

// ── Fetch a single email with full body ────────────────────────────────────
export async function fetchEmailDetail(accessToken, messageId) {
  try {
    const msg = await gmailFetch(accessToken, `/messages/${messageId}?format=full`);
    return parseMessage(msg);
  } catch {
    return null;
  }
}

// ── Send a reply email ─────────────────────────────────────────────────────
export async function sendReply(accessToken, { to, subject, body, threadId }) {
  const raw = makeRaw({ to, subject, body, threadId });
  return gmailFetch(accessToken, '/messages/send', {
    method: 'POST',
    body: JSON.stringify({ raw, threadId }),
  });
}

// ── Delete an email ────────────────────────────────────────────────────────
export async function deleteEmail(accessToken, messageId) {
  await fetch(`${BASE}/messages/${messageId}/trash`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

// ── Internal helpers ───────────────────────────────────────────────────────
function parseMessage(msg) {
  const headers = msg.payload?.headers || [];
  const get = name => headers.find(h => h.name.toLowerCase() === name)?.value || '';

  return {
    id: msg.id,
    threadId: msg.threadId,
    subject: get('subject'),
    from: get('from'),
    to: get('to'),
    date: get('date'),
    snippet: msg.snippet || '',
    body: extractBody(msg.payload),
  };
}

function extractBody(payload) {
  if (!payload) return '';
  if (payload.body?.data) return decodeBase64(payload.body.data);
  if (payload.parts) {
    for (const part of payload.parts) {
      if (part.mimeType === 'text/plain' && part.body?.data)
        return decodeBase64(part.body.data);
    }
    for (const part of payload.parts) {
      const nested = extractBody(part);
      if (nested) return nested;
    }
  }
  return '';
}

function decodeBase64(data) {
  try {
    return decodeURIComponent(
      escape(atob(data.replace(/-/g, '+').replace(/_/g, '/')))
    );
  } catch {
    return '';
  }
}

function makeRaw({ to, subject, body, threadId }) {
  const msg = [
    `To: ${to}`,
    `Subject: ${subject}`,
    'Content-Type: text/plain; charset=utf-8',
    '',
    body,
  ].join('\r\n');
  return btoa(unescape(encodeURIComponent(msg)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}
