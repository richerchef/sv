// Minimal URL state: read and write scene/year in query params
function applyUrlState() {
	const params = new URLSearchParams(window.location.search);
	const s = params.get('scene');
	const y = params.get('year');
	if (s && typeof window.currentScene !== 'undefined') {
		currentScene = s;
	}
	if (y && Array.isArray(window.years)) {
		const idx = window.years.indexOf(y);
		if (idx >= 0) currentYearIndex = idx;
	}
}

function pushUrlState() {
	const params = new URLSearchParams(window.location.search);
	params.set('scene', currentScene);
	params.set('year', years[currentYearIndex]);
	// include camera state if available
	try {
		if (viewer) {
			const yaw = typeof viewer.getYaw === 'function' ? viewer.getYaw() : null;
			const pitch = typeof viewer.getPitch === 'function' ? viewer.getPitch() : null;
			const hfov = typeof viewer.getHfov === 'function' ? viewer.getHfov() : null;
			if (yaw !== null) params.set('yaw', yaw.toFixed(3));
			if (pitch !== null) params.set('pitch', pitch.toFixed(3));
			if (hfov !== null) params.set('hfov', hfov.toFixed(3));
		}
	} catch (e) {}
	const newUrl = window.location.pathname + '?' + params.toString();
	window.history.replaceState({}, '', newUrl);
}

// When applying URL state, also capture camera params for initial view
function readCameraFromUrl() {
	const params = new URLSearchParams(window.location.search);
	const yaw = params.get('yaw');
	const pitch = params.get('pitch');
	const hfov = params.get('hfov');
	if (yaw || pitch || hfov) {
		window.initialView = {
			yaw: yaw ? Number(yaw) : 0,
			pitch: pitch ? Number(pitch) : 0,
			hfov: hfov ? Number(hfov) : 0
		};
	}
}

window.readCameraFromUrl = readCameraFromUrl;

window.applyUrlState = applyUrlState;
window.pushUrlState = pushUrlState;
