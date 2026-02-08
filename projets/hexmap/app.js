// ═══════════════════════════════════════════════════════════════
//  HexMap Viewer — app.js
//  Deux couches indépendantes : Map (PDF) et Grille hexagonale
//  Chaque couche a son propre zoom, pan, rotation
// ═══════════════════════════════════════════════════════════════

pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// ─── Constants ───
const MIN_ZOOM = 0.05;
const MAX_ZOOM = 10;
const ZOOM_FACTOR = 0.1;
const SMOOTH_LERP = 0.12;
const GRID_COLS = 80;
const GRID_ROWS = 60;

// ─── Layer state ───
const layers = {
    map: {
        container: null,
        targetZoom: 1,
        smoothing: false,
        zoomPivotX: 0,
        zoomPivotY: 0
    },
    grid: {
        container: null,
        targetZoom: 1,
        smoothing: false,
        zoomPivotX: 0,
        zoomPivotY: 0
    }
};

let activeKey = 'map';
let smoothEnabled = false;
let gridVisible = false;
let hexSize = 40;
let gridGraphics = null;
let scene = null;

// Pan state (DOM-driven)
let isPanning = false;
let panContainer = null;
const panStart = { mx: 0, my: 0, cx: 0, cy: 0 };

// ─── Phaser ───
const config = {
    type: Phaser.AUTO,
    parent: 'game-container',
    backgroundColor: '#3c3c3c',
    scale: {
        mode: Phaser.Scale.RESIZE,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    scene: { create, update },
    input: { mouse: { preventDefaultWheel: false } }
};

const game = new Phaser.Game(config);

// ═══════════════════════════════════════════════════════════════
//  Phaser Scene
// ═══════════════════════════════════════════════════════════════

function create() {
    scene = this;

    // Containers — grid renders on top of map
    layers.map.container = this.add.container(0, 0);
    layers.grid.container = this.add.container(0, 0);

    // Hex grid graphics (inside grid container)
    gridGraphics = this.add.graphics();
    layers.grid.container.add(gridGraphics);
    drawHexGrid();

    // Grille masquée au démarrage
    layers.grid.container.setVisible(false);

    // ─── DOM-based input (reliable right-click + wheel) ───
    setupDOMInput();

    // Load default map
    loadPDF('Map.pdf');
}

function update() {
    // Smooth zoom animation
    for (const key of ['map', 'grid']) {
        const L = layers[key];
        if (!L.smoothing || !L.container) continue;

        const current = L.container.scaleX;
        const target = L.targetZoom;
        const diff = Math.abs(current - target);

        if (diff > 0.001) {
            const z = Phaser.Math.Linear(current, target, SMOOTH_LERP);
            zoomContainerAt(L.container, z, L.zoomPivotX, L.zoomPivotY);
        } else {
            zoomContainerAt(L.container, target, L.zoomPivotX, L.zoomPivotY);
            L.smoothing = false;
        }
    }
    updateStatusBar();
}

// ═══════════════════════════════════════════════════════════════
//  DOM Input — right-click pan + wheel zoom
//  (bypasses Phaser input which is unreliable for right-click)
// ═══════════════════════════════════════════════════════════════

function setupDOMInput() {
    const el = document.getElementById('game-container');

    // Block context menu
    el.addEventListener('contextmenu', (e) => e.preventDefault());

    // Right-click pan
    el.addEventListener('mousedown', (e) => {
        if (e.button === 2) {
            e.preventDefault();
            isPanning = true;
            panContainer = layers[activeKey].container;
            panStart.mx = e.clientX;
            panStart.my = e.clientY;
            panStart.cx = panContainer.x;
            panStart.cy = panContainer.y;
        }
    });

    window.addEventListener('mousemove', (e) => {
        if (isPanning && panContainer) {
            panContainer.x = panStart.cx + (e.clientX - panStart.mx);
            panContainer.y = panStart.cy + (e.clientY - panStart.my);
        }
    });

    window.addEventListener('mouseup', (e) => {
        if (e.button === 2) {
            isPanning = false;
            panContainer = null;
        }
    });

    // Wheel zoom
    el.addEventListener('wheel', (e) => {
        e.preventDefault();
        const rect = el.querySelector('canvas').getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;

        const L = layers[activeKey];
        const c = L.container;
        const oldZoom = c.scaleX;
        let newZoom;

        if (e.deltaY < 0) {
            newZoom = Math.min(MAX_ZOOM, oldZoom + ZOOM_FACTOR * oldZoom);
        } else {
            newZoom = Math.max(MIN_ZOOM, oldZoom - ZOOM_FACTOR * oldZoom);
        }

        if (smoothEnabled) {
            L.targetZoom = newZoom;
            L.zoomPivotX = px;
            L.zoomPivotY = py;
            L.smoothing = true;
        } else {
            zoomContainerAt(c, newZoom, px, py);
        }

        updateStatusBar();
    }, { passive: false });
}

// ═══════════════════════════════════════════════════════════════
//  Transform helpers
// ═══════════════════════════════════════════════════════════════

/** Zoom a container towards a screen-space pivot point */
function zoomContainerAt(container, newScale, pivotX, pivotY) {
    const oldScale = container.scaleX;
    const rot = container.rotation;
    const cosR = Math.cos(-rot);
    const sinR = Math.sin(-rot);

    const dx = pivotX - container.x;
    const dy = pivotY - container.y;
    const lx = (dx * cosR - dy * sinR) / oldScale;
    const ly = (dx * sinR + dy * cosR) / oldScale;

    container.setScale(newScale);

    const cosR2 = Math.cos(rot);
    const sinR2 = Math.sin(rot);
    const sx = lx * newScale;
    const sy = ly * newScale;
    const dx2 = sx * cosR2 - sy * sinR2;
    const dy2 = sx * sinR2 + sy * cosR2;

    container.x = pivotX - dx2;
    container.y = pivotY - dy2;
}

/** Rotate a container by angleDelta around a screen-space pivot */
function rotateContainerAt(container, angleDelta, pivotX, pivotY) {
    const scale = container.scaleX;
    const rot = container.rotation;
    const cosR = Math.cos(-rot);
    const sinR = Math.sin(-rot);

    const dx = pivotX - container.x;
    const dy = pivotY - container.y;
    const lx = (dx * cosR - dy * sinR) / scale;
    const ly = (dx * sinR + dy * cosR) / scale;

    container.rotation += angleDelta;

    const newRot = container.rotation;
    const cosR2 = Math.cos(newRot);
    const sinR2 = Math.sin(newRot);
    const sx = lx * scale;
    const sy = ly * scale;
    const dx2 = sx * cosR2 - sy * sinR2;
    const dy2 = sx * sinR2 + sy * cosR2;

    container.x = pivotX - dx2;
    container.y = pivotY - dy2;
}

// ═══════════════════════════════════════════════════════════════
//  Hex Grid
// ═══════════════════════════════════════════════════════════════

function drawHexGrid() {
    if (!gridGraphics) return;
    gridGraphics.clear();
    gridGraphics.lineStyle(1, 0x00ffff, 0.6);

    for (let col = 0; col < GRID_COLS; col++) {
        for (let row = 0; row < GRID_ROWS; row++) {
            let cx = col * 1.5 * hexSize;
            let cy = row * Math.sqrt(3) * hexSize;
            if (col % 2 === 1) cy += (Math.sqrt(3) / 2) * hexSize;
            drawHex(gridGraphics, cx, cy, hexSize);
        }
    }
}

function drawHex(gfx, cx, cy, size) {
    gfx.beginPath();
    for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 180) * (60 * i);
        const x = cx + size * Math.cos(angle);
        const y = cy + size * Math.sin(angle);
        if (i === 0) gfx.moveTo(x, y);
        else gfx.lineTo(x, y);
    }
    gfx.closePath();
    gfx.strokePath();
}

