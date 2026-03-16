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
    loadCurrentMarket(); // Cargar mercado guardado si existe
    renderFormationSelector();
    loadTemplatesList();
    setFormation('433');
    updateSquadInfo();
});

async function loadCurrentMarket() {
    try {
        const res = await fetch('/api/market/current');
        if (res.ok) {
            const data = await res.json();
            if (data.success) renderMarketList(data.mercado);
        }
    } catch (e) {}
}

// ---------- CARGAR JUGADORES ----------
async function loadPlayers() {
    const res = await fetch('/api/players');
    allPlayers = await res.json();
}

/**
 * Recarga la base de datos de jugadores local y actualiza los stats de los que estan en el campo.
 */
async function refreshSquadStats() {
    const btn = document.getElementById('btn-refresh-stats');
    if (btn) btn.disabled = true;
    showToast('Actualizando estadísticas locales...');
    
    try {
        await loadPlayers();
        // Actualizar el squad actual con los nuevos objetos (match por nombre)
        for (let i = 0; i < squad.length; i++) {
            if (squad[i]) {
                const updated = allPlayers.find(p => p.name === squad[i].name);
                if (updated) squad[i] = updated;
            }
        }
        renderPitch();
        updateSquadInfo();
        showToast('Estadísticas actualizadas correctamente');
    } catch (e) {
        showToast('Error al actualizar estadísticas', true);
    } finally {
        if (btn) btn.disabled = false;
    }
}

/**
 * Lanza el proceso de scraping en el servidor.
 */
async function triggerScraping() {
    const btn = document.getElementById('btn-full-scrape');
    if (!confirm('Esto lanzará un navegador en el servidor para descargar datos de UEFA.com. Tardará varios minutos. ¿Continuar?')) return;
    
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Scraping...';
    }
    showToast('Iniciando actualización UEFA (esto tardará)...');
    
    try {
        const res = await fetch('/api/players/update', { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            showToast('¡UEFA Sync completado! Refrescando equipo...');
            await refreshSquadStats();
        } else {
            showToast('Error: ' + data.error, true);
        }
    } catch (e) {
        showToast('Error de conexión con el scraper', true);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Update UEFA (Scraping)';
        }
    }
}

// ---------- FORMACIONES ----------
function renderFormationSelector() {
    const select = document.getElementById('formation-select');
    if (!select) return;

    const formations = Object.keys(FORMATION_LAYOUTS);
    select.innerHTML = formations
        .map(f => `<option value="${f}">${f.split('').join('-')}</option>`)
        .join('');

    select.value = currentFormation;
    select.onchange = () => setFormation(select.value);
}

function setFormation(f) {
    if (!FORMATION_LAYOUTS[f]) return;

    const hadPlayers = squad.some(Boolean);
    if (hadPlayers && f !== currentFormation) {
        const ok = confirm('Cambiar la formación vaciará la plantilla actual. ¿Continuar?');
        if (!ok) {
            const select = document.getElementById('formation-select');
            if (select) select.value = currentFormation;
            return;
        }
    }

    currentFormation = f;
    squad = new Array(11).fill(null);
    const select = document.getElementById('formation-select');
    if (select) select.value = f;

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

    const analyzeBtn = document.getElementById('btn-analyze');
    if (analyzeBtn) {
        analyzeBtn.disabled = filled.length < 11;
        analyzeBtn.onclick = toggleChat;
    }

    // Sincronizar con el servidor en segundo plano
    syncSquadWithServer(filled);
}

// ---------- SINCRONIZACION ----------
async function syncSquadWithServer(filledSquad) {
    try {
        await fetch('/api/sync_squad', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ squad: filledSquad }),
        });
    } catch (e) {
        console.error('Error sincronizando plantilla:', e);
    }
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
        body: JSON.stringify({ filename, squad: orderedSquad, formation: currentFormation }),
    });

    const data = await res.json();

    if (data.success) {
        showToast('Plantilla guardada como ' + filename + '.json');
        loadTemplatesList();
    } else {
        showToast('Error al guardar', true);
    }
}

async function loadTemplatesList() {
    const select = document.getElementById('load-template-select');
    const loadBtn = document.getElementById('btn-load-template');
    if (!select || !loadBtn) return;

    try {
        const res = await fetch('/api/templates');
        const data = await res.json();

        if (!data.success || !Array.isArray(data.templates) || data.templates.length === 0) {
            select.innerHTML = '<option value="">Sin plantillas guardadas</option>';
            loadBtn.disabled = true;
            return;
        }

        select.innerHTML = data.templates
            .map(name => `<option value="${escapeAttr(name)}">${name}</option>`)
            .join('');
        loadBtn.disabled = false;
    } catch (e) {
        select.innerHTML = '<option value="">Error al cargar</option>';
        loadBtn.disabled = true;
    }
}

