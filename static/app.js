// =============================================
//  FANTASY UCL — SQUAD BUILDER (JavaScript)
// =============================================

// ---------- FORMACIONES: posiciones (x%, y%) en el campo ----------
const FORMATION_LAYOUTS = {
    '433': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 12, y: 73, pos: 'DEF', label: 'LI' },
        { x: 35, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 65, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 88, y: 73, pos: 'DEF', label: 'LD' },
        { x: 25, y: 50, pos: 'CEN', label: 'MC' },
        { x: 50, y: 46, pos: 'CEN', label: 'MC' },
        { x: 75, y: 50, pos: 'CEN', label: 'MC' },
        { x: 18, y: 24, pos: 'DEL', label: 'EI' },
        { x: 50, y: 18, pos: 'DEL', label: 'DC' },
        { x: 82, y: 24, pos: 'DEL', label: 'ED' },
    ],
    '442': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 12, y: 73, pos: 'DEF', label: 'LI' },
        { x: 35, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 65, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 88, y: 73, pos: 'DEF', label: 'LD' },
        { x: 12, y: 48, pos: 'CEN', label: 'MI' },
        { x: 37, y: 50, pos: 'CEN', label: 'MC' },
        { x: 63, y: 50, pos: 'CEN', label: 'MC' },
        { x: 88, y: 48, pos: 'CEN', label: 'MD' },
        { x: 35, y: 22, pos: 'DEL', label: 'DC' },
        { x: 65, y: 22, pos: 'DEL', label: 'DC' },
    ],
    '451': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 12, y: 73, pos: 'DEF', label: 'LI' },
        { x: 35, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 65, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 88, y: 73, pos: 'DEF', label: 'LD' },
        { x: 10, y: 47, pos: 'CEN', label: 'MI' },
        { x: 30, y: 50, pos: 'CEN', label: 'MC' },
        { x: 50, y: 47, pos: 'CEN', label: 'MC' },
        { x: 70, y: 50, pos: 'CEN', label: 'MC' },
        { x: 90, y: 47, pos: 'CEN', label: 'MD' },
        { x: 50, y: 20, pos: 'DEL', label: 'DC' },
    ],
    '343': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 25, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 50, y: 79, pos: 'DEF', label: 'DFC' },
        { x: 75, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 12, y: 48, pos: 'CEN', label: 'MI' },
        { x: 37, y: 50, pos: 'CEN', label: 'MC' },
        { x: 63, y: 50, pos: 'CEN', label: 'MC' },
        { x: 88, y: 48, pos: 'CEN', label: 'MD' },
        { x: 18, y: 24, pos: 'DEL', label: 'EI' },
        { x: 50, y: 18, pos: 'DEL', label: 'DC' },
        { x: 82, y: 24, pos: 'DEL', label: 'ED' },
    ],
    '352': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 25, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 50, y: 79, pos: 'DEF', label: 'DFC' },
        { x: 75, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 10, y: 47, pos: 'CEN', label: 'MI' },
        { x: 30, y: 50, pos: 'CEN', label: 'MC' },
        { x: 50, y: 47, pos: 'CEN', label: 'MC' },
        { x: 70, y: 50, pos: 'CEN', label: 'MC' },
        { x: 90, y: 47, pos: 'CEN', label: 'MD' },
        { x: 35, y: 22, pos: 'DEL', label: 'DC' },
        { x: 65, y: 22, pos: 'DEL', label: 'DC' },
    ],
    '532': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 8,  y: 68, pos: 'DEF', label: 'CAI' },
        { x: 28, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 50, y: 79, pos: 'DEF', label: 'DFC' },
        { x: 72, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 92, y: 68, pos: 'DEF', label: 'CAD' },
        { x: 25, y: 48, pos: 'CEN', label: 'MC' },
        { x: 50, y: 46, pos: 'CEN', label: 'MC' },
        { x: 75, y: 48, pos: 'CEN', label: 'MC' },
        { x: 35, y: 22, pos: 'DEL', label: 'DC' },
        { x: 65, y: 22, pos: 'DEL', label: 'DC' },
    ],
    '541': [
        { x: 50, y: 91, pos: 'POR', label: 'POR' },
        { x: 8,  y: 68, pos: 'DEF', label: 'CAI' },
        { x: 28, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 50, y: 79, pos: 'DEF', label: 'DFC' },
        { x: 72, y: 77, pos: 'DEF', label: 'DFC' },
        { x: 92, y: 68, pos: 'DEF', label: 'CAD' },
        { x: 12, y: 47, pos: 'CEN', label: 'MI' },
        { x: 37, y: 50, pos: 'CEN', label: 'MC' },
        { x: 63, y: 50, pos: 'CEN', label: 'MC' },
        { x: 88, y: 47, pos: 'CEN', label: 'MD' },
        { x: 50, y: 20, pos: 'DEL', label: 'DC' },
    ],
};

