// viewer uses the global `hotspots` object loaded in `app.js`

/**
 * Initialise viewer and load hotspots data
 */
async function initViewer() {
  const sceneDef = getSceneDefinition(currentScene);
  const year = years[currentYearIndex];
  const image = typeof getImageFilename === 'function' ? getImageFilename(sceneDef, year) : (sceneDef.images ? sceneDef.images[year] : null);

  // create the pannellum viewer (or recreate if present)
  createViewerForImage(image, () => {
    renderHotspots();
    // if URL specified an initial view, apply it
    if (window.initialView) {
      const v = window.initialView;
      try { viewer.lookAt(v.pitch || 0, v.yaw || 0, v.hfov || 0); } catch (e) {}
      window.initialView = null;
    }
  });

  updateSceneTitle(sceneDef.name);
}

function createViewerForImage(image, onLoad) {
  const container = document.getElementById('viewer');
  // destroy existing viewer cleanly if possible
  try {
    if (viewer && typeof viewer.destroy === 'function') viewer.destroy();
  } catch (e) {}
  // clear container
  if (container) container.innerHTML = '';

  viewer = pannellum.viewer('viewer', {
    type: 'equirectangular',
    panorama: `images/${image}`,
    autoLoad: true,
    showControls: true
  });

  viewer.on('load', () => {
    // If a pending pan (from search click) exists, apply it first (smoothly)
    if (window.pendingPan) {
      try {
        animateLookAt(window.pendingPan.pitch || 0, window.pendingPan.yaw || 0, window.pendingPan.hfov || 0, 700);
      } catch (e) {}
      window.pendingPan = null;
    } else if (window.initialView) {
      try {
        animateLookAt(window.initialView.pitch || 0, window.initialView.yaw || 0, window.initialView.hfov || 0, 700);
      } catch (e) {}
      window.initialView = null;
    }

    if (onLoad && typeof onLoad === 'function') onLoad();

    // Update compass and date
    if (typeof updateCompassAndDate === 'function') updateCompassAndDate();
  });

  // Update compass on view change
  viewer.on('animatefinished', () => {
    if (typeof updateCompassAndDate === 'function') updateCompassAndDate();
    if (typeof pushUrlState === 'function') pushUrlState();
  });
}

/**
 * Smoothly animate camera from current view to target view.
 * Returns a Promise that resolves when animation completes.
 */
function animateLookAt(targetPitch, targetYaw, targetHfov, duration = 600) {
  if (!viewer) return Promise.resolve();
  const startYaw = typeof viewer.getYaw === 'function' ? viewer.getYaw() : 0;
  const startPitch = typeof viewer.getPitch === 'function' ? viewer.getPitch() : 0;
  const startHfov = typeof viewer.getHfov === 'function' ? viewer.getHfov() : 0;

  // Normalize angles to [-180,180) for shortest path
  function normalize(a) { return ((((a % 360) + 540) % 360) - 180); }
  const sYaw = normalize(startYaw);
  const tYaw = normalize(targetYaw || 0);
  let deltaYaw = tYaw - sYaw;
  // shortest path
  if (deltaYaw > 180) deltaYaw -= 360;
  if (deltaYaw < -180) deltaYaw += 360;

  const sPitch = startPitch;
  const tPitch = targetPitch || 0;
  const sHfov = startHfov || 0;
  const tHfov = (typeof targetHfov === 'number') ? targetHfov : sHfov;

  const start = performance.now();
  return new Promise(resolve => {
    function step(now) {
      const p = Math.min(1, (now - start) / duration);
      const ease = (p < 0.5) ? (2*p*p) : (1 - Math.pow(-2*p + 2, 2)/2);
      const curYaw = sYaw + deltaYaw * ease;
      const curPitch = sPitch + (tPitch - sPitch) * ease;
      const curHfov = sHfov + (tHfov - sHfov) * ease;
      try { viewer.lookAt(curPitch, curYaw, curHfov); } catch (e) {}
      if (p < 1) requestAnimationFrame(step); else resolve();
    }
    requestAnimationFrame(step);
  });
}

/**
 * Reload the panorama for the selected scene + year
 * while preserving camera orientation
 */
function loadScene(sceneId) {
  const sceneDef = getSceneDefinition(sceneId);
  if (!sceneDef) return;

  const year = years[currentYearIndex];
  const image = typeof getImageFilename === 'function' ? getImageFilename(sceneDef, year) : (sceneDef.images ? sceneDef.images[year] : null);
  // Preserve previous view
  let yaw = 0, pitch = 0, hfov = 0;
  try {
    if (viewer) {
      yaw = viewer.getYaw();
      pitch = viewer.getPitch();
      hfov = viewer.getHfov ? viewer.getHfov() : 0;
    }
  } catch (e) {}

  // Recreate viewer with the new image and restore orientation after load
  createViewerForImage(image, () => {
    try { viewer.lookAt(pitch, yaw, hfov || 0); } catch (e) {}
    renderHotspots();
  });

  currentScene = sceneId;
  updateSceneTitle(sceneDef.name);
  if (typeof window.pushUrlState === 'function') window.pushUrlState();
}

