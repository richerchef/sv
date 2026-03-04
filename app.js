let viewer;
let scenes;
let hotspots;
let hotspotMeta;

let currentScene = "engine_room";
// `years` contains the list of image keys (e.g. dates like 12_05_2022 or 2022)
let years = [];
let currentYearIndex = 0;

async function init() {
  scenes = await fetch("data/scenes.json").then(r => r.json());
  hotspots = await fetch("data/hotspots.json").then(r => r.json());
  // optional metadata for hotspots (id -> { label, type, description })
  try { hotspotMeta = await fetch('data/hotspot_meta.json').then(r=>r.json()); } catch (e) { hotspotMeta = {}; }

  // Build global list of image keys (dates) collected from scenes.
  buildImageKeyIndex();

  // Apply URL state (if any) before initialising viewer
  if (typeof applyUrlState === 'function') applyUrlState();
  if (typeof readCameraFromUrl === 'function') readCameraFromUrl();

  initViewer();
  initUI();
  // Init hotspot UI (filters, search)
  if (typeof initHotspotsUI === 'function') initHotspotsUI();
}

function initUI() {
  // Sidebar toggle
  const toggle = document.getElementById('sidebar-toggle');
  const controls = document.getElementById('controls');
  toggle.addEventListener('click', () => {
    controls.classList.toggle('collapsed');
    toggle.textContent = controls.classList.contains('collapsed') ? '☰' : '✕';
  });

  // See more dates button
  const seeMoreBtn = document.getElementById('see-more-dates');
  seeMoreBtn.addEventListener('click', () => {
    showDateSelector();
  });

  // Select scene button
  const selectSceneBtn = document.getElementById('select-scene');
  selectSceneBtn.addEventListener('click', () => {
    showSceneSelector();
  });

  // Update compass and date on viewer load and change
  updateCompassAndDate();
}

window.onload = init;

/**
 * Build a unified list of image keys (date tokens) from all scenes.
 * Supports scenes that declare `images` as an object (key -> filename)
 * or as an array of filenames. The extracted keys become the `years` used by the UI.
 */
function buildImageKeyIndex() {
  const keys = new Set();
  if (!scenes || !Array.isArray(scenes.scenes)) return;
  scenes.scenes.forEach(s => {
    if (!s.images) return;
    if (Array.isArray(s.images)) {
      s.images.forEach(fn => {
        const k = extractKeyFromFilename(s.id, fn);
        if (k) keys.add(k);
      });
    } else if (typeof s.images === 'object') {
      // assume mapping key -> filename
      Object.keys(s.images).forEach(k => keys.add(k));
    }
  });

  // Convert to array and sort by date-like pattern (dd_mm_yyyy or yyyy)
  const arr = Array.from(keys);
  arr.sort((a,b) => {
    // try dd_mm_yyyy
    const da = parseDateKey(a);
    const db = parseDateKey(b);
    if (da && db) return da - db;
    if (da && !db) return -1;
    if (!da && db) return 1;
    return a.localeCompare(b);
  });
  years = arr;
}

function extractKeyFromFilename(sceneId, filename) {
  if (!filename) return null;
  // strip path
  const base = filename.split('/').pop();
  // try to match sceneId_...suffix
  const re = new RegExp('^' + sceneId + '_(.+)\\.[a-zA-Z0-9]+$');
  const m = base.match(re);
  if (m && m[1]) return m[1].replace(/[^0-9_\-]/g,'');
  // fallback: try to pull a date-like token
  const m2 = base.match(/(\d{4}|\d{2}_\d{2}_\d{4})/);
  return m2 ? m2[0] : null;
}

function parseDateKey(k) {
  if (!k) return null;
  // dd_mm_yyyy
  const m = k.match(/^(\d{2})_(\d{2})_(\d{4})$/);
  if (m) return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1])).getTime();
  // yyyy
  const m2 = k.match(/^(\d{4})$/);
  if (m2) return new Date(Number(m2[1]),0,1).getTime();
  return null;
}