// ---------- ESTADO GLOBAL ----------
let currentFormation = '433';
let squad = new Array(11).fill(null);
let allPlayers = [];
let activeSlotIndex = null;

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
    loadPlayers();
    renderFormationButtons();
    setFormation('433');
    updateSquadInfo();
});

// ---------- CARGAR JUGADORES ----------
async function loadPlayers() {
    const res = await fetch('/api/players');
    allPlayers = await res.json();
}

// ---------- FORMACIONES ----------
function renderFormationButtons() {
    const grid = document.getElementById('formation-grid');
    const formations = Object.keys(FORMATION_LAYOUTS);
    grid.innerHTML = '';
    formations.forEach(f => {
        const btn = document.createElement('button');
        btn.className = 'formation-btn' + (f === currentFormation ? ' active' : '');
        btn.textContent = f.split('').join('-');
        btn.addEventListener('click', () => setFormation(f));
        grid.appendChild(btn);
    });
}

function setFormation(f) {
    currentFormation = f;
    squad = new Array(11).fill(null);
    document.querySelectorAll('.formation-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.replace(/-/g, '') === f);
    });
    renderPitch();
    updateSquadInfo();
}

// ---------- RENDERIZAR CAMPO ----------
function renderPitch() {
    const container = document.getElementById('pitch-slots');
    container.innerHTML = '';
    const layout = FORMATION_LAYOUTS[currentFormation];

    layout.forEach((slot, idx) => {
        const el = document.createElement('div');
        el.className = 'player-slot';
        el.style.left = slot.x + '%';
        el.style.top = slot.y + '%';
        el.dataset.index = idx;

        if (squad[idx]) {
            el.innerHTML = filledCardHTML(squad[idx], slot.label);
        } else {
            el.innerHTML = emptyCardHTML(slot.label);
        }

        el.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-btn')) {
                squad[idx] = null;
                renderPitch();
                updateSquadInfo();
                return;
            }
            openPlayerModal(idx, slot.pos);
        });

        container.appendChild(el);
    });
}

function emptyCardHTML(label) {
    return `
        <div class="player-card">
            <div class="add-icon">+</div>
            <span class="slot-label">${label}</span>
        </div>
        <div class="position-badge">${label}</div>`;
}

function filledCardHTML(player, label) {
    const pts = player.ptos_total || '0';
    return `
        <div class="player-card filled">
            <span class="remove-btn" title="Quitar">X</span>
            <div class="player-rating-badge">${pts}</div>
            <div class="player-name">${player.name}</div>
            <div class="player-price">${player.price}</div>
            <div class="stars">${starsHTML(player.estado_forma)}</div>
        </div>
        <div class="position-badge">${label}</div>`;
}

function starsHTML(forma) {
    if (!forma) return '';
    const val = parseFloat(forma);
    let html = '';
    for (let i = 1; i <= 5; i++) {
        if (val >= i) html += '<span style="color:#ffd700">&#9733;</span>';
        else if (val >= i - 0.5) html += '<span style="color:#ffd700">&#9733;</span>';
        else html += '<span class="empty">&#9733;</span>';
    }
    return html;
}

// ---------- MODAL DE SELECCION ----------
function openPlayerModal(slotIndex, position) {
    activeSlotIndex = slotIndex;
    const overlay = document.getElementById('modal-overlay');
    const titlePos = document.getElementById('modal-pos-label');
    const searchInput = document.getElementById('modal-search');

    titlePos.textContent = positionFullName(position);
    searchInput.value = '';
    overlay.classList.add('active');

    renderPlayerList(position, '');

    searchInput.oninput = () => renderPlayerList(position, searchInput.value);
    searchInput.focus();
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    activeSlotIndex = null;
}

function positionFullName(pos) {
    const map = { 'POR': 'Portero', 'DEF': 'Defensa', 'CEN': 'Centrocampista', 'DEL': 'Delantero' };
    return map[pos] || pos;
}

