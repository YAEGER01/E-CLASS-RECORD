// Global isolated namespace with safe utilities so other code can rely on stable helpers
window.GradeBuilderV2 = window.GradeBuilderV2 || {};
(function (GB) {
  // safeFetch: returns Response or null on network/error (never throws)
  GB.safeFetch = async function (url, opts) {
    try {
      const res = await fetch(url, opts);
      if (!res.ok) {
        // return null to signal non-ok
        console.warn('GradeBuilderV2.safeFetch non-ok', url, res.status);
        return null;
      }
      return res;
    } catch (e) {
      console.warn('GradeBuilderV2.safeFetch failed', url, e);
      return null;
    }
  };

  GB.getClasses = () => window._classes || [];
  GB.getStructures = () => window._savedStructures || [];
  GB.getInstructor = () => window._instructor || null;

  // safe swal/toast
  GB._swal = window.Swal || null;
  GB.showToast = function (type, message, timer = 2000) {
    if (GB._swal) {
      GB._swal.fire({ toast: true, position: 'top-end', icon: type, title: message, showConfirmButton: false, timer });
      return;
    }
    const statusEl = document.getElementById('save-status');
    if (statusEl) statusEl.textContent = message;
    else console.log(`${type}: ${message}`);
  };

  GB.showConfirm = async function (title, text, callback) {
    if (GB._swal) {
      const isDelete = /delete|remove/i.test(title + ' ' + text);
      const res = await GB._swal.fire({ title: title || 'Confirm', text: text || '', icon: isDelete ? 'warning' : 'question', showCancelButton: true, confirmButtonText: isDelete ? 'Delete' : 'Confirm', confirmButtonColor: isDelete ? '#d33' : undefined });
      if (res && res.isConfirmed) return callback && callback();
      return;
    }
    if (confirm(text || title || 'Confirm?')) return callback && callback();
  };

})(window.GradeBuilderV2);