function applyLoadedSquadToFormation(loadedPlayers) {
    const byPosition = {
        POR: loadedPlayers.filter(p => p.position === 'POR'),
        DEF: loadedPlayers.filter(p => p.position === 'DEF'),
        CEN: loadedPlayers.filter(p => p.position === 'CEN'),
        DEL: loadedPlayers.filter(p => p.position === 'DEL'),
    };

    const layout = FORMATION_LAYOUTS[currentFormation];
    const nextSquad = new Array(11).fill(null);

    layout.forEach((slot, idx) => {
        const list = byPosition[slot.pos] || [];
        nextSquad[idx] = list.length > 0 ? list.shift() : null;
    });

    squad = nextSquad;
    renderPitch();
    updateSquadInfo();
}

async function loadSavedTemplate() {
    const select = document.getElementById('load-template-select');
    if (!select || !select.value) {
        showToast('Selecciona una plantilla', true);
        return;
    }

    try {
        const res = await fetch('/api/templates/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: select.value }),
        });
        const data = await res.json();

        if (!data.success) {
            showToast('Error al cargar: ' + (data.error || 'desconocido'), true);
            return;
        }

        const loadedPlayers = Array.isArray(data.squad) ? data.squad : [];
        applyLoadedSquadToFormation(loadedPlayers);
        showToast('Plantilla cargada: ' + select.value);
    } catch (e) {
        showToast('Error de conexión al cargar plantilla', true);
    }
}

// ---------- MERCADO ----------
async function generateMarket() {
    showToast('Generando mercado personalizado...');
    try {
        const res = await fetch('/api/market/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ squad: squad.filter(Boolean) }),
        });
        const data = await res.json();
        if (data.success) {
            showToast('¡Mercado de 15 jugadores listo!');
            renderMarketList(data.mercado);
        } else {
            showToast('Error al generar mercado: ' + data.error, true);
        }
    } catch (e) {
        showToast('Error de conexión', true);
    }
}

function renderMarketList(players) {
    const list = document.getElementById('market-list');
    const container = document.getElementById('market-view');
    if (!list || !container) return;

    if (!players || players.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    list.innerHTML = players.map(p => `
        <li style="margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <span style="color: #ffd700;">${p.position}</span> · <strong>${p.name}</strong> (${p.price})
        </li>
    `).join('');
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

// ---------- ANALIZAR CON IA ----------
async function analyzeSquad() {
    const presupuesto = parseFloat(document.getElementById('presupuesto-input').value) || 0;
    const btn = document.getElementById('btn-analyze');

    btn.disabled = true;
    btn.textContent = 'Analizando...';
    showToast('El análisis puede tardar varios minutos...');

    try {
        const res = await fetch('/api/analizar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ squad: squad.filter(Boolean), presupuesto }),
        });

        const data = await res.json();

        if (data.success) {
            document.getElementById('results-content').textContent = data.resultado;
            document.getElementById('results-overlay').classList.add('active');
        } else {
            showToast('Error: ' + data.error, true);
        }
    } catch (e) {
        showToast('Error de conexión con el servidor', true);
    } finally {
        btn.disabled = squad.filter(Boolean).length < 11;
        btn.textContent = 'Analizar con IA';
    }
}

function closeResults() {
    document.getElementById('results-overlay').classList.remove('active');
}

// ---------- CHATBOT LOGIC ----------
function toggleChat() {
    const input = document.getElementById('chat-input');
    if (input) input.focus();
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    appendMessage('user', text);
    input.value = '';

    // Mostrar indicador de carga
    const typingId = 'typing-' + Date.now();
    appendMessage('bot', '...', typingId);

    try {
        const presupuestoEl = document.getElementById('presupuesto-input');
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                squad: squad.filter(Boolean),
                presupuesto: presupuestoEl ? parseFloat(presupuestoEl.value) || 0 : 0
            }),
        });

        const data = await res.json();
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        if (data.success) {
            appendMessage('bot', data.response);
        } else {
            appendMessage('bot', 'Error: ' + data.error);
        }
    } catch (e) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        appendMessage('bot', 'Error de conexión con el analista.');
    }
}

function appendMessage(role, text, id = null) {
    const container = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${role}-msg`;
    if (id) msgDiv.id = id;
    
    // Mantenemos los saltos de línea y emojis
    msgDiv.style.whiteSpace = 'pre-wrap';
    msgDiv.textContent = text;
    
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

// ---------- EVENT LISTENERS EXTRA ----------
document.addEventListener('DOMContentLoaded', () => {
    // ... codigo anterior ...
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    if (chatSend) {
        chatSend.onclick = sendChatMessage;
    }
    if (chatInput) {
        chatInput.onkeydown = (e) => {
            if (e.key === 'Enter') sendChatMessage();
        };
    }
});

// ---------- ATAJOS TECLADO ----------
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        const chatPanel = document.getElementById('chat-panel');
        if (chatPanel.classList.contains('active')) toggleChat();
    }
    // ... resto del codigo ...
});