function renderPlayerList(position, search) {
    const list = document.getElementById('modal-players-list');
    const usedNames = new Set(squad.filter(Boolean).map(p => p.name));

    let filtered = allPlayers.filter(p => p.position === position);

    if (search.trim()) {
        const q = search.trim().toLowerCase();
        filtered = filtered.filter(p => p.name.toLowerCase().includes(q));
    }

    filtered.sort((a, b) => parseInt(b.ptos_total || '0') - parseInt(a.ptos_total || '0'));

    if (filtered.length === 0) {
        list.innerHTML = '<div style="padding:20px;text-align:center;color:#4a6088;">No se encontraron jugadores</div>';
        return;
    }

    list.innerHTML = filtered.map(p => {
        const isUsed = usedNames.has(p.name);
        return `
            <div class="modal-player-row ${isUsed ? 'disabled' : ''}" data-name="${escapeAttr(p.name)}">
                <div class="mp-rating">${p.ptos_total || '0'}</div>
                <div class="mp-info">
                    <div class="mp-name">${p.name}</div>
                    <div class="mp-meta">${p.price} · ${p.team_match || ''} · ${p.estado_forma || ''}</div>
                </div>
                <div class="mp-stats">
                    <div class="mp-stat">
                        <div class="mp-stat-val">${p.goles || 0}</div>
                        <div class="mp-stat-label">GOL</div>
                    </div>
                    <div class="mp-stat">
                        <div class="mp-stat-val">${p.asistencias || 0}</div>
                        <div class="mp-stat-label">ASI</div>
                    </div>
                    <div class="mp-stat">
                        <div class="mp-stat-val">${p.mins_jugados || 0}</div>
                        <div class="mp-stat-label">MIN</div>
                    </div>
                </div>
            </div>`;
    }).join('');

    list.querySelectorAll('.modal-player-row:not(.disabled)').forEach(row => {
        row.addEventListener('click', () => {
            const name = row.dataset.name;
            const player = allPlayers.find(p => p.name === name);
            if (player && activeSlotIndex !== null) {
                squad[activeSlotIndex] = player;
                closeModal();
                renderPitch();
                updateSquadInfo();
            }
        });
    });
}

function escapeAttr(str) {
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ---------- SQUAD INFO ----------
function updateSquadInfo() {
    const filled = squad.filter(Boolean);
    document.getElementById('info-players').textContent = `${filled.length} / 11`;

    let totalPrice = 0;
    filled.forEach(p => {
        totalPrice += parseFloat((p.price || '0').replace('m', ''));
    });
    document.getElementById('info-price').textContent = totalPrice.toFixed(1) + 'm';

    let totalPts = 0;
    filled.forEach(p => {
        totalPts += parseInt(p.ptos_total || '0');
    });
    document.getElementById('info-pts').textContent = totalPts;

    const avg = filled.length > 0 ? (totalPts / filled.length).toFixed(1) : '0';
    document.getElementById('info-avg').textContent = avg;

    document.getElementById('btn-save').disabled = filled.length < 11;
}

// ---------- GUARDAR (inline estilo FUTBIN) ----------
async function saveSquad() {
    const input = document.getElementById('save-filename');
    const filename = input.value.trim();
    if (!filename) {
        input.focus();
        showToast('Escribe un nombre para la plantilla', true);
        return;
    }

    const layout = FORMATION_LAYOUTS[currentFormation];
    const posOrder = { 'POR': 0, 'DEF': 1, 'CEN': 2, 'DEL': 3 };
    const indexed = squad.map((p, i) => ({ player: p, slot: layout[i] }));
    indexed.sort((a, b) => posOrder[a.slot.pos] - posOrder[b.slot.pos]);

    const orderedSquad = [];
    indexed.forEach(item => {
        if (item.player) orderedSquad.push(item.player);
    });

    const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, squad: orderedSquad }),
    });

    const data = await res.json();

    if (data.success) {
        showToast('Plantilla guardada como ' + filename + '.json');
    } else {
        showToast('Error al guardar', true);
    }
}

// ---------- LIMPIAR ----------
function clearSquad() {
    squad = new Array(11).fill(null);
    renderPitch();
    updateSquadInfo();
}

// ---------- TOAST ----------
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast show' + (isError ? ' error' : '');
    setTimeout(() => { toast.className = 'toast'; }, 3000);
}

// ---------- ATAJOS TECLADO ----------
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
    // Enter en la barra de guardado
    if (e.key === 'Enter' && document.activeElement === document.getElementById('save-filename')) {
        const btn = document.getElementById('btn-save');
        if (!btn.disabled) saveSquad();
    }
});