// ═══════════════════════════════════════════════════════════════
//  PDF Loading
// ═══════════════════════════════════════════════════════════════

async function loadPDF(url) {
    setStatus('Chargement du PDF...');
    try {
        const pdf = await pdfjsLib.getDocument(url).promise;
        await renderPDFPages(pdf);
        fitLayerToWindow('map');
        setStatus('Prêt');
    } catch (err) {
        console.error('Erreur chargement PDF:', err);
        setStatus('Erreur : impossible de charger le PDF');
    }
}

async function loadPDFFromFile(file) {
    const data = new Uint8Array(await file.arrayBuffer());
    setStatus('Chargement du PDF...');
    try {
        const pdf = await pdfjsLib.getDocument({ data }).promise;
        layers.map.container.removeAll(true);
        await renderPDFPages(pdf);
        fitLayerToWindow('map');
        setStatus('Prêt');
    } catch (err) {
        console.error('Erreur chargement PDF:', err);
        setStatus('Erreur : impossible de charger le PDF');
    }
}

async function renderPDFPages(pdf) {
    const numPages = pdf.numPages;
    let yOffset = 0;

    for (let i = 1; i <= numPages; i++) {
        setStatus(`Rendu page ${i}/${numPages}...`);
        const page = await pdf.getPage(i);
        const scale = 2;
        const viewport = page.getViewport({ scale });

        const canvas = document.createElement('canvas');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const ctx = canvas.getContext('2d');
        await page.render({ canvasContext: ctx, viewport }).promise;

        const texKey = 'page_' + i + '_' + Date.now();
        scene.textures.addCanvas(texKey, canvas);

        const sprite = scene.add.image(viewport.width / 2, yOffset + viewport.height / 2, texKey);
        layers.map.container.add(sprite);

        yOffset += viewport.height + 10;
    }
}