/**
 * Render hotspots for the current scene
 */
function renderHotspots() {
  if (!hotspots || !viewer || !scenes) return;

  // Remove existing hotspots
  const existing = (viewer.getConfig().hotSpots || []).slice();
  existing.forEach(h => {
    try { viewer.removeHotSpot(h.id); } catch (e) {}
  });

  // Prefer hotspots keyed by image filename (per-image hotspots). Resolve image name first.
  const sceneDef = getSceneDefinition(currentScene);
  const yearKey = years[currentYearIndex];
  const imageFilename = (typeof getImageFilename === 'function') ? getImageFilename(sceneDef, yearKey) : null;
  const imageBase = imageFilename ? imageFilename.split('/').pop() : null;
  let perImageHotspots = [];
  if (imageBase && hotspots[imageBase]) perImageHotspots = hotspots[imageBase];
  // also support keys like "sceneId|imageName"
  else if (imageBase && hotspots[`${currentScene}|${imageBase}`]) perImageHotspots = hotspots[`${currentScene}|${imageBase}`];

  const useHotspots = perImageHotspots.length ? perImageHotspots : (hotspots[currentScene] || []);

  // Filter by active types and by year if hotspot specifies years
  const allowedTypes = window.activeHotspotTypes || null; // set in hotspots.js
  const year = years[currentYearIndex];

  useHotspots.forEach(hs => {
    // hs may be minimal (id,yaw,pitch) — merge with hotspotMeta if available
    const meta = (typeof hotspotMeta !== 'undefined' && hotspotMeta && hotspotMeta[hs.id]) ? hotspotMeta[hs.id] : {};
    const merged = Object.assign({}, meta, hs);

    if (allowedTypes && allowedTypes.length && merged.type && !allowedTypes.includes(merged.type)) return;
    if (merged.years && Array.isArray(merged.years) && !merged.years.includes(year)) return;

    viewer.addHotSpot({
      id: merged.id,
      pitch: merged.pitch,
      yaw: merged.yaw,
      cssClass: `hotspot hotspot-${merged.type || 'default'}`,
      createTooltipFunc: hotspotTooltip,
      createTooltipArgs: merged,
      clickHandlerFunc: function(evt) {
        // Smoothly center the hotspot and show info panel
        animateLookAt(merged.pitch, merged.yaw, undefined, 700).then(() => {
          if (typeof pushUrlState === 'function') pushUrlState();
        });
        showHotspotInfo(merged);
      }
    });
  });

  // Add link hotspots from scenes definition
  if (sceneDef && sceneDef.links) {
    sceneDef.links.forEach((ln, idx) => {
      viewer.addHotSpot({
        id: `link-${currentScene}-${idx}`,
        pitch: ln.pitch,
        yaw: ln.yaw,
        cssClass: 'link-hotspot',
        createTooltipFunc: function(div) { div.innerHTML = `<small>${ln.label}</small>`; },
        clickHandlerFunc: function() {
          // navigate to linked scene and request the view to be the link's orientation
          window.pendingPan = { pitch: ln.pitch, yaw: ln.yaw };
          loadScene(ln.to);
        }
      });
    });
  }
}

/** Show hotspot details in the overlay */
function showHotspotInfo(hs) {
  const el = document.getElementById('hotspot-info');
  if (!el) return;
  el.innerHTML = `
    <div class="close">✕</div>
    <div class="title">${hs.label || 'Item'}</div>
    <div class="meta">${hs.type || ''}</div>
    <div class="desc">${hs.description || ''}</div>
  `;
  el.classList.remove('hidden'); el.classList.add('visible');
  const close = el.querySelector('.close');
  if (close) close.onclick = () => hideHotspotInfo();
}

function hideHotspotInfo() {
  const el = document.getElementById('hotspot-info');
  if (!el) return;
  el.classList.remove('visible'); el.classList.add('hidden');
}

/**
 * Hotspot tooltip renderer
 */
function hotspotTooltip(div, hs) {
  div.innerHTML = `
    <strong>${hs.label}</strong><br>
    <small>${hs.type}</small>
  `;
}

/**
 * Lookup helper
 */
function getSceneDefinition(sceneId) {
  return scenes.scenes.find(s => s.id === sceneId);
}

/**
 * Update scene title in UI
 */
function updateSceneTitle(name) {
  const el = document.getElementById("scene-title");
  if (el) el.textContent = name;
}


function onYearChanged(index) {
  currentYearIndex = index;

  // Reload current scene with new year image
  loadScene(currentScene);
  if (typeof window.pushUrlState === 'function') window.pushUrlState();
}

// Programmatic helper when changing year from other modules
window.onYearChanged = onYearChanged;