document.addEventListener('DOMContentLoaded', () => {
  // Predefined subcategory options by category (LABORATORY/LECTURE)
  const SUBCATEGORY_OPTIONS = {
    LABORATORY: [
      'LAB PARTICIPATION',
      'LAB HOMEWORK',
      'LAB EXERCISE',
      'PRELIM LAB EXAM',
      'MIDTERM LAB EXAM',
      'FINAL LAB EXAM'
    ],
    LECTURE: [
      'ATTENDANCE',
      'ATTITUDE',
      'RECITATION',
      'HOMEWORK',
      'QUIZ',
      'PROJECT',
      'PRELIM EXAM',
      'MIDTERM EXAM',
      'FINAL EXAM'
    ]
  };
  const labList = document.getElementById('lab-list');
  const lectureList = document.getElementById('lecture-list');
  const labAdd = document.getElementById('lab-add');
  const lectureAdd = document.getElementById('lecture-add');
  const subTemplate = document.getElementById('sub-template');
  const labSum = document.getElementById('lab-sum');
  const lectureSum = document.getElementById('lecture-sum');
  const saveBtn = document.getElementById('save-btn');
  const status = document.getElementById('save-status');
  const classSelect = document.getElementById('class-select');
  const structureName = document.getElementById('structure-name');
  const structureListContainer = document.getElementById('structure-list');
  let selectedStructureId = null;
  // editing/read-only state
  let editingStructureId = null; // when set, Save will update this id
  let readOnlyMode = false; // when true, inputs are disabled and saving is blocked
  // snapshot of the last-loaded structure (used by Cancel Edit)
  let lastLoadedSnapshot = null;
  // helper: use SweetAlert2 for confirmations and toasts
  function showToast(type, message, timer = 2000) {
    if (window.Swal) {
      Swal.fire({
        toast: true,
        position: 'top-end',
        icon: type,
        title: message,
        showConfirmButton: false,
        timer
      });
    } else {
      // fallback to status text (safe-guarded)
      if (status) status.textContent = message;
      else console.log(`${type}: ${message}`);
    }
  }

  // Helper to find a class object by id
  function getClassById(cid) {
    try {
      const classes = window._classes || [];
      return classes.find(c => String(c.class_id || c.id) === String(cid)) || null;
    } catch (e) { return null; }
  }

  // Render structure content into a container element
  function renderStructureContent(container, structure) {
    container.innerHTML = '';
    if (!structure || typeof structure !== 'object') {
      container.textContent = 'No structure';
      return;
    }
    ['LABORATORY', 'LECTURE'].forEach(catKey => {
      const list = structure[catKey] || [];
      const h = document.createElement('h4'); h.textContent = catKey; container.appendChild(h);
      if (!list.length) {
        const p = document.createElement('div'); p.className = 'muted'; p.textContent = '(none)'; container.appendChild(p); return;
      }
      const ul = document.createElement('ul'); ul.className = 'preview-sublist';
      list.forEach(sub => {
        const li = document.createElement('li');
        const name = document.createElement('strong'); name.textContent = sub.name || 'Unnamed';
        const wt = document.createElement('span'); wt.textContent = ` — ${parseFloat(sub.weight||0).toFixed(2)}%`;
        li.appendChild(name); li.appendChild(wt);
        ul.appendChild(li);
      });
      container.appendChild(ul);
    });
  }

  // Enable/disable editing of the main editor region
  function setReadOnlyMode(flag) {
    readOnlyMode = !!flag;
    const inputs = Array.from(document.querySelectorAll('#lab-list [data-field], #lecture-list [data-field]'));
    inputs.forEach(inp => { inp.disabled = readOnlyMode; });
    // hide/show remove buttons
    Array.from(document.querySelectorAll('.sub-item [data-action="remove"]')).forEach(btn => {
      btn.style.display = readOnlyMode ? 'none' : '';
    });
    // disable add buttons
    if (labAdd) labAdd.disabled = readOnlyMode;
    if (lectureAdd) lectureAdd.disabled = readOnlyMode;
    // disable header inputs if present
    if (structureName) structureName.disabled = readOnlyMode;
    if (classSelect) classSelect.disabled = readOnlyMode;
    // disable clear/cancel buttons
    const clearFieldsBtn = document.querySelector('.clear-fields');
    const cancelEditBtn = document.querySelector('.cancel-edit');
    if (clearFieldsBtn) clearFieldsBtn.disabled = readOnlyMode;
    if (cancelEditBtn) cancelEditBtn.disabled = readOnlyMode;
    // toggle read-only CSS class on the main container for high-contrast styles
    const mainContent = document.getElementById('main-content');
    if (mainContent) mainContent.classList.toggle('read-only', readOnlyMode);
    // disable save buttons via updateSaveEnabled guard
    updateSaveEnabled();
  }

  // Update the preview box for the selected structure id (or clear if null)
  function updatePreview(structureId) {
    const previewBox = document.getElementById('preview-box');
    if (!previewBox) return;
    if (!structureId) {
      previewBox.innerHTML = 'No preview yet.';
      return;
    }
    const s = (window._savedStructures || []).find(x => String(x.id) === String(structureId));
    if (!s) { previewBox.innerHTML = 'Structure not found.'; return; }
    // build preview
    const classObj = getClassById(s.class_id);
    const instructor = window._instructor || {};
    const container = document.createElement('div');
    container.className = 'preview-details';
    const title = document.createElement('h3'); title.textContent = s.structure_name || '(unnamed)'; container.appendChild(title);
    const meta = document.createElement('div'); meta.className = 'preview-meta';
    const cls = document.createElement('div'); cls.innerHTML = `<strong>Class:</strong> ${escapeHtml(classObj ? (classObj.course + (classObj.section ? (' - ' + classObj.section) : '')) : String(s.class_id))}`;
    const prof = document.createElement('div'); prof.innerHTML = `<strong>Created by:</strong> ${escapeHtml((instructor && (instructor.name || '')) || '')} ${escapeHtml((instructor && instructor.email) ? ('‹' + instructor.email + '›') : '')}`;
    meta.appendChild(cls); meta.appendChild(prof); container.appendChild(meta);
    // structure content
    const structDiv = document.createElement('div'); structDiv.className = 'preview-structure';
    try {
      const structureObj = JSON.parse(s.structure_json || '{}');
      renderStructureContent(structDiv, structureObj);
    } catch (e) {
      structDiv.textContent = 'Invalid structure JSON';
    }
    container.appendChild(structDiv);
    // place into preview box
    previewBox.innerHTML = '';
    previewBox.appendChild(container);
  }

  /* Guided tips: show contextual floating tips for core functions
     - Uses localStorage key 'gb_v2_tips_last_shown' to remember last shown timestamp (ms)
     - Only shows if last shown is older than tipsConfig.thresholdHours
     - Shows a sequence of tips (each for tipsConfig.displayMs) anchored to page elements if present
  */
  const tipsConfig = {
    storageKey: 'gb_v2_tips_last_shown',
    thresholdHours: 6, // show tips again only if user returns after 6 hours
    displayMs: 3500,
    gapMs: 500
  };

  const tips = [
    { sel: '#new-structure-btn', text: 'Create a new grade structure here. Click to start a fresh template.' },
    { sel: '#lab-add', text: 'Add laboratory subcategories. Weights must total 100%.' },
    { sel: '#lecture-add', text: 'Add lecture subcategories. Weights must total 100%.' },
    { sel: '#save-btn-bottom', text: 'Save the structure. Enabled when either category totals 100%.' },
    { sel: '#preview-btn', text: 'Preview the structure JSON before saving.' }
  ];

  function createTipEl(text) {
    const el = document.createElement('div');
    el.className = 'gb-tip';
    el.setAttribute('role', 'dialog');
    el.innerHTML = `<div class="gb-tip-arrow"></div><div class="gb-tip-body">${escapeHtml(text)}<button class="gb-tip-close" aria-label="Close">×</button></div>`;
    // close handler
    el.querySelector('.gb-tip-close').addEventListener('click', () => { el.remove(); });
    document.body.appendChild(el);
    return el;
  }

  function positionTipEl(el, target) {
    if (!el || !target) return;
    const trgRect = target.getBoundingClientRect();
    const bodyRect = document.body.getBoundingClientRect();
    // place tip above the element if there's room, otherwise below
    const tipW = 260; // fixed width
    el.style.width = tipW + 'px';
    const spaceAbove = trgRect.top;
    const spaceBelow = window.innerHeight - trgRect.bottom;
    const top = (spaceAbove > 120) ? (window.scrollY + trgRect.top - 12 - el.offsetHeight) : (window.scrollY + trgRect.bottom + 12);
    // center horizontally over target where possible
    let left = window.scrollX + trgRect.left + (trgRect.width / 2) - (tipW / 2);
    left = Math.max(8, Math.min(left, window.innerWidth - tipW - 8));
    el.style.position = 'absolute';
    el.style.top = top + 'px';
    el.style.left = left + 'px';
  }

  async function showTipsIfNeeded() {
    try {
      const last = parseInt(localStorage.getItem(tipsConfig.storageKey) || '0', 10) || 0;
      const ageMs = Date.now() - last;
      const thresholdMs = tipsConfig.thresholdHours * 3600 * 1000;
      if (last && ageMs < thresholdMs) return; // recently shown
      // show sequence of tips
      for (let i = 0; i < tips.length; i++) {
        const t = tips[i];
        const target = document.querySelector(t.sel);
        if (!target) continue; // skip if element absent
        const tipEl = createTipEl(t.text);
        // wait for it to be added to DOM to measure
        await new Promise(r => requestAnimationFrame(r));
        positionTipEl(tipEl, target);
        // fade in
        tipEl.classList.add('visible');
        await new Promise(r => setTimeout(r, tipsConfig.displayMs));
        tipEl.classList.remove('visible');
        tipEl.remove();
        await new Promise(r => setTimeout(r, tipsConfig.gapMs));
      }
      localStorage.setItem(tipsConfig.storageKey, String(Date.now()));
    } catch (e) { /* non-fatal */ console.warn('showTipsIfNeeded failed', e); }
  }

  // Run tips asynchronously after a short delay so page elements settle
  setTimeout(() => { try { showTipsIfNeeded(); } catch (e){console.warn(e);} }, 1200);

  function showConfirm(titleText, messageText, callback) {
    if (window.Swal) {
      const isDelete = /delete|remove/i.test(titleText || messageText || '');
      return Swal.fire({
        title: titleText || 'Confirm',
        text: messageText || '',
        icon: isDelete ? 'warning' : 'question',
        showCancelButton: true,
        confirmButtonText: isDelete ? 'Delete' : 'Confirm',
        confirmButtonColor: isDelete ? '#d33' : undefined
      }).then((res) => { if (res.isConfirmed) return callback && callback(); });
    }
    // fallback
    if (confirm(messageText || titleText || 'Confirm?')) return callback && callback();
  }

  // Safe HTML escaper for content placed into Swal html strings
  function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    const s = String(unsafe);
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
  }

  function createSub(type /* 'LABORATORY' | 'LECTURE' | undefined */, name = '', weight = '') {
    const frag = subTemplate.content.cloneNode(true);
    const el = frag.querySelector('.sub-item');
    const nameInput = el.querySelector('[data-field="name"]');
    // If a type is provided, replace the name input with a dropdown select of predefined options
    if (type && SUBCATEGORY_OPTIONS[type]) {
      const sel = document.createElement('select');
      sel.setAttribute('data-field', 'name');
      sel.className = 'subcategory-select';
      // Placeholder option
      const ph = document.createElement('option');
      ph.value = '';
      ph.textContent = '(select subcategory)';
      sel.appendChild(ph);
      // Add options
      SUBCATEGORY_OPTIONS[type].forEach(opt => {
        const o = document.createElement('option');
        o.value = opt;
        o.textContent = opt;
        sel.appendChild(o);
      });
      // Custom option
      const customOpt = document.createElement('option');
      customOpt.value = '__CUSTOM__';
      customOpt.textContent = 'Custom…';
      sel.appendChild(customOpt);

      if (name) sel.value = name;
      // If provided name isn't in the predefined list, inject it so it's selectable
      if (name && sel.value !== name) {
        const dyn = document.createElement('option');
        dyn.value = name;
        dyn.textContent = name;
        sel.insertBefore(dyn, customOpt); // add before custom option
        sel.value = name;
      }

      // When selecting Custom…, prompt for a name (Swal if available; fallback to prompt)
      sel.addEventListener('change', async () => {
        if (sel.value === '__CUSTOM__') {
          let customName = '';
          try {
            if (window.Swal) {
              const res = await Swal.fire({
                title: 'Custom subcategory name',
                input: 'text',
                inputPlaceholder: 'Enter name (e.g., Special Project)',
                showCancelButton: true,
                confirmButtonText: 'Use name'
              });
              if (res && res.isConfirmed) customName = (res.value || '').trim();
            } else {
              customName = (prompt('Enter custom subcategory name:') || '').trim();
            }
          } catch (_) { /* ignore */ }
          if (!customName) customName = 'Unnamed';
          // Insert the custom name as an option (before Custom…) and select it
          const exists = Array.from(sel.options).some(o => o.value === customName);
          if (!exists) {
            const dyn2 = document.createElement('option');
            dyn2.value = customName;
            dyn2.textContent = customName;
            sel.insertBefore(dyn2, customOpt);
          }
          sel.value = customName;
        }
      });
      nameInput.replaceWith(sel);
    } else {
      // fallback to free-text if no type provided
      nameInput.value = name;
    }
    el.querySelector('[data-field="weight"]').value = weight;
    el.querySelector('[data-action="remove"]').addEventListener('click', () => {
      el.remove(); updateSums();
    });
    // wire live input listener so sums update while typing
    const weightInput = el.querySelector('[data-field="weight"]');
    if (weightInput) {
      weightInput.addEventListener('input', () => { updateSums(); updateSaveEnabled(); });
    }
    return el;
  }

  function updateSums() {
    const labTotal = Array.from(labList.querySelectorAll('[data-field="weight"]')).reduce((s, inp) => s + (parseFloat(inp.value) || 0), 0);
    const lecTotal = Array.from(lectureList.querySelectorAll('[data-field="weight"]')).reduce((s, inp) => s + (parseFloat(inp.value) || 0), 0);
    labSum.textContent = `Total: ${labTotal.toFixed(2)}%`;
    lectureSum.textContent = `Total: ${lecTotal.toFixed(2)}%`;
    return { labTotal, lecTotal };
  }

  labAdd.addEventListener('click', () => { labList.appendChild(createSub('LABORATORY')); updateSums(); });
  lectureAdd.addEventListener('click', () => { lectureList.appendChild(createSub('LECTURE')); updateSums(); });

  // Load classes and existing structures
  async function loadData() {
    try {
      // use safeFetch so network failure won't throw and break the script
      const res = await (window.GradeBuilderV2 && window.GradeBuilderV2.safeFetch ? window.GradeBuilderV2.safeFetch('/api/gradebuilder/data') : fetch('/api/gradebuilder/data').catch(()=>null));
      if (!res) {
        // ensure globals exist so other code doesn't break
        window._classes = window._classes || [];
        window._savedStructures = window._savedStructures || [];
        window._instructor = window._instructor || null;
        if (window.GradeBuilderV2 && window.GradeBuilderV2.showToast) window.GradeBuilderV2.showToast('error', 'Failed to load classes');
        // update UI state defensively
        updateSaveEnabled();
        return;
      }
      const data = await res.json();
      // store csrf token for subsequent POST/DELETE operations
      window.csrfToken = data.csrf_token || null;
      // cache classes so flows can work even if '#class-select' is not present
  // cache instructor info too for preview
  window._instructor = data.instructor || null;
      window._classes = data.classes || [];
      // If class_id is provided in the URL, preselect it (even if header select is commented out)
      try {
        const params = new URLSearchParams(window.location.search);
        const cid = params.get('class_id');
        if (cid && classSelect) {
          classSelect.value = String(cid);
        }
      } catch(_) {}
      if (classSelect) {
        classSelect.innerHTML = '<option value="">(select class)</option>';
        (data.classes || []).forEach(c => {
          const opt = document.createElement('option'); opt.value = c.class_id; opt.textContent = `${c.course} - ${c.section}`; classSelect.appendChild(opt);
        });
      }
      // Populate saved structures as clickable items
      // cache structures for quick lookup
      window._savedStructures = data.structures || [];
      if (structureListContainer) structureListContainer.innerHTML = '';
      // if there are no saved structures, show a helpful placeholder
      const structuresArr = data.structures || [];
      if (structuresArr.length === 0) {
        const noneItem = document.createElement('div');
        noneItem.className = 'structure-item placeholder';
        noneItem.textContent = '(none)';
        noneItem.dataset.id = '';
        if (structureListContainer) structureListContainer.appendChild(noneItem);
      }
      structuresArr.forEach(s => {
        const item = document.createElement('div');
        item.className = 'structure-item';
        item.tabIndex = 0;
        item.setAttribute('role', 'button');
        item.dataset.id = s.id;

        const label = document.createElement('div');
        label.className = 'structure-label';
        label.textContent = `${s.structure_name} (${s.class_id})`;
        item.appendChild(label);

        const actions = document.createElement('div');
        actions.className = 'item-actions';

        const makeBtn = (txt, cls) => { const b = document.createElement('button'); b.className = cls || 'btn'; b.type = 'button'; b.textContent = txt; return b; };

        const loadBtn = makeBtn('Load', 'btn btn-secondary');
        const editBtn = makeBtn('Edit', 'btn btn-secondary');
        const dupBtn = makeBtn('Duplicate', 'btn');
        const histBtn = makeBtn('History', 'btn');
        const delBtn = makeBtn('Delete', 'btn btn-danger');

        // For small screens show a single 'Options' button that opens a modal with actions.
        // If SweetAlert2 is available, append an Options button that opens a modal containing the actions.
        if (window.Swal) {
          const optionsBtn = makeBtn('Options', 'btn btn-secondary options-btn');
          optionsBtn.type = 'button';
          optionsBtn.addEventListener('click', (ev) => {
            ev.stopPropagation();
            // Build modal HTML with unique ids to avoid collisions
            const idBase = `swal-opts-${s.id}`;
            const html = `
              <div style="display:flex;flex-direction:column;gap:8px;align-items:stretch;">
                <button id="${idBase}-load" class="swal-action btn btn-secondary">Load</button>
                <button id="${idBase}-edit" class="swal-action btn btn-secondary">Edit</button>
                <button id="${idBase}-dup" class="swal-action btn">Duplicate</button>
                <button id="${idBase}-hist" class="swal-action btn">History</button>
                <button id="${idBase}-del" class="swal-action btn btn-danger">Delete</button>
              </div>
            `;
            Swal.fire({ title: `${escapeHtml(s.structure_name)} — Options`, html, showCancelButton: true, showConfirmButton: false, didOpen: () => {
              // wire up buttons inside modal to reuse existing handlers
              const byId = (n) => document.getElementById(`${idBase}-${n}`);
              const bind = (btnEl, actionFn) => { if (btnEl) btnEl.addEventListener('click', async (e) => { e.stopPropagation(); await actionFn(); Swal.close(); }); };
              bind(byId('load'), async () => { await loadStructureReadOnlyById(s.id); });
              bind(byId('edit'), async () => { await loadStructureForEditById(s.id); });
              bind(byId('dup'), async () => {
                try {
                  const headers = { 'Content-Type': 'application/json' };
                  if (window.csrfToken) headers['X-CSRFToken'] = window.csrfToken;
                  const structure = JSON.parse(s.structure_json || '{}');
                  const payload = { class_id: s.class_id, structure_name: `${s.structure_name} (copy)`, structure_json: JSON.stringify(structure) };
                  const res = await fetch('/api/gradebuilder/save', { method: 'POST', headers, body: JSON.stringify(payload) });
                  const out = await res.json();
                  if (res.ok) { showToast('success', 'Duplicated'); await loadData(); }
                  else showToast('error', out.error || 'Duplicate failed');
                } catch (e) { showToast('error', 'Network error'); }
              });
              bind(byId('hist'), async () => {
                try {
                  const res = await fetch(`/api/gradebuilder/history/${s.id}`);
                  if (!res.ok) { showToast('error', 'History not available'); return; }
                  const hist = await res.json();
                  Swal.fire({ title: 'History', html: `<pre style="text-align:left;white-space:pre-wrap;">${escapeHtml(JSON.stringify(hist, null, 2))}</pre>`, width: 700 });
                } catch (e) { showToast('error', 'Failed to fetch history'); }
              });
              bind(byId('del'), async () => {
                await showConfirm('Delete structure', `Delete "${s.structure_name}"? This will remove version history.`, async () => {
                  try {
                    const headers = {};
                    if (window.csrfToken) headers['X-CSRFToken'] = window.csrfToken;
                    const res = await fetch(`/api/gradebuilder/delete/${s.id}`, { method: 'DELETE', headers });
                    const out = await res.json();
                    if (res.ok) { showToast('success', out.message || 'Deleted'); await loadData(); }
                    else showToast('error', out.error || 'Delete failed');
                  } catch (e) { showToast('error', 'Network error'); }
                });
              });
            }});
          });
          actions.appendChild(optionsBtn);
        } else {
          // fallback: when Swal not available keep inline action buttons
          actions.appendChild(loadBtn);
          actions.appendChild(editBtn);
          actions.appendChild(dupBtn);
          actions.appendChild(histBtn);
          actions.appendChild(delBtn);
        }
        item.appendChild(actions);

        // selection when clicking label or item background
        const selectItem = () => {
          selectedStructureId = String(s.id);
          if (structureListContainer) {
            Array.from(structureListContainer.querySelectorAll('.structure-item')).forEach(el => el.classList.toggle('selected', el.dataset.id === selectedStructureId));
          }
          updatePreview(selectedStructureId);
        };
        // clicking anywhere on the item (except action buttons) should select it
        item.addEventListener('click', (ev) => {
          // if the click came from inside the actions area, ignore (buttons stopPropagation but double-guard here)
          if (ev.target && ev.target.closest && ev.target.closest('.item-actions')) return;
          selectItem();
        });
        item.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); selectItem(); } });

        // action handlers (stop propagation so they don't re-select)
        loadBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          showConfirm('Load structure', `Load \"${s.structure_name}\" into the editor (read-only)?`, async () => { await loadStructureReadOnlyById(s.id); });
        });
        editBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          showConfirm('Edit structure', `Edit \"${s.structure_name}\"?`, async () => { await loadStructureForEditById(s.id); });
        });
        dupBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          showConfirm('Duplicate structure', `Create a duplicate of \"${s.structure_name}\"?`, async () => {
            try {
              const headers = { 'Content-Type': 'application/json' };
              if (window.csrfToken) headers['X-CSRFToken'] = window.csrfToken;
              const structure = JSON.parse(s.structure_json || '{}');
              const payload = { class_id: s.class_id, structure_name: `${s.structure_name} (copy)`, structure_json: JSON.stringify(structure) };
              const res = await fetch('/api/gradebuilder/save', { method: 'POST', headers, body: JSON.stringify(payload) });
              const out = await res.json();
              if (res.ok) { showToast('success', 'Duplicated'); await loadData(); }
              else showToast('error', out.error || 'Duplicate failed');
            } catch (e) { showToast('error', 'Network error'); }
          });
        });
        histBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          showConfirm('View history', `Fetch history for \"${s.structure_name}\"?`, async () => {
            try {
              const res = await fetch(`/api/gradebuilder/history/${s.id}`);
              if (!res.ok) { showToast('error', 'History not available'); return; }
              const hist = await res.json();
              if (window.Swal) {
                Swal.fire({ title: 'History', html: `<pre style="text-align:left;white-space:pre-wrap;">${escapeHtml(JSON.stringify(hist, null, 2))}</pre>`, width: 700 });
              } else {
                alert(JSON.stringify(hist, null, 2));
              }
            } catch (e) { showToast('error', 'Failed to fetch history'); }
          });
        });
        delBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          showConfirm('Delete structure', `Delete \"${s.structure_name}\"? This will remove version history.`, async () => {
            try {
              const headers = {};
              if (window.csrfToken) headers['X-CSRFToken'] = window.csrfToken;
              const res = await fetch(`/api/gradebuilder/delete/${s.id}`, { method: 'DELETE', headers });
              const out = await res.json();
              if (res.ok) { showToast('success', out.message || 'Deleted'); await loadData(); }
              else showToast('error', out.error || 'Delete failed');
            } catch (e) { showToast('error', 'Network error'); }
          });
        });

        if (structureListContainer) structureListContainer.appendChild(item);
      });
  // clear selection and preview after reload
  selectedStructureId = null;
  updatePreview(null);
      // update save button enabled state (class select may have been repopulated)
      updateSaveEnabled();
    } catch (e) {
      console.error('Failed to load classes', e);
    }
  }

  loadData();

  // New Structure button — prompt for name and class using SweetAlert
  const newStructureBtn = document.getElementById('new-structure-btn');
  if (newStructureBtn) newStructureBtn.addEventListener('click', async (ev) => {
    ev.preventDefault();
    // build class options HTML (use cached classes if the select is missing)
    let classOptionsHtml = '';
    const classesSource = (window._classes && window._classes.length) ? window._classes : (classSelect ? Array.from(classSelect.options).map(o=>({class_id:o.value, course:o.textContent, section: ''})) : []);
    classesSource.forEach(c => {
      const val = c.class_id || c.value || '';
      if (!val) return;
      const label = c.course ? (c.section ? `${c.course} - ${c.section}` : c.course) : (c.textContent || String(val));
      classOptionsHtml += `<option value="${val}">${label}</option>`;
    });
    const html = `
      <label style="display:block;margin-bottom:8px;">Structure name</label>
      <input id="swal-structure-name" class="swal2-input" placeholder="New Structure" />
      <label style="display:block;margin:10px 0 8px;">Class</label>
      <select id="swal-class-select" class="swal2-select">${classOptionsHtml}</select>
    `;
    if (window.Swal) {
      const { value: formValues } = await Swal.fire({
        title: 'Create new structure',
        html,
        focusConfirm: false,
        showCancelButton: true,
        preConfirm: () => {
          const name = document.getElementById('swal-structure-name').value.trim();
          const cid = document.getElementById('swal-class-select').value;
          if (!cid) {
            Swal.showValidationMessage('Please select a class');
            return false;
          }
          return { name: name || 'New Structure', classId: cid };
        }
      });
      if (formValues) {
        // persist selection for save() to avoid double-asking and populate editor (guard elements present)
        window._pendingClassId = formValues.classId;
        window._pendingStructureName = formValues.name;
        if (structureName) structureName.value = formValues.name;
        if (classSelect) classSelect.value = formValues.classId;
        if (labList) labList.innerHTML = '';
        if (lectureList) lectureList.innerHTML = '';
        // new structure - clear any last loaded snapshot
        lastLoadedSnapshot = null;
        editingStructureId = null; // creating new
        setReadOnlyMode(false);
        updateSums();
        updateSaveEnabled();
        if (structureName) structureName.focus();
        showToast('success', 'New structure ready');
      }
    } else {
      // fallback: just clear editor and focus
      if (structureName) structureName.value = 'New Structure';
      if (classSelect) classSelect.value = '';
      if (labList) labList.innerHTML = '';
      if (lectureList) lectureList.innerHTML = '';
      // new structure - clear any last loaded snapshot
      lastLoadedSnapshot = null;
      updateSums();
      updateSaveEnabled();
      if (structureName) structureName.focus();
    }
  });

  // helper to load a structure by id (from cached window._savedStructures)
  async function loadStructureById(sid) {
    try {
      const s = (window._savedStructures || []).find(x => String(x.id) === String(sid));
  if (!s) { showToast('error', 'Structure not found'); return; }
      const structure = JSON.parse(s.structure_json || '{}');
    // store snapshot for cancel/restore behavior
    lastLoadedSnapshot = {
      id: s.id,
      class_id: s.class_id,
      structure_name: s.structure_name,
      structure_json: s.structure_json
    };
  if (classSelect) classSelect.value = s.class_id;
  // cache for save flow when header select is absent
  window._pendingClassId = s.class_id;
    updateSaveEnabled();
  if (structureName) structureName.value = s.structure_name;
  window._pendingStructureName = s.structure_name;
    // clear lists
    if (labList) labList.innerHTML = '';
    if (lectureList) lectureList.innerHTML = '';
  (structure.LABORATORY || []).forEach(cat => { if (labList) labList.appendChild(createSub('LABORATORY', cat.name, cat.weight)); });
  (structure.LECTURE || []).forEach(cat => { if (lectureList) lectureList.appendChild(createSub('LECTURE', cat.name, cat.weight)); });
    updateSums();
  showToast('success', 'Loaded structure');
      // mark selected in UI
      selectedStructureId = String(sid);
      Array.from(structureListContainer.querySelectorAll('.structure-item')).forEach(el => el.classList.toggle('selected', el.dataset.id === selectedStructureId));
      updatePreview(selectedStructureId);
    } catch (e) {
      showToast('error', 'Failed to load structure');
    }
  }

  // Helper wrappers for specific modes
  async function loadStructureForEditById(sid) {
    editingStructureId = String(sid);
    await loadStructureById(sid);
    setReadOnlyMode(false);
    if (structureName) structureName.focus();
  }

  async function loadStructureReadOnlyById(sid) {
    editingStructureId = null;
    await loadStructureById(sid);
    setReadOnlyMode(true);
  }

  // Sidebar toggle behavior
  const leftSidebar = document.getElementById('left-sidebar');
  const rightSidebar = document.getElementById('right-sidebar');
  const toggleBtn = document.getElementById('toggle-sidebars-btn');
  const appLayout = document.querySelector('.app-layout');
  function toggleSidebars() {
    if (!leftSidebar || !rightSidebar) return;
    const hidden = leftSidebar.classList.toggle('hidden');
    rightSidebar.classList.toggle('hidden', hidden);
    // also toggle a class on the layout so the grid collapses the empty columns
    if (appLayout) appLayout.classList.toggle('sidebars-hidden', hidden);
  }
  if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebars);

  // Save buttons (top and bottom) elements
  const saveBtnTop = document.getElementById('save-btn');
  const saveBtnBottom = document.getElementById('save-btn-bottom');
  // Enable/disable save buttons depending on whether lab or lecture totals hit 100% (real-time)
  function updateSaveEnabled() {
    try {
      if (readOnlyMode) {
        if (saveBtnTop) saveBtnTop.disabled = true;
        if (saveBtnBottom) saveBtnBottom.disabled = true;
        if (status) status.textContent = 'Read-only preview. Click Edit to modify.';
        return;
      }
      const { labTotal, lecTotal } = updateSums();
      const labCount = (labList ? labList.querySelectorAll('.sub-item').length : 0);
      const lecCount = (lectureList ? lectureList.querySelectorAll('.sub-item').length : 0);
      const tol = 0.001;
      const labIs100 = Math.abs(labTotal - 100) <= tol;
      const lecIs100 = Math.abs(lecTotal - 100) <= tol;
      // Enable only if:
      // - each non-empty category sums to 100, and
      // - at least one category is non-empty and sums to 100
      const perCategoryOk = (labCount === 0 || labIs100) && (lecCount === 0 || lecIs100);
      const hasOneComplete = (labCount > 0 && labIs100) || (lecCount > 0 && lecIs100);
      const enabled = perCategoryOk && hasOneComplete;
      if (saveBtnTop) saveBtnTop.disabled = !enabled;
      if (saveBtnBottom) saveBtnBottom.disabled = !enabled;
      // small visual cue in status
      if (status) {
        if (!enabled) {
          status.textContent = 'Each non-empty category must total 100%. Fill exactly 100% in LABORATORY and/or LECTURE.';
        }
        else status.textContent = '';
      }
    } catch (e) { /* ignore */ }
  }
  // Keep class-change behavior (if header select exists we still update UI when class changes)
  if (classSelect) classSelect.addEventListener('change', () => updateSaveEnabled());

  // Helper: wire existing weight inputs so typing updates sums in real-time
  function wireWeightInputs() {
    try {
      const inputs = Array.from(document.querySelectorAll('[data-field="weight"]'));
      inputs.forEach(inp => {
        // avoid attaching multiple listeners
        if (inp._gb_input_wired) return;
        inp.addEventListener('input', () => { updateSums(); updateSaveEnabled(); });
        inp._gb_input_wired = true;
      });
    } catch (e) { /* ignore */ }
  }

  // initial wiring
  wireWeightInputs();

  // Preview button simple behavior
  const previewBtn = document.getElementById('preview-btn');
  if (previewBtn) previewBtn.addEventListener('click', () => {
    const previewBox = document.getElementById('preview-box');
    const structure = {
      LABORATORY: Array.from(document.querySelectorAll('#lab-list .sub-item')).map(el => ({name: el.querySelector('[data-field="name"]').value, weight: parseFloat(el.querySelector('[data-field="weight"]').value)||0})),
      LECTURE: Array.from(document.querySelectorAll('#lecture-list .sub-item')).map(el => ({name: el.querySelector('[data-field="name"]').value, weight: parseFloat(el.querySelector('[data-field="weight"]').value)||0})),
    };
    if (previewBox) {
      // Build a readable, styled preview instead of raw JSON
      const container = document.createElement('div');
      container.className = 'preview-details';

      const title = document.createElement('h3');
      const n = (structureName && structureName.value && structureName.value.trim()) ? structureName.value.trim() : 'Structure Preview';
      title.textContent = n;
      container.appendChild(title);

      const structDiv = document.createElement('div');
      structDiv.className = 'preview-structure';
      try {
        // reuse existing renderer used elsewhere in the page
        renderStructureContent(structDiv, structure);
      } catch (e) {
        // fallback to a simple readable text version
        const toList = (arr) => (arr||[]).map(x => `• ${x.name || 'Unnamed'} — ${(parseFloat(x.weight)||0).toFixed(2)}%`).join('\n');
        structDiv.innerHTML = `<pre style="white-space:pre-wrap">LABORATORY\n${toList(structure.LABORATORY)}\n\nLECTURE\n${toList(structure.LECTURE)}</pre>`;
      }
      container.appendChild(structDiv);

      previewBox.innerHTML = '';
      previewBox.appendChild(container);
    } else {
      console.log('Preview (readable):', structure);
    }
  });

  // Save: build structure_json with empty assessments arrays
  async function handleSave() {
    if (readOnlyMode) {
      showToast('error', 'This is a read-only view. Use Edit to modify.');
      return;
    }
    // Derive structure name with sensible fallbacks even when the header input is absent
    let name = null;
    if (structureName && structureName.value && structureName.value.trim()) {
      name = structureName.value.trim();
    } else if (window._pendingStructureName) {
      name = String(window._pendingStructureName);
    } else if (lastLoadedSnapshot && lastLoadedSnapshot.structure_name) {
      name = String(lastLoadedSnapshot.structure_name);
    } else {
      name = 'Untitled Structure';
    }

    // Resolve class id similarly with fallbacks
    let classId = (classSelect && classSelect.value) ? parseInt(classSelect.value) : null;
    if (!classId && window._pendingClassId) {
      classId = parseInt(window._pendingClassId);
    }
    if (!classId && lastLoadedSnapshot && lastLoadedSnapshot.class_id) {
      classId = parseInt(lastLoadedSnapshot.class_id);
    }
    // If no class select element or no selection, prompt the user with a modal to choose a class
    if (!classId) {
      // If Swal available, prompt for class (and optionally name) using cached window._classes
      if (window.Swal) {
        const classes = (window._classes || []).filter(c => c && (c.class_id || c.id));
        let optionsHtml = '<option value="">(select class)</option>';
        classes.forEach(c => {
          const val = c.class_id || c.id;
          const label = c.course ? (c.section ? `${c.course} - ${c.section}` : c.course) : (c.class_code || String(val));
          optionsHtml += `<option value="${val}">${escapeHtml(label)}</option>`;
        });
        const html = `
          <label style="display:block;margin-bottom:8px;">Structure name</label>
          <input id="swal-save-structure-name" class="swal2-input" value="${escapeHtml(name)}" />
          <label style="display:block;margin:10px 0 8px;">Class</label>
          <select id="swal-save-class-select" class="swal2-select">${optionsHtml}</select>
        `;
        const result = await Swal.fire({ title: 'Select class before saving', html, focusConfirm: false, showCancelButton: true, preConfirm: () => {
          const n = document.getElementById('swal-save-structure-name').value.trim();
          const cid = document.getElementById('swal-save-class-select').value;
          if (!cid) { Swal.showValidationMessage('Please select a class'); return false; }
          return { name: n || name, classId: cid };
        }});
        if (!result || !result.value) {
          showToast('info', 'Save cancelled');
          return;
        }
  name = result.value.name || name;
  classId = parseInt(result.value.classId);
  // cache for subsequent saves
  window._pendingStructureName = name;
  window._pendingClassId = classId;
  if (structureName) structureName.value = name;
  if (classSelect) classSelect.value = String(classId);
      } else {
        // fallback: cannot prompt, show message and abort
        showToast('error', 'Select a class');
        if (classSelect) classSelect.focus();
        return;
      }
    }

    const { labTotal, lecTotal } = updateSums();
    const labCount = (labList ? labList.querySelectorAll('.sub-item').length : 0);
    const lecCount = (lectureList ? lectureList.querySelectorAll('.sub-item').length : 0);
    const tol = 0.001;
    const labIs100 = Math.abs(labTotal - 100) <= tol;
    const lecIs100 = Math.abs(lecTotal - 100) <= tol;
    const perCategoryOk = (labCount === 0 || labIs100) && (lecCount === 0 || lecIs100);
    const hasOneComplete = (labCount > 0 && labIs100) || (lecCount > 0 && lecIs100);
    if (!(perCategoryOk && hasOneComplete)) {
      if (!perCategoryOk) {
        showToast('error', 'Each non-empty category must total 100% before saving');
      } else {
        showToast('error', 'Add subcategories totaling 100% in at least one category');
      }
      return;
    }

    function collect(list) {
      return Array.from(list.querySelectorAll('.sub-item')).map(el => {
        const nEl = el.querySelector('[data-field="name"]');
        const raw = nEl ? (nEl.value || '') : '';
        const name = String(raw).trim() || 'Unnamed';
        const weight = parseFloat(el.querySelector('[data-field="weight"]').value) || 0;
        return { name, weight, assessments: [] };
      });
    }

    const structure = {
      LABORATORY: collect(labList),
      LECTURE: collect(lectureList)
    };

  showToast('info', 'Saving...');
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (window.csrfToken) headers['X-CSRFToken'] = window.csrfToken;
      const isEdit = !!editingStructureId;
      const url = isEdit ? `/api/gradebuilder/update/${editingStructureId}` : '/api/gradebuilder/save';
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ class_id: classId, structure_name: name, structure_json: JSON.stringify(structure) })
      });
      const out = await res.json();
      if (res.ok) { showToast('success', isEdit ? 'Updated' : 'Saved');
        // reload structures list
        await loadData();
        if (isEdit) {
          editingStructureId = null; // exit edit mode after successful update
        }
      } else { showToast('error', out.error || out.message || 'Save failed'); }
    } catch (e) {
      showToast('error', 'Network error');
    }
  }

  // attach save handler to whichever save button exists (top or bottom)
  if (saveBtnTop) saveBtnTop.addEventListener('click', handleSave);
  if (saveBtnBottom) saveBtnBottom.addEventListener('click', handleSave);

  // Clear Fields and Cancel Edit behavior (buttons in editor header)
  const clearFieldsBtn = document.querySelector('.clear-fields');
  const cancelEditBtn = document.querySelector('.cancel-edit');

  if (clearFieldsBtn) clearFieldsBtn.addEventListener('click', (ev) => {
    ev.preventDefault();
    // clear the editor inputs but do not change lastLoadedSnapshot
    if (labList) labList.innerHTML = '';
    if (lectureList) lectureList.innerHTML = '';
    if (structureName) structureName.value = '';
    if (classSelect) classSelect.value = '';
  editingStructureId = null;
  setReadOnlyMode(false);
  updateSums();
  updateSaveEnabled();
    showToast('info', 'Fields cleared');
  });

  if (cancelEditBtn) cancelEditBtn.addEventListener('click', (ev) => {
    ev.preventDefault();
    // restore the lastLoadedSnapshot if present, otherwise clear
    if (!lastLoadedSnapshot) {
      // nothing to restore — just clear
      if (labList) labList.innerHTML = '';
      if (lectureList) lectureList.innerHTML = '';
      if (structureName) structureName.value = '';
      if (classSelect) classSelect.value = '';
      editingStructureId = null;
      setReadOnlyMode(false);
      updateSums();
      updateSaveEnabled();
      showToast('info', 'No saved structure to restore; fields cleared');
      return;
    }
    // confirm discard changes
    showConfirm('Cancel changes', 'Discard unsaved changes and restore the previously loaded structure?', async () => {
      try {
        // parse and repopulate from lastLoadedSnapshot
        const s = lastLoadedSnapshot;
        const structure = JSON.parse(s.structure_json || '{}');
        if (classSelect) classSelect.value = s.class_id;
        if (structureName) structureName.value = s.structure_name;
        if (labList) labList.innerHTML = '';
        if (lectureList) lectureList.innerHTML = '';
  (structure.LABORATORY || []).forEach(cat => { if (labList) labList.appendChild(createSub('LABORATORY', cat.name, cat.weight)); });
  (structure.LECTURE || []).forEach(cat => { if (lectureList) lectureList.appendChild(createSub('LECTURE', cat.name, cat.weight)); });
  setReadOnlyMode(false);
  updateSums();
  updateSaveEnabled();
        showToast('success', 'Restored loaded structure');
      } catch (e) {
        showToast('error', 'Failed to restore structure');
      }
    });
  });

  // Load selected structure into editor
  const loadStructureBtnEl = document.getElementById('load-structure-btn');
  if (loadStructureBtnEl) loadStructureBtnEl.addEventListener('click', async () => {
    const sid = selectedStructureId;
    if (!sid) { showToast('error', 'Select a structure to load'); return; }
    try {
      await loadStructureReadOnlyById(sid);
      showToast('success', 'Loaded (read-only)');
    } catch (e) {
      showToast('error', 'Failed to load structure');
    }
  });

  // Delete selected structure
  const deleteStructureBtnEl = document.getElementById('delete-structure-btn');
  if (deleteStructureBtnEl) deleteStructureBtnEl.addEventListener('click', async () => {
    const sid = selectedStructureId;
    if (!sid) return showToast('error', 'Select a structure to delete');
    await showConfirm('Delete selected structure', 'This will remove version history. Are you sure?', async () => {
      try {
        const headers = {};
        if (window.csrfToken) headers['X-CSRFToken'] = window.csrfToken;
        const res = await fetch(`/api/gradebuilder/delete/${sid}`, { method: 'DELETE', headers });
        const out = await res.json();
        if (res.ok) { showToast('success', out.message || 'Deleted'); await loadData(); }
        else showToast('error', out.error || 'Delete failed');
      } catch (e) { showToast('error', 'Network error'); }
    });
  });

});