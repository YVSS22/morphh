const drop = document.getElementById('drop');
const fileInput = document.getElementById('file');
const preview = document.getElementById('preview');
const dropInner = document.getElementById('dropInner');
const go = document.getElementById('go');
const out = document.getElementById('out');
const dl = document.getElementById('dl');
const loader = document.getElementById('loader');
const resultEmpty = document.getElementById('resultEmpty');
const error = document.getElementById('error');

let fileData = null;
let fileMime = '';
let resultUrl = null;

function readFile(f) {
  if (!f || !f.type.startsWith('image/')) return;
  const reader = new FileReader();
  reader.onload = () => {
    fileData = reader.result.split(',')[1];
    fileMime = f.type;
    preview.src = reader.result;
    preview.classList.remove('hidden');
    dropInner.classList.add('hidden');
    go.disabled = false;
  };
  reader.readAsDataURL(f);
}

drop.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => readFile(e.target.files[0]));

['dragover', 'dragenter'].forEach(ev => drop.addEventListener(ev, e => {
  e.preventDefault(); drop.classList.add('drag');
}));
['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => {
  e.preventDefault(); drop.classList.remove('drag');
}));
drop.addEventListener('drop', e => readFile(e.dataTransfer.files[0]));

go.addEventListener('click', async () => {
  if (!fileData) return;
  go.disabled = true;
  out.classList.add('hidden');
  dl.classList.add('hidden');
  error.classList.add('hidden');
  resultEmpty.classList.add('hidden');
  loader.classList.remove('hidden');

  try {
    const res = await fetch('/api/photoreal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: fileData, mime: fileMime }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ('Erreur ' + res.status));
    resultUrl = data.url;
    const url = data.url + '?t=' + Date.now();
    out.src = url;
    out.classList.remove('hidden');
    dl.classList.remove('hidden');
  } catch (e) {
    error.textContent = 'Erreur : ' + e.message;
    error.classList.remove('hidden');
    resultEmpty.classList.remove('hidden');
  } finally {
    loader.classList.add('hidden');
    go.disabled = false;
  }
});

// Enregistrer : partage natif (Photos) sur mobile, téléchargement sinon
if (navigator.canShare && navigator.canShare({ files: [new File([''], 'x', { type: 'image/jpeg' })] })) {
  dl.textContent = 'Enregistrer dans Photos';
}
dl.addEventListener('click', async () => {
  if (!resultUrl) return;
  try {
    const blob = await (await fetch(resultUrl)).blob();
    const file = new File([blob], 'morphh.jpg', { type: 'image/jpeg' });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file] });
    } else {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'morphh.jpg';
      a.click();
    }
  } catch (e) {
    // partage annulé par l'utilisateur : on ignore
  }
});
