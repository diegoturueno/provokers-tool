// --- NAVIGATION HANDLERS (GLOBAL) ---
// Definir esto FUERA de cualquier función para garantizar que existe
window.switchPhase = function (phaseId) {
    console.log("Switching to phase:", phaseId);

    try {
        // 1. Ocultar todas las vistas
        document.querySelectorAll('section[id^="phase-"]').forEach(el => el.classList.add('hidden'));

        // 2. Desactivar todos los links
        document.querySelectorAll('.phase-link').forEach(el => el.classList.remove('active'));

        // 3. Mostrar vista objetivo
        const target = document.getElementById('phase-' + phaseId + '-view');
        if (target) {
            target.classList.remove('hidden');
        } else {
            console.error("No view found for phase " + phaseId);
            // Fallback: intentar buscar por ID numérico si hay discrepancia
            const altTarget = document.getElementById('phase-' + parseInt(phaseId) + '-view');
            if (altTarget) altTarget.classList.remove('hidden');
        }

        // 4. Activar link objetivo
        const link = document.querySelector(`.phase-link[data-phase="${phaseId}"]`);
        if (link) link.classList.add('active');

        // 5. Actualizar Header
        const titles = { 1: 'Inputs', 2: 'Patrones', 3: 'Ejes', 7: 'Arquetipo' };
        const statusSpan = document.querySelector('.case-status');
        if (statusSpan) statusSpan.textContent = `Fase ${phaseId}: ${titles[phaseId] || ''}`;

    } catch (e) {
        console.error("Error switching phase:", e);
        alert("Error al cambiar de fase: " + e.message);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    try {
        // --- ROUTING SIMPLE ---
        const path = window.location.pathname;

        if (path === '/') {
            initDashboard();
        } else if (path.startsWith('/case/')) {
            initCaseView();
        }
    } catch (e) {
        console.error("Critical Error in App Initialization:", e);
        alert("Error crítico al iniciar la aplicación: " + e.message);
    }

    // --- DASHBOARD LOGIC ---
    function initDashboard() {
        const modal = document.getElementById('new-case-modal');
        const btn = document.getElementById('new-case-btn');
        const span = document.getElementsByClassName("close-modal")[0];
        const form = document.getElementById('new-case-form');
        const grid = document.getElementById('cases-grid');

        // Cargar casos
        fetch('/api/cases')
            .then(res => res.json())
            .then(cases => {
                grid.innerHTML = '';
                if (cases.length === 0) {
                    grid.innerHTML = '<div style="color:var(--text-secondary)">No hay casos. Crea uno nuevo.</div>';
                    return;
                }
                cases.forEach(c => {
                    const card = document.createElement('div');
                    card.className = 'case-card';
                    card.innerHTML = `
                        <h3>${c.identifier}</h3>
                        <p>${c.description || 'Sin descripción'}</p>
                        <div class="case-meta">
                            <span>${new Date(c.created_at).toLocaleDateString()}</span>
                            <span style="color: var(--success)">Activo</span>
                        </div>
                    `;
                    card.onclick = () => window.location.href = `/case/${c.id}`;
                    grid.appendChild(card);
                });
            });

        // Modal Logic
        if (btn) btn.onclick = () => modal.style.display = "block";
        if (span) span.onclick = () => modal.style.display = "none";
        window.onclick = (event) => { if (event.target == modal) modal.style.display = "none"; }

        // Crear Caso
        if (form) form.onsubmit = async (e) => {
            e.preventDefault();
            const identifier = document.getElementById('case-identifier').value;
            const description = document.getElementById('case-description').value;

            const res = await fetch('/api/cases', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ identifier, description })
            });

            if (res.ok) {
                window.location.reload();
            }
        };
    }

    // --- CASE VIEW LOGIC ---
    function initCaseView() {
        // CURRENT_CASE_ID está definido en el HTML
        const inputsList = document.getElementById('inputs-list');
        const patternsList = document.getElementById('patterns-list');
        const addBtn = document.getElementById('add-input-btn');
        const analyzeBtn = document.getElementById('analyze-patterns-btn');
        const formContainer = document.getElementById('input-form-container');
        const cancelBtn = document.getElementById('cancel-input-btn');
        const form = document.getElementById('new-input-form');

        // Navigation Elements
        const phaseLinks = document.querySelectorAll('.phase-link');
        // Usar strings como claves para coincidir con dataset.phase
        const phaseViews = {
            "1": document.getElementById('phase-1-view'),
            "2": document.getElementById('phase-2-view'),
            "3": document.getElementById('phase-3-view')
        };
        const statusSpan = document.querySelector('.case-status');

        // Mode Toggle Logic
        const cloudToggle = document.getElementById('cloud-toggle');
        const modeLabel = document.getElementById('mode-label');

        if (cloudToggle) {
            cloudToggle.addEventListener('change', () => {
                if (cloudToggle.checked) {
                    modeLabel.textContent = "Modo Nube (OpenAI)";
                    modeLabel.style.color = "#2cb67d";
                } else {
                    modeLabel.textContent = "Modo Local (Ollama)";
                    modeLabel.style.color = "#94a1b2";
                }
            });
        }

        // Cargar Info del Caso
        fetch(`/api/cases/${CURRENT_CASE_ID}`)
            .then(res => res.json())
            .then(data => {
                const header = document.getElementById('header-case-id');
                if (header) header.textContent = data.identifier;
            })
            .catch(e => console.error("Error loading case info:", e));

        // Initial Load
        loadInputs();
        loadPatterns();

        // Inicializar en Fase 1
        // (Ya se hace por defecto en el HTML, pero esto asegura el estado)

        // Enable Phase 2 link for demo purposes (normally logic based)
        const p2Link = document.querySelector('[data-phase="2"]');
        if (p2Link) p2Link.classList.remove('disabled');


        // --- PHASE 1 LOGIC ---
        if (addBtn) addBtn.onclick = () => {
            formContainer.classList.remove('hidden');
            addBtn.style.display = 'none';
        };

        if (cancelBtn) cancelBtn.onclick = () => {
            formContainer.classList.add('hidden');
            addBtn.style.display = 'block';
            form.reset();
        };

        if (form) form.onsubmit = async (e) => {
            e.preventDefault();
            const content = document.getElementById('input-content').value;
            const type = document.getElementById('input-type').value;
            const date = document.getElementById('input-date').value;

            const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/inputs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content,
                    input_type: type,
                    metadata: { date }
                })
            });

            if (res.ok) {
                loadInputs();
                cancelBtn.click();
            }
        };

        function loadInputs() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/inputs`)
                .then(res => res.json())
                .then(inputs => {
                    if (!inputsList) return;
                    inputsList.innerHTML = '';
                    if (inputs.length === 0) {
                        inputsList.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding: 2rem;">No hay inputs registrados. Agrega el primero.</div>';
                        return;
                    }
                    inputs.forEach(inp => {
                        const div = document.createElement('div');
                        div.className = 'input-card';
                        const meta = JSON.parse(inp.metadata || '{}');
                        div.innerHTML = `
                            <div class="input-header">
                                <span class="input-badge">${inp.input_type}</span>
                                <span>${meta.date || ''}</span>
                            </div>
                            <div class="input-content">${inp.content}</div>
                        `;
                        inputsList.appendChild(div);
                    });
                })
                .catch(e => console.error("Error loading inputs:", e));
        }

        // --- PHASE 2 LOGIC ---
        if (analyzeBtn) {
            analyzeBtn.onclick = async () => {
                console.log("Botón presionado");
                analyzeBtn.classList.add('loading');
                analyzeBtn.disabled = true;

                const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';
                console.log("Modo:", mode);

                try {
                    const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/analyze/patterns`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: mode })
                    });

                    const contentType = res.headers.get("content-type");
                    if (contentType && contentType.indexOf("application/json") !== -1) {
                        const data = await res.json();
                        if (data.error) {
                            alert('Error: ' + data.error);
                        } else {
                            loadPatterns();
                        }
                    } else {
                        const text = await res.text();
                        console.error("Server Error:", text);
                        alert('Error del servidor (500). Revisa la consola para más detalles.');
                    }

                } catch (e) {
                    alert('Error de conexión: ' + e.message);
                    console.error(e);
                } finally {
                    analyzeBtn.classList.remove('loading');
                    analyzeBtn.disabled = false;
                }
            };
        }

        function loadPatterns() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/patterns`)
                .then(res => res.json())
                .then(patterns => {
                    if (!patternsList) return;
                    patternsList.innerHTML = '';
                    if (patterns.length === 0) {
                        patternsList.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding: 2rem; grid-column: 1/-1;">No hay patrones detectados aún.</div>';
                        return;
                    }
                    patterns.forEach(p => {
                        const div = document.createElement('div');
                        div.className = 'pattern-card';
                        div.innerHTML = `
                            <div class="pattern-tags">
                                <span class="tag recurrence-${p.recurrence}">Recurrencia: ${p.recurrence}</span>
                                <span class="tag">Persistencia: ${p.persistence}</span>
                                <span class="tag">Presión: ${p.pressure_context}</span>
                            </div>
                            <h4>${p.description}</h4>
                            ${p.contradictions !== 'Ninguna' ? `<div class="pattern-contradictions">⚠️ ${p.contradictions}</div>` : ''}
                        `;
                        patternsList.appendChild(div);
                    });
                })
                .catch(e => console.error("Error loading patterns:", e));
        }


        // --- PHASE 3 LOGIC ---
        const autoLinkBtn = document.getElementById('auto-link-btn');

        if (autoLinkBtn) {
            autoLinkBtn.onclick = async () => {
                autoLinkBtn.classList.add('loading');
                autoLinkBtn.disabled = true;
                const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';

                try {
                    const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/analyze/link_axes`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: mode })
                    });
                    const data = await res.json();
                    if (data.error) alert(data.error);
                    else loadAxesAssignments();
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    autoLinkBtn.classList.remove('loading');
                    autoLinkBtn.disabled = false;
                }
            };
        }

        function loadAxesAssignments() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/axis_assignments`)
                .then(res => res.json())
                .then(assigns => {
                    // Limpiar columnas
                    document.querySelectorAll('.axis-column .axis-content').forEach(el => el.innerHTML = '');

                    assigns.forEach(a => {
                        // Buscar columna por nombre de eje (data-axis)
                        const col = document.querySelector(`.axis-column[data-axis="${a.axis_name}"] .axis-content`);
                        if (col) {
                            const card = document.createElement('div');
                            card.className = 'axis-card';
                            card.innerHTML = `
                                <strong>${a.pattern_description}</strong>
                                <div class="justification">${a.justification}</div>
                            `;
                            col.appendChild(card);
                        }
                    });
                })
                .catch(e => console.error("Error loading axes:", e));
        }

        // Cargar datos iniciales si estamos en fase 3
        loadAxesAssignments();

        // Habilitar link fase 3
        const p3Link = document.querySelector('[data-phase="3"]');
        if (p3Link) p3Link.classList.remove('disabled');

    } // End initCaseView
});