/** Get the filename for a scene and a selected image key */
function getImageFilename(sceneDef, key) {
  if (!sceneDef) return null;
  if (!key) {
    // fallback: if object mapping, pick first; if array, first
    if (Array.isArray(sceneDef.images)) return sceneDef.images[0];
    if (sceneDef.images && typeof sceneDef.images === 'object') {
      const k = Object.keys(sceneDef.images)[0];
      return sceneDef.images[k];
    }
    return null;
  }

  if (Array.isArray(sceneDef.images)) {
    // find file containing _key
    const found = sceneDef.images.find(fn => fn.indexOf('_' + key) !== -1);
    if (found) return found;
    // try any file that contains sceneId
    if (sceneDef.images.length) return sceneDef.images[0];
    return null;
  }

  if (sceneDef.images && typeof sceneDef.images === 'object') {
    if (sceneDef.images[key]) return sceneDef.images[key];
    // maybe values already contain date tokens, try to find value that includes key
    const vals = Object.values(sceneDef.images);
    const found = vals.find(v => v.indexOf('_' + key) !== -1);
    if (found) return found;
    // fallback to first value
    return vals[0];
  }
  return null;
}
// Show date selector modal for current scene
function showDateSelector() {
  const sceneDef = getSceneDefinition(currentScene);
  if (!sceneDef || !sceneDef.images) return;

  const dates = Object.keys(sceneDef.images);
  if (dates.length <= 1) return; // No need if only one date

  // Create modal
  const modal = document.createElement('div');
  modal.style.position = 'fixed';
  modal.style.top = '0';
  modal.style.left = '0';
  modal.style.width = '100%';
  modal.style.height = '100%';
  modal.style.background = 'rgba(0,0,0,0.5)';
  modal.style.display = 'flex';
  modal.style.alignItems = 'center';
  modal.style.justifyContent = 'center';
  modal.style.zIndex = '1000';

  const content = document.createElement('div');
  content.style.background = '#fff';
  content.style.padding = '20px';
  content.style.borderRadius = '8px';
  content.style.maxWidth = '400px';
  content.style.width = '90%';

  const title = document.createElement('h3');
  title.textContent = `Select Date for ${sceneDef.name}`;
  content.appendChild(title);

  const list = document.createElement('ul');
  list.style.listStyle = 'none';
  list.style.padding = '0';
  list.style.maxHeight = '300px';
  list.style.overflowY = 'auto';

  dates.forEach(date => {
    const li = document.createElement('li');
    li.style.padding = '10px';
    li.style.cursor = 'pointer';
    li.style.borderBottom = '1px solid #eee';
    li.style.display = 'flex';
    li.style.alignItems = 'center';
    li.style.gap = '10px';

    // Image preview
    const img = document.createElement('img');
    img.src = `images/${sceneDef.images[date]}`;
    img.style.width = '60px';
    img.style.height = '40px';
    img.style.objectFit = 'cover';
    img.style.borderRadius = '4px';
    li.appendChild(img);

    // Date text
    const text = document.createElement('span');
    text.textContent = formatDate(date);
    li.appendChild(text);

    if (date === years[currentYearIndex]) {
      li.style.background = '#e3f2fd';
      li.style.fontWeight = 'bold';
    }
    li.addEventListener('click', () => {
      const idx = years.indexOf(date);
      if (idx >= 0) {
        currentYearIndex = idx;
        loadScene(currentScene);
        if (typeof pushUrlState === 'function') pushUrlState();
      }
      document.body.removeChild(modal);
    });
    list.appendChild(li);
  });

  content.appendChild(list);

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.style.marginTop = '10px';
  closeBtn.style.padding = '8px 16px';
  closeBtn.addEventListener('click', () => document.body.removeChild(modal));
  content.appendChild(closeBtn);

  modal.appendChild(content);
  document.body.appendChild(modal);
}

// Format date key to readable format
function formatDate(dateKey) {
  const m = dateKey.match(/^(\d{2})_(\d{2})_(\d{4})$/);
  if (m) {
    return `${m[1]}/${m[2]}/${m[4]}`;
  }
  return dateKey;
}

// Show scene selector modal with image previews
function showSceneSelector() {
  if (!scenes || !scenes.scenes) return;

  // Create modal
  const modal = document.createElement('div');
  modal.style.position = 'fixed';
  modal.style.top = '0';
  modal.style.left = '0';
  modal.style.width = '100%';
  modal.style.height = '100%';
  modal.style.background = 'rgba(0,0,0,0.5)';
  modal.style.display = 'flex';
  modal.style.alignItems = 'center';
  modal.style.justifyContent = 'center';
  modal.style.zIndex = '1000';

  const content = document.createElement('div');
  content.style.background = '#fff';
  content.style.padding = '20px';
  content.style.borderRadius = '8px';
  content.style.maxWidth = '500px';
  content.style.width = '90%';

  const title = document.createElement('h3');
  title.textContent = 'Select Scene';
  content.appendChild(title);

  const list = document.createElement('ul');
  list.style.listStyle = 'none';
  list.style.padding = '0';
  list.style.maxHeight = '400px';
  list.style.overflowY = 'auto';

  scenes.scenes.forEach(scene => {
    const li = document.createElement('li');
    li.style.padding = '10px';
    li.style.cursor = 'pointer';
    li.style.borderBottom = '1px solid #eee';
    li.style.display = 'flex';
    li.style.alignItems = 'center';
    li.style.gap = '10px';

    // Image preview - use first image
    let previewSrc = '';
    if (scene.images) {
      if (Array.isArray(scene.images)) {
        previewSrc = scene.images[0];
      } else if (typeof scene.images === 'object') {
        const keys = Object.keys(scene.images);
        if (keys.length > 0) {
          previewSrc = scene.images[keys[0]];
        }
      }
    }
    if (previewSrc) {
      const img = document.createElement('img');
      img.src = `images/${previewSrc}`;
      img.style.width = '80px';
      img.style.height = '50px';
      img.style.objectFit = 'cover';
      img.style.borderRadius = '4px';
      li.appendChild(img);
    }

    // Scene name
    const text = document.createElement('span');
    text.textContent = scene.name;
    li.appendChild(text);

    if (scene.id === currentScene) {
      li.style.background = '#e3f2fd';
      li.style.fontWeight = 'bold';
    }
    li.addEventListener('click', () => {
      loadScene(scene.id);
      if (typeof pushUrlState === 'function') pushUrlState();
      document.body.removeChild(modal);
    });
    list.appendChild(li);
  });

  content.appendChild(list);

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.style.marginTop = '10px';
  closeBtn.style.padding = '8px 16px';
  closeBtn.addEventListener('click', () => document.body.removeChild(modal));
  content.appendChild(closeBtn);

  modal.appendChild(content);
  document.body.appendChild(modal);
}

// Update compass and capture date display
function updateCompassAndDate() {
  const compassNeedle = document.getElementById('compass-needle');
  const dateEl = document.getElementById('capture-date');

  if (compassNeedle && viewer) {
    const yaw = viewer.getYaw ? viewer.getYaw() : 0;
    compassNeedle.style.transform = `rotate(${yaw}deg)`;
  }

  if (dateEl) {
    const sceneDef = getSceneDefinition(currentScene);
    const sceneName = sceneDef ? sceneDef.name : currentScene;
    const currentDate = years[currentYearIndex];
    dateEl.textContent = `${sceneName} - ${formatDate(currentDate)}`;
  }
}