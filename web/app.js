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
