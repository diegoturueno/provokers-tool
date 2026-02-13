// --- GLOBAL STATE ---
let CURRENT_PROJECT_ID = null;

// --- NAVIGATION HANDLERS (GLOBAL) ---
window.switchPhase = function (phaseId) {
    console.log("Switching to phase:", phaseId);
    try {
        document.querySelectorAll('section[id^="phase-"]').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.phase-link').forEach(el => el.classList.remove('active'));

        const target = document.getElementById('phase-' + phaseId + '-view');
        if (target) target.classList.remove('hidden');
        else {
            const altTarget = document.getElementById('phase-' + parseInt(phaseId) + '-view');
            if (altTarget) altTarget.classList.remove('hidden');
        }

        const link = document.querySelector(`.phase-link[data-phase="${phaseId}"]`);
        if (link) link.classList.add('active');

        const titles = { 0: 'Contexto', 1: 'Inputs', 2: 'Patrones', 3: 'Ejes', 4: 'Dimensiones', 5: 'Tensiones', 6: 'Diagnóstico', 7: 'Arquetipo', 8: 'Reporte' };
        const statusSpan = document.querySelector('.case-status');
        if (statusSpan) statusSpan.textContent = `Fase ${phaseId}: ${titles[phaseId] || ''}`;

    } catch (e) {
        console.error("Error switching phase:", e);
        alert("Error al cambiar de fase: " + e.message);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    try {
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
});

// --- DASHBOARD: PROJECTS LOGIC ---
function initDashboard() {
    const projectsSection = document.getElementById('projects-section');
    const projectDetailSection = document.getElementById('project-detail-section');
    const projectsGrid = document.getElementById('projects-grid');

    // Elements for Project Creation
    const newProjectBtn = document.getElementById('new-project-btn');
    const newProjectModal = document.getElementById('new-project-modal');
    const closeProjectModal = document.getElementById('close-project-modal');
    const newProjectForm = document.getElementById('new-project-form');

    // Elements for Project Detail
    const backToProjectsBtn = document.getElementById('back-to-projects');
    const currentProjectTitle = document.getElementById('current-project-title');
    const casesGrid = document.getElementById('cases-grid');
    const deleteProjectBtn = document.getElementById('delete-project-btn');

    // Load Projects Initial
    loadProjects();

    function loadProjects() {
        projectsGrid.innerHTML = '<div class="loading-spinner">Cargando proyectos...</div>';

        fetch('/api/projects')
            .then(res => res.json())
            .then(projects => {
                projectsGrid.innerHTML = '';
                if (projects.length === 0) {
                    projectsGrid.innerHTML = '<div style="color:var(--text-secondary); grid-column:1/-1; text-align:center;">No hay proyectos. Crea uno nuevo para empezar.</div>';
                    return;
                }

                projects.forEach(p => {
                    const card = document.createElement('div');
                    card.className = 'case-card'; // Reuse case-card style
                    card.style.borderLeft = '4px solid var(--primary)'; // Distinguish slightly

                    card.innerHTML = `
                        <div class="card-header">
                            <h3>${p.name}</h3>
                            <span style="font-size:0.8rem; color:var(--text-secondary);">${p.case_count || 0} Casos</span>
                        </div>
                        <p>${p.description || 'Sin descripción'}</p>
                        <div class="case-meta">
                            <span>Creado: ${new Date(p.created_at).toLocaleDateString()}</span>
                        </div>
                    `;

                    card.onclick = () => openProject(p);
                    projectsGrid.appendChild(card);
                });
            })
            .catch(err => {
                console.error(err);
                projectsGrid.innerHTML = '<div style="color:red">Error al cargar proyectos.</div>';
            });
    }

    function openProject(project) {
        CURRENT_PROJECT_ID = project.id;

        // UI Switch
        projectsSection.classList.add('hidden');
        projectDetailSection.classList.remove('hidden');

        // Setup Header
        currentProjectTitle.textContent = project.name;

        // Load Cases for this Project
        loadCases(project.id);
    }

    function loadCases(projectId) {
        casesGrid.innerHTML = '<div class="loading-spinner">Cargando casos...</div>';

        fetch(`/api/projects/${projectId}`)
            .then(res => res.json())
            .then(data => {
                const cases = data.cases;
                casesGrid.innerHTML = '';

                if (cases.length === 0) {
                    casesGrid.innerHTML = '<div style="color:var(--text-secondary); grid-column:1/-1; text-align:center;">Esta carpeta está vacía. Crea un caso nuevo.</div>';
                    return;
                }

                cases.forEach(c => {
                    const card = document.createElement('div');
                    card.className = 'case-card';
                    card.innerHTML = `
                        <div class="card-header">
                            <h3>${c.identifier}</h3>
                            <button class="delete-btn" title="Eliminar caso" onclick="event.stopPropagation(); deleteCase(${c.id})">🗑️</button>
                        </div>
                        <p>${c.description || 'Sin descripción'}</p>
                        <div class="case-meta">
                            <span>${new Date(c.created_at).toLocaleDateString()}</span>
                            <span style="color: var(--success)">Activo</span>
                        </div>
                    `;
                    card.onclick = () => window.location.href = `/case/${c.id}`;
                    casesGrid.appendChild(card);
                });
            })
            .catch(err => {
                console.error(err);
                casesGrid.innerHTML = '<div style="color:red">Error al cargar casos.</div>';
            });
    }

    // --- EVENTS ---

    // 1. Project Creation
    if (newProjectBtn) newProjectBtn.onclick = () => newProjectModal.style.display = "block";
    if (closeProjectModal) closeProjectModal.onclick = () => newProjectModal.style.display = "none";

    if (newProjectForm) newProjectForm.onsubmit = async (e) => {
        e.preventDefault();
        const name = document.getElementById('project-name').value;
        const description = document.getElementById('project-description').value;

        try {
            const res = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description })
            });

            if (res.ok) {
                newProjectModal.style.display = "none";
                newProjectForm.reset();
                loadProjects();
            } else {
                const d = await res.json();
                alert(d.error);
            }
        } catch (err) {
            alert('Error al crear proyecto: ' + err.message);
        }
    };

    // 2. Navigation Back
    if (backToProjectsBtn) backToProjectsBtn.onclick = () => {
        projectDetailSection.classList.add('hidden');
        projectsSection.classList.remove('hidden');
        CURRENT_PROJECT_ID = null;
        loadProjects(); // Refresh list to update counts
    };

    // 3. Delete Project
    if (deleteProjectBtn) deleteProjectBtn.onclick = async () => {
        if (!confirm('¿Estás SEGURO de eliminar este proyecto y TODOS sus casos? Esta acción es irreversible.')) return;

        try {
            const res = await fetch(`/api/projects/${CURRENT_PROJECT_ID}`, { method: 'DELETE' });
            if (res.ok) {
                alert('Proyecto eliminado.');
                backToProjectsBtn.click();
            } else {
                alert('Error al eliminar proyecto.');
            }
        } catch (err) {
            alert('Error de conexión: ' + err.message);
        }
    };

    // 4. Case Creation (Now Contextual)
    const newCaseBtn = document.getElementById('new-case-btn');
    const newCaseModal = document.getElementById('new-case-modal');
    const closeCaseModal = document.getElementById('close-case-modal');
    const newCaseForm = document.getElementById('new-case-form');

    if (newCaseBtn) newCaseBtn.onclick = () => newCaseModal.style.display = "block";
    if (closeCaseModal) closeCaseModal.onclick = () => newCaseModal.style.display = "none";

    if (newCaseForm) newCaseForm.onsubmit = async (e) => {
        e.preventDefault();
        const identifier = document.getElementById('case-identifier').value;
        const description = document.getElementById('case-description').value;
        // IMPORTANT: Use CURRENT_PROJECT_ID
        if (!CURRENT_PROJECT_ID) {
            alert("Error: No hay proyecto seleccionado.");
            return;
        }

        try {
            const res = await fetch('/api/cases', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    identifier,
                    description,
                    project_id: CURRENT_PROJECT_ID
                })
            });

            if (res.ok) {
                newCaseModal.style.display = "none";
                newCaseForm.reset();
                loadCases(CURRENT_PROJECT_ID); // Reload cases, stay in project view
            } else {
                const d = await res.json();
                alert(d.error);
            }
        } catch (err) {
            alert('Error al crear caso: ' + err.message);
        }
    };

    window.onclick = (event) => {
        if (event.target == newProjectModal) newProjectModal.style.display = "none";
        if (event.target == newCaseModal) newCaseModal.style.display = "none";
    };

    // 5. Delete Case
    window.deleteCase = async function (id) {
        if (!confirm('¿Estás seguro de que quieres eliminar este caso? Esta acción no se puede deshacer.')) {
            return;
        }

        try {
            const res = await fetch(`/api/cases/${id}`, { method: 'DELETE' });
            if (res.ok) {
                loadCases(CURRENT_PROJECT_ID); // Reload list in context
            } else {
                const data = await res.json();
                alert('Error: ' + (data.error || 'No se pudo eliminar'));
            }
        } catch (e) {
            alert('Error de conexión: ' + e.message);
        }
    };

    // 6. PROJECT REPORT LOGIC
    const generateReportBtn = document.getElementById('generate-report-btn');
    const projectReportSection = document.getElementById('project-report-section');
    const backToDetailBtn = document.getElementById('back-to-project-detail');
    const aiAnalysisDiv = document.getElementById('project-ai-analysis');
    const aiModeSelect = document.getElementById('project-ai-mode');

    // Back Button
    if (backToDetailBtn) backToDetailBtn.onclick = () => {
        projectReportSection.classList.add('hidden');
        projectDetailSection.classList.remove('hidden');
    };

    // Generate Button
    if (generateReportBtn) generateReportBtn.onclick = async () => {
        if (!CURRENT_PROJECT_ID) return;

        // UI Switch
        projectDetailSection.classList.add('hidden');
        projectReportSection.classList.remove('hidden');

        aiAnalysisDiv.innerHTML = '<div class="loading-spinner">Generando reporte con IA... (Esto puede tardar unos segundos)</div>';

        const mode = aiModeSelect ? aiModeSelect.value : 'local';

        try {
            const res = await fetch(`/api/projects/${CURRENT_PROJECT_ID}/generate_report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode })
            });

            if (res.ok) {
                const data = await res.json();
                renderProjectReport(data);
            } else {
                const err = await res.json();
                aiAnalysisDiv.innerHTML = `<div style="color:red">Error: ${err.error}</div>`;
            }
        } catch (e) {
            aiAnalysisDiv.innerHTML = `<div style="color:red">Error de conexión: ${e.message}</div>`;
        }
    };

    function renderProjectReport(data) {
        // 1. Text Analysis (Markdown)
        // Check if showdon is loaded
        if (typeof showdown !== 'undefined') {
            const converter = new showdown.Converter();
            aiAnalysisDiv.innerHTML = converter.makeHtml(data.ai_analysis);
        } else {
            aiAnalysisDiv.innerHTML = `<pre>${data.ai_analysis}</pre>`;
        }

        // 2. Archetype Chart
        renderArchetypeChart(data.stats.archetype_distribution);

        // 3. Radar Chart
        renderGroupRadarChart(data.stats.axis_averages);
    }

    function renderArchetypeChart(distribution) {
        const ctx = document.getElementById('archetypePieChart');
        if (!ctx) return;

        if (window.projectArchetypeChart) window.projectArchetypeChart.destroy();

        const labels = Object.keys(distribution);
        const values = Object.values(distribution);

        // Colors palette
        const colors = ['#7f5af0', '#2cb67d', '#ff8906', '#e53170', '#fffffe', '#94a1b2'];

        window.projectArchetypeChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#fffffe' } }
                }
            }
        });
    }

    function renderGroupRadarChart(averages) {
        const ctx = document.getElementById('groupRadarChart');
        if (!ctx) return;

        if (window.projectRadarChart) window.projectRadarChart.destroy();

        const labels = ["Generación", "Relación con el cambio feminista", "Modelo de masculinidad", "Apertura a diversidad sexual y familiar", "Manejo emocional y cuidado de sí", "Presión social / falta de referentes"];

        // Map average keys to labels (fuzzy match)
        const dataPoints = labels.map(label => {
            // Find key that matches
            const key = Object.keys(averages).find(k => label.toLowerCase().includes(k.toLowerCase()) || k.toLowerCase().includes(label.toLowerCase()));
            return key ? averages[key] : 0;
        });

        window.projectRadarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ["Generación", "Feminismo", "Modelo Masc.", "Diversidad", "Emociones", "Presión Social"],
                datasets: [{
                    label: 'Promedio del Grupo',
                    data: dataPoints,
                    fill: true,
                    backgroundColor: 'rgba(44, 182, 125, 0.2)', // Greenish
                    borderColor: '#2cb67d',
                    pointBackgroundColor: '#2cb67d',
                    pointBorderColor: '#fff'
                }]
            },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#94a1b2', font: { size: 10 } },
                        ticks: { display: false } // Hide numbers for cleaner look
                    }
                },
                plugins: {
                    legend: { labels: { color: '#fffffe' } }
                }
            }
        });
    }
}

// --- CASE VIEW LOGIC (Unchanged mostly, just ensure it works) ---
function initCaseView() {
    // We can assume CURRENT_CASE_ID is available globally via template injection if needed,
    // but typically it is extracted from URL in pure SPA or template.
    // In this app, CURRENT_CASE_ID seems to be injected by template in case_view.html `const CURRENT_CASE_ID = {{ case_id }};`

    // ... Copying existing logic for Case View ...
    const inputsList = document.getElementById('inputs-list');
    const patternsList = document.getElementById('patterns-list');
    const addBtn = document.getElementById('add-input-btn');
    const analyzeBtn = document.getElementById('analyze-patterns-btn');
    const formContainer = document.getElementById('input-form-container');
    const cancelBtn = document.getElementById('cancel-input-btn');
    const form = document.getElementById('new-input-form');
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
    if (typeof CURRENT_CASE_ID !== 'undefined') {
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
        loadAxesAssignments();
        loadDimensions();
        loadTensions();
        loadThreshold();
        loadArchetype();
        loadReport();
    }

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
        if (!inputsList) return;
        fetch(`/api/cases/${CURRENT_CASE_ID}/inputs`)
            .then(res => res.json())
            .then(inputs => {
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

    function setLoading(btn, isLoading, loadingText = "Procesando...") {
        if (!btn) return;
        const textSpan = btn.querySelector('.btn-text');

        if (isLoading) {
            btn.classList.add('loading');
            btn.disabled = true;
            if (textSpan) {
                btn.dataset.originalText = textSpan.textContent;
                textSpan.textContent = loadingText;
            }
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
            if (textSpan && btn.dataset.originalText) {
                textSpan.textContent = btn.dataset.originalText;
            }
        }
    }

    // --- PHASE 2 LOGIC ---
    if (analyzeBtn) {
        analyzeBtn.onclick = async () => {
            setLoading(analyzeBtn, true, "Detectando Patrones...");
            const mode = (cloudToggle && cloudToggle.checked) ? 'cloud' : 'local';

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
            } finally {
                setLoading(analyzeBtn, false);
            }
        };
    }

    function loadPatterns() {
        if (!patternsList) return;
        fetch(`/api/cases/${CURRENT_CASE_ID}/patterns`)
            .then(res => res.json())
            .then(patterns => {
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
            setLoading(autoLinkBtn, true, "Vinculando Ejes...");
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
                setLoading(autoLinkBtn, false);
            }
        };
    }

    function loadAxesAssignments() {
        if (!document.querySelector('.axis-column')) return;
        fetch(`/api/cases/${CURRENT_CASE_ID}/axis_assignments`)
            .then(res => res.json())
            .then(assigns => {
                document.querySelectorAll('.axis-column .axis-content').forEach(el => el.innerHTML = '');
                assigns.forEach(a => {
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
                // Enable Phase 4 Link
                const pLink = document.querySelector('[data-phase="4"]');
                if (pLink) pLink.classList.remove('disabled');
            });
    }

    // --- PHASE 4 LOGIC ---
    const analyzeDimBtn = document.getElementById('analyze-dimensions-btn');
    if (analyzeDimBtn) {
        analyzeDimBtn.onclick = async () => {
            setLoading(analyzeDimBtn, true, "Clasificando...");
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
            } catch (e) { alert(e.message); }
            finally { setLoading(analyzeDimBtn, false); }
        };
    }

    function loadDimensions() {
        const container = document.getElementById('dimensions-container');
        if (!container) return;

        fetch(`/api/cases/${CURRENT_CASE_ID}/axis_states`)
            .then(res => res.json())
            .then(states => {
                container.innerHTML = '';
                if (states.length === 0) {
                    container.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--text-secondary)">No hay dimensiones analizadas.</div>';
                    return;
                }
                states.forEach(s => {
                    const statusClass = `status-${s.status.replace(/\\s+/g, '-')}`;
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
                const pLink = document.querySelector('[data-phase="5"]');
                if (pLink) pLink.classList.remove('disabled');
            });
    }

    // --- PHASE 5 LOGIC ---
    const analyzeTensionBtn = document.getElementById('analyze-tensions-btn');
    if (analyzeTensionBtn) {
        analyzeTensionBtn.onclick = async () => {
            setLoading(analyzeTensionBtn, true, "Buscando Tensiones...");
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
            } catch (e) { alert(e.message); }
            finally { setLoading(analyzeTensionBtn, false); }
        };
    }

    function loadTensions() {
        const container = document.getElementById('tensions-container');
        if (!container) return;

        fetch(`/api/cases/${CURRENT_CASE_ID}/tensions`)
            .then(res => res.json())
            .then(tensions => {
                container.innerHTML = '';
                if (tensions.length === 0) {
                    container.innerHTML = '<div style="text-align:center; color:var(--text-secondary)">No hay tensiones detectadas.</div>';
                    return;
                }
                tensions.forEach(t => {
                    let severityClass = 'baja';
                    if (t.severity.includes('Alta')) severityClass = 'alta';
                    else if (t.severity.includes('Media')) severityClass = 'media';

                    const div = document.createElement('div');
                    div.className = 'tension-card';
                    div.innerHTML = `
                        <div class="tension-header">
                            <span class="tension-type">${t.type}</span>
                            <span class="tension-severity severity-${severityClass}">${t.severity}</span>
                        </div>
                        <div class="tension-desc">${t.description}</div>
                        <div class="tension-axes">
                            <strong>Ejes en conflicto:</strong> ${t.axes_involved.join(', ')}
                        </div>
                    `;
                    container.appendChild(div);
                });
                const pLink = document.querySelector('[data-phase="6"]');
                if (pLink) pLink.classList.remove('disabled');
            });
    }

    // --- PHASE 6 LOGIC ---
    const analyzeThresholdBtn = document.getElementById('analyze-threshold-btn');
    if (analyzeThresholdBtn) {
        analyzeThresholdBtn.onclick = async () => {
            setLoading(analyzeThresholdBtn, true, "Evaluando...");
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
            } catch (e) { alert(e.message); }
            finally { setLoading(analyzeThresholdBtn, false); }
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

                const circle = document.querySelector('.score-circle');
                if (data.score >= 61) circle.style.borderColor = 'var(--success)';
                else if (data.score >= 41) circle.style.borderColor = '#ffce56';
                else circle.style.borderColor = 'var(--danger)';

                const pLink = document.querySelector('[data-phase="7"]');
                if (pLink) pLink.classList.remove('disabled');
            });
    }

    // --- PHASE 7 LOGIC ---
    const analyzeArchetypeBtn = document.getElementById('analyze-archetype-btn');
    if (analyzeArchetypeBtn) {
        analyzeArchetypeBtn.onclick = async () => {
            setLoading(analyzeArchetypeBtn, true, "Definiendo Arquetipo...");
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
            } catch (e) { alert(e.message); }
            finally { setLoading(analyzeArchetypeBtn, false); }
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
                const pLink = document.querySelector('[data-phase="8"]');
                if (pLink) pLink.classList.remove('disabled');
            });
    }

    // --- PHASE 8 LOGIC ---
    function loadReport() {
        fetch(`/api/cases/${CURRENT_CASE_ID}/report`)
            .then(res => res.json())
            .then(data => {
                if (data.error || !data) return;

                // Header
                document.getElementById('rep-case-id').textContent = data.case_info.id || CURRENT_CASE_ID;
                document.getElementById('rep-date').textContent = new Date().toLocaleDateString();

                // 1. Archetype
                if (data.archetype) {
                    document.querySelector('.rep-arch-name').textContent = data.archetype.archetype_name;
                    document.querySelector('.rep-arch-desc').textContent = data.archetype.description;
                    document.getElementById('rep-arch-fit').textContent = data.archetype.fit_score || '--';
                }

                // 2. Threshold
                if (data.threshold) {
                    document.getElementById('rep-score').textContent = data.threshold.score;
                    document.getElementById('rep-status').textContent = data.threshold.status;
                }

                // Radar Chart Logic (simplified for brevity, assume similar to before)
                renderRadarChart(data.axes);
            });
    }

    function renderRadarChart(axes) {
        if (!axes) return;
        const ctx = document.getElementById('axesRadarChart');
        if (!ctx) return;

        // ... (Chart.js logic reused from previous implementation) ...
        // For brevity in this update, assume standard chart logic
        // Only ensuring it doesn't break if Chart is missing
        if (typeof Chart === 'undefined') return;

        // ... (Simplified Chart setup) ...
        // Re-implement if strictly needed, but assuming user didn't ask to change chart behavior.
        // Copying the vital logic:
        if (window.myRadarChart) window.myRadarChart.destroy();

        const axisLabels = ["Generación", "Relación con el cambio feminista", "Modelo de masculinidad", "Apertura a diversidad sexual y familiar", "Manejo emocional y cuidado de sí", "Presión social / falta de referentes"];

        const getScore = (status, value) => {
            const s = (status || "").toLowerCase();
            if (s.includes("definido") && !s.includes("no")) return 90;
            if (s.includes("tensión") || s.includes("tension")) return 50;
            if (s.includes("parcial")) return 60;
            if (s.includes("no definido")) return 30;
            return 40;
        };

        const dataPoints = axisLabels.map(label => {
            const found = axes.find(a => a.axis_name.includes(label) || label.includes(a.axis_name));
            return found ? getScore(found.status, found.value) : 20;
        });

        window.myRadarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ["Generación", "Feminismo", "Modelo Masc.", "Diversidad", "Emociones", "Presión Social"],
                datasets: [{
                    label: 'Perfil de Masculinidad',
                    data: dataPoints,
                    fill: true,
                    backgroundColor: 'rgba(127, 90, 240, 0.2)',
                    borderColor: '#7f5af0',
                    pointBackgroundColor: '#7f5af0'
                }]
            },
            options: { elements: { line: { borderWidth: 3 } } }
        });
    }
}
