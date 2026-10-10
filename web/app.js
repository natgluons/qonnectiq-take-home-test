const form = document.querySelector('#question-form');
const field = document.querySelector('#question');
const send = document.querySelector('#send');
const chat = document.querySelector('#chat');
const status = document.querySelector('#status');

function message(role, text, sources = []) {
  const bubble = document.createElement('div');
  bubble.className = `message ${role}`;
  // textContent is deliberate: model output is never trusted as HTML.
  bubble.textContent = text;
  if (sources.length) {
    const details = document.createElement('details');
    details.className = 'sources';
    const summary = document.createElement('summary');
    summary.textContent = `Evidence (${sources.length})`;
    details.append(summary);
    for (const source of sources) {
      const line = document.createElement('div');
      line.textContent = `${source.source_file} · page ${source.page} · ${source.section}${source.report_date ? ' · ' + source.report_date : ''}`;
      details.append(line);
    }
    bubble.append(details);
  }
  chat.append(bubble);
  bubble.scrollIntoView({behavior: 'smooth', block: 'end'});
  return bubble;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = field.value.trim();
  if (!question) return;
  field.value = '';
  send.disabled = true;
  message('user', question);
  const pending = message('assistant', 'Searching source documents…');
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question}),
    });
    const data = await response.json();
    pending.remove();
    message('assistant', response.ok ? data.answer : (data.detail || 'Request failed.'), response.ok ? data.sources : []);
  } catch {
    pending.remove();
    message('assistant', 'Unable to reach the server.');
  } finally {
    send.disabled = false;
    field.focus();
  }
});

fetch('/api/health').then(r => r.json()).then(data => {
