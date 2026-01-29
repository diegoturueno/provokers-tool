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
        const titles = { 1: 'Inputs', 2: 'Patrones', 3: 'Ejes', 4: 'Dimensiones', 5: 'Tensiones', 6: 'Umbral', 7: 'Arquetipo' };
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

        // --- PHASE 4 LOGIC ---
        const analyzeDimBtn = document.getElementById('analyze-dimensions-btn');

        if (analyzeDimBtn) {
            analyzeDimBtn.onclick = async () => {
                analyzeDimBtn.classList.add('loading');
                analyzeDimBtn.disabled = true;
                const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';

                try {
                    const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/analyze/dimensions`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: mode })
                    });
                    const data = await res.json();
                    if (data.error) alert(data.error);
                    else loadDimensions();
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    analyzeDimBtn.classList.remove('loading');
                    analyzeDimBtn.disabled = false;
                }
            };
        }

        function loadDimensions() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/axis_states`)
                .then(res => res.json())
                .then(states => {
                    const container = document.getElementById('dimensions-container');
                    if (!container) return;
                    container.innerHTML = '';

                    if (states.length === 0) {
                        container.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--text-secondary)">No hay dimensiones analizadas.</div>';
                        return;
                    }

                    states.forEach(s => {
                        const statusClass = `status-${s.status.replace(/\s+/g, '-')}`;
                        const div = document.createElement('div');
                        div.className = `dimension-card ${statusClass}`;
                        div.innerHTML = `
                            <div class="dim-header">
                                <span class="dim-title">${s.axis_name}</span>
                                <span class="dim-status">${s.status}</span>
                            </div>
                            <div class="dim-value">${s.value || '---'}</div>
                            <div class="dim-justification">${s.justification}</div>
                        `;
                        container.appendChild(div);
                    });
                })
                .catch(e => console.error("Error loading dimensions:", e));
        }

        // Cargar datos iniciales si estamos en fase 4
        loadDimensions();

        // Habilitar link fase 4 si hay datos previos (opcional, por ahora lo dejamos habilitado por defecto en HTML o aquí)
        const p4Link = document.querySelector('[data-phase="4"]');
        if (p4Link) p4Link.classList.remove('disabled');

        // --- PHASE 5 LOGIC ---
        const analyzeTensionBtn = document.getElementById('analyze-tensions-btn');

        if (analyzeTensionBtn) {
            analyzeTensionBtn.onclick = async () => {
                analyzeTensionBtn.classList.add('loading');
                analyzeTensionBtn.disabled = true;
                const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';

                try {
                    const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/analyze/tensions`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: mode })
                    });
                    const data = await res.json();
                    if (data.error) alert(data.error);
                    else loadTensions();
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    analyzeTensionBtn.classList.remove('loading');
                    analyzeTensionBtn.disabled = false;
                }
            };
        }

        function loadTensions() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/tensions`)
                .then(res => res.json())
                .then(tensions => {
                    const container = document.getElementById('tensions-container');
                    if (!container) return;
                    container.innerHTML = '';

                    if (tensions.length === 0) {
                        container.innerHTML = '<div style="text-align:center; color:var(--text-secondary)">No hay tensiones detectadas.</div>';
                        return;
                    }

                    tensions.forEach(t => {
                        const div = document.createElement('div');
                        div.className = 'tension-card';
                        div.innerHTML = `
                            <div class="tension-header">
                                <span class="tension-type">${t.type}</span>
                                <span class="tension-severity severity-${t.severity}">${t.severity}</span>
                            </div>
                            <div class="tension-desc">${t.description}</div>
                            <div class="tension-axes">
                                <strong>Ejes en conflicto:</strong> ${t.axes_involved.join(', ')}
                            </div>
                        `;
                        container.appendChild(div);
                    });
                })
                .catch(e => console.error("Error loading tensions:", e));
        }

        // Cargar datos iniciales
        loadTensions();

        // Habilitar link fase 5
        const p5Link = document.querySelector('[data-phase="5"]');
        if (p5Link) p5Link.classList.remove('disabled');

        // --- PHASE 6 LOGIC ---
        const analyzeThresholdBtn = document.getElementById('analyze-threshold-btn');

        if (analyzeThresholdBtn) {
            analyzeThresholdBtn.onclick = async () => {
                analyzeThresholdBtn.classList.add('loading');
                analyzeThresholdBtn.disabled = true;
                const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';

                try {
                    const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/analyze/threshold`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: mode })
                    });
                    const data = await res.json();
                    if (data.error) alert(data.error);
                    else loadThreshold();
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    analyzeThresholdBtn.classList.remove('loading');
                    analyzeThresholdBtn.disabled = false;
                }
            };
        }

        function loadThreshold() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/threshold`)
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('threshold-container');
                    if (!data || !container) return;

                    container.classList.remove('hidden');
                    document.getElementById('threshold-score').textContent = data.score;
                    document.getElementById('threshold-status').textContent = data.status;
                    document.getElementById('threshold-reasoning').textContent = data.reasoning;

                    // Color coding based on score
                    const circle = document.querySelector('.score-circle');
                    if (data.score >= 61) circle.style.borderColor = 'var(--success)';
                    else if (data.score >= 41) circle.style.borderColor = '#ffce56';
                    else circle.style.borderColor = 'var(--danger)';
                })
                .catch(e => console.error("Error loading threshold:", e));
        }

        // Cargar datos iniciales
        loadThreshold();

        // Habilitar link fase 6
        const p6Link = document.querySelector('[data-phase="6"]');
        if (p6Link) p6Link.classList.remove('disabled');

        // --- PHASE 7 LOGIC ---
        const analyzeArchetypeBtn = document.getElementById('analyze-archetype-btn');

        if (analyzeArchetypeBtn) {
            analyzeArchetypeBtn.onclick = async () => {
                analyzeArchetypeBtn.classList.add('loading');
                analyzeArchetypeBtn.disabled = true;
                const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';

                try {
                    const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/analyze/archetype`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: mode })
                    });
                    const data = await res.json();
                    if (data.error) alert(data.error);
                    else loadArchetype();
                } catch (e) {
                    alert('Error: ' + e.message);
                } finally {
                    analyzeArchetypeBtn.classList.remove('loading');
                    analyzeArchetypeBtn.disabled = false;
                }
            };
        }

        function loadArchetype() {
            fetch(`/api/cases/${CURRENT_CASE_ID}/archetype`)
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('archetype-container');
                    if (!data || !container) return;

                    container.classList.remove('hidden');
                    document.getElementById('arch-name').textContent = data.archetype_name;
                    document.getElementById('arch-fit').textContent = data.fit_score;
                    document.getElementById('arch-desc').textContent = data.description;

                    const traitsContainer = document.getElementById('arch-traits');
                    traitsContainer.innerHTML = '';
                    if (data.key_traits && Array.isArray(data.key_traits)) {
                        data.key_traits.forEach(trait => {
                            const span = document.createElement('span');
                            span.className = 'trait-tag';
                            span.textContent = trait;
                            traitsContainer.appendChild(span);
                        });
                    }
                })
                .catch(e => console.error("Error loading archetype:", e));
        }

        // Cargar datos iniciales
        loadArchetype();

        // Habilitar link fase 7
        const p7Link = document.querySelector('[data-phase="7"]');
        if (p7Link) p7Link.classList.remove('disabled');

    } // End initCaseView
});
