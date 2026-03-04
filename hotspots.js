// Hotspot controls, search

window.activeHotspotTypes = ['pump','valve'];

function initHotspotsUI() {
  // Filters
  const boxes = document.querySelectorAll('.filter');
  boxes.forEach(cb => {
    cb.addEventListener('change', () => {
      updateActiveFilters();
    });
  });

  // Search
  const search = document.getElementById('search');
  const results = document.getElementById('results');
  if (search) {
    search.addEventListener('input', e => {
      const q = e.target.value.trim().toLowerCase();
      renderSearchResults(q, results);
    });
  }
}

function updateActiveFilters() {
  const boxes = document.querySelectorAll('.filter');
  const active = [];
  boxes.forEach(cb => { if (cb.checked) active.push(cb.value); });
  window.activeHotspotTypes = active;
  if (typeof renderHotspots === 'function') renderHotspots();
}

function renderSearchResults(query, container) {
  if (!container) return;
  container.innerHTML = '';
  if (!query) return;

  const matches = [];
  Object.keys(hotspots || {}).forEach(key => {
    const list = hotspots[key] || [];
    // try to resolve sceneId: key may be image basename, or "scene|image", or scene id
    let sceneId = null;
    if (key.indexOf('|') !== -1) sceneId = key.split('|')[0];
    else {
      // try to find a scene that contains this image in its images
      if (scenes && Array.isArray(scenes.scenes)) {
        for (const s of scenes.scenes) {
          if (!s.images) continue;
          if (Array.isArray(s.images) && s.images.indexOf(key) !== -1) { sceneId = s.id; break; }
          if (typeof s.images === 'object') {
            const vals = Object.values(s.images || {});
            if (vals.indexOf(key) !== -1) { sceneId = s.id; break; }
          }
        }
      }
    }

    list.forEach(h => {
      const meta = (typeof hotspotMeta !== 'undefined' && hotspotMeta && hotspotMeta[h.id]) ? hotspotMeta[h.id] : {};
      const label = (meta.label || h.label || h.id || '').toLowerCase();
      if (label.indexOf(query) !== -1) matches.push({ sceneId: sceneId || key, h: Object.assign({}, meta, h) });
    });
  });

  matches.forEach(m => {
    const li = document.createElement('li');
    const sceneName = (m.sceneId && getSceneDefinition(m.sceneId)) ? getSceneDefinition(m.sceneId).name : m.sceneId;
    li.textContent = `${m.h.label || m.h.id} — ${sceneName}`;
    li.addEventListener('click', () => {
      // Request navigation to scene and then pan to hotspot once loaded
      window.pendingPan = { pitch: m.h.pitch, yaw: m.h.yaw };
      loadScene(m.sceneId);
    });
    container.appendChild(li);
  });
}

// Expose for other modules
window.initHotspotsUI = initHotspotsUI;