// ═══════════════════════════════════════════════════════════════
//  Fit to window
// ═══════════════════════════════════════════════════════════════

function fitLayerToWindow(key) {
    const c = layers[key].container;
    if (!c || c.list.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    c.list.forEach((child) => {
        const hw = (child.displayWidth || 0) / 2;
        const hh = (child.displayHeight || 0) / 2;
        minX = Math.min(minX, child.x - hw);
        minY = Math.min(minY, child.y - hh);
        maxX = Math.max(maxX, child.x + hw);
        maxY = Math.max(maxY, child.y + hh);
    });

    const contentW = maxX - minX;
    const contentH = maxY - minY;
    if (contentW <= 0 || contentH <= 0) return;

    const viewW = game.scale.width;
    const viewH = game.scale.height;
    const zoom = Math.min(viewW / contentW, viewH / contentH) * 0.95;

    c.setScale(zoom);
    c.rotation = 0;

    const centerLocalX = (minX + maxX) / 2;
    const centerLocalY = (minY + maxY) / 2;
    c.x = viewW / 2 - centerLocalX * zoom;
    c.y = viewH / 2 - centerLocalY * zoom;

    layers[key].targetZoom = zoom;
    layers[key].smoothing = false;
}

// ═══════════════════════════════════════════════════════════════
//  UI
// ═══════════════════════════════════════════════════════════════

function setStatus(text) {
    document.getElementById('status-text').textContent = text;
}

function updateStatusBar() {
    const c = layers[activeKey].container;
    const zoom = c ? Math.round(c.scaleX * 100) : 100;
    document.getElementById('zoom-level').textContent = zoom + '%';
    document.getElementById('active-layer').textContent =
        'Couche : ' + (activeKey === 'map' ? 'Map' : 'Grille');
}

// ─── Toggle active layer (segmented control) ───
const toggleMap = document.getElementById('toggle-map');
const toggleGrid = document.getElementById('toggle-grid');

function setActiveLayer(key) {
    activeKey = key;
    toggleMap.classList.toggle('active', key === 'map');
    toggleGrid.classList.toggle('active', key === 'grid');
    updateStatusBar();
}

toggleMap.addEventListener('click', () => setActiveLayer('map'));
toggleGrid.addEventListener('click', () => setActiveLayer('grid'));

// ─── Smooth toggle ───
const btnSmooth = document.getElementById('btn-smooth');
btnSmooth.addEventListener('click', () => {
    smoothEnabled = !smoothEnabled;
    btnSmooth.classList.toggle('toggle-on', smoothEnabled);
});

// ─── Rotate active layer ───
document.getElementById('btn-rotate').addEventListener('click', () => {
    const c = layers[activeKey].container;
    const cx = game.scale.width / 2;
    const cy = game.scale.height / 2;
    rotateContainerAt(c, Math.PI / 2, cx, cy);
});

// ─── Menu: Fichier ───
document.getElementById('menu-open').addEventListener('click', () => {
    document.getElementById('file-input').click();
});

document.getElementById('file-input').addEventListener('change', (e) => {
    if (e.target.files.length > 0) loadPDFFromFile(e.target.files[0]);
});

document.getElementById('menu-quit').addEventListener('click', () => {
    window.close();
});

// ─── Menu: Affichage ───
document.getElementById('menu-zoom-in').addEventListener('click', () => {
    const c = layers[activeKey].container;
    const cx = game.scale.width / 2;
    const cy = game.scale.height / 2;
    zoomContainerAt(c, c.scaleX * 1.2, cx, cy);
});

document.getElementById('menu-zoom-out').addEventListener('click', () => {
    const c = layers[activeKey].container;
    const cx = game.scale.width / 2;
    const cy = game.scale.height / 2;
    zoomContainerAt(c, c.scaleX / 1.2, cx, cy);
});

document.getElementById('menu-zoom-reset').addEventListener('click', () => {
    const c = layers[activeKey].container;
    const cx = game.scale.width / 2;
    const cy = game.scale.height / 2;
    zoomContainerAt(c, 1, cx, cy);
});

document.getElementById('menu-fit').addEventListener('click', () => {
    fitLayerToWindow(activeKey);
});

// ─── Menu: Grille ───
document.getElementById('menu-grid-toggle').addEventListener('click', () => {
    gridVisible = !gridVisible;
    layers.grid.container.setVisible(gridVisible);
    document.getElementById('menu-grid-toggle').textContent =
        gridVisible ? 'Masquer la grille' : 'Afficher la grille';
});

function setHexSize(size) {
    hexSize = size;
    drawHexGrid();
    document.getElementById('menu-grid-small').classList.toggle('checked', size === 20);
    document.getElementById('menu-grid-medium').classList.toggle('checked', size === 40);
    document.getElementById('menu-grid-large').classList.toggle('checked', size === 60);
}

document.getElementById('menu-grid-small').addEventListener('click', () => setHexSize(20));
document.getElementById('menu-grid-medium').addEventListener('click', () => setHexSize(40));
document.getElementById('menu-grid-large').addEventListener('click', () => setHexSize(60));

// ─── Keyboard shortcuts ───
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && (e.key === '+' || e.key === '=')) {
        e.preventDefault();
        const c = layers[activeKey].container;
        const cx = game.scale.width / 2;
        const cy = game.scale.height / 2;
        zoomContainerAt(c, c.scaleX * 1.2, cx, cy);
    } else if (e.ctrlKey && e.key === '-') {
        e.preventDefault();
        const c = layers[activeKey].container;
        const cx = game.scale.width / 2;
        const cy = game.scale.height / 2;
        zoomContainerAt(c, c.scaleX / 1.2, cx, cy);
    } else if (e.ctrlKey && e.key === '0') {
        e.preventDefault();
        fitLayerToWindow(activeKey);
    }
});
