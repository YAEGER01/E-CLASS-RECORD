/**
 * Grade Management System for instructor_grades_unified.html
 * Computes TOTAL using backend API and handles grade entry operations
 */

(function() {
  'use strict';

  // SweetAlert2 helper functions
  const SwalLib = window.Sweetalert2 || window.Swal || null;
  
  const swalAlert = async (icon, title, text) => {
    if (!SwalLib) { window.alert(text || title || ''); return; }
    await SwalLib.fire({ icon: icon || 'info', title: title || '', text: text || '' });
  };
  
  const swalConfirm = async (title, text, confirmText='Confirm') => {
    if (!SwalLib) { return window.confirm(text || title || '') ? true : false; }
    const res = await SwalLib.fire({ title, text: text || '', icon: 'question', showCancelButton: true, confirmButtonText: confirmText });
    return !!res.isConfirmed;
  };
  
  const swalPromptText = async (title, inputValue) => {
    if (!SwalLib) { return window.prompt(title || '', inputValue || ''); }
    const res = await SwalLib.fire({ title: title || '', input: 'text', inputValue: inputValue || '', showCancelButton: true, confirmButtonText: 'Continue' });
    return res.isConfirmed ? (res.value ?? '') : null;
  };
  
  const swalPromptNumber = async (title, inputValue) => {
    if (!SwalLib) { const v = window.prompt(title || '', String(inputValue ?? '')); return v == null ? null : v; }
    const res = await SwalLib.fire({ title: title || '', input: 'number', inputValue: inputValue != null ? String(inputValue) : '', inputAttributes: { min: '1', step: '1' }, showCancelButton: true, confirmButtonText: 'Continue' });
    return res.isConfirmed ? (res.value ?? '') : null;
  };

  /**
   * Grade Management System Class
   */
  class GradeManagementSystem {
    constructor() {
      // DOM Elements
      this.tbody = null;
      this.saveBtn = null;
      this.status = null;
      this.recalcBtn = null;
      this.dataEl = null;
      this.classId = 0;
      this.structureId = 0;
      this.csrfToken = null;
      this.actionsBox = null;

      // State
      this.GROUPED_CACHE = null;
      this.dirty = new Map();
      this.serverComputeTimer = null;
      this.persistTimer = null;
      this.scrollTimers = new Map();
      this.SUB_GROUPS = {};

      // Configuration
      this.INPUT_PERSISTENCE_ENABLED = true;
      this.SCROLL_PERSIST_ENABLED = true;
      this.PERSIST_KEY = '';
      this.inputsLocked = false;
    }

    /**
     * Setup the grade management system (prepare DOM hooks and event listeners)
     */
    setup() {
      if (this.cacheElements()) {
        this.initPersistence();
        this.setupEventListeners();
        this.setupScrollPersistence();
        this.buildSubGroups();
        this.init();
      }
    }

    /**
     * Cache DOM elements and initialize basic properties
     */
    cacheElements() {
      this.tbody = document.getElementById('tbody');
      this.saveBtn = document.getElementById('save-btn');
      this.status = document.getElementById('save-status');
      this.recalcBtn = document.getElementById('recalc-btn');
      this.dataEl = document.getElementById('page-data');
      this.classId = parseInt(this.dataEl?.dataset?.classId || '0', 10) || 0;
      this.structureId = parseInt(this.dataEl?.dataset?.structureId || '0', 10) || 0;
      this.csrfToken = this.dataEl?.dataset?.csrfToken || null;
      this.actionsBox = document.getElementById('structure-actions');

      // Return false if tbody is not found
      return !!this.tbody;
    }

    /**
     * Get grouped assessments from JSON element
     */
    getGrouped() {
      if (this.GROUPED_CACHE) return this.GROUPED_CACHE;
      try {
        const gaEl = document.getElementById('ga-json');
        this.GROUPED_CACHE = JSON.parse((gaEl && gaEl.textContent) || '{}') || {};
      } catch(_) { this.GROUPED_CACHE = {}; }
      return this.GROUPED_CACHE;
    }

    /**
     * Get existing assessment names for a category and subcategory
     */
    getExistingNames(category, sub) {
      try {
        const G = this.getGrouped();
        const arr = (((G || {})[category] || {})[sub] || []);
        return Array.isArray(arr) ? arr.map(a => a && a.name ? String(a.name) : '').filter(Boolean) : [];
      } catch(_) { return []; }
    }

    /**
     * Parse assessment name to extract base and index
     */
    parseName(name) {
      if (!name) return { base: '', index: null };
      const m = String(name).trim().match(/^(.+?)\s*(\d+)$/);
      if (!m) return { base: String(name).trim(), index: null };
      return { base: m[1].trim(), index: parseInt(m[2], 10) };
    }

    /**
     * Generate next assessment name suggestion
     */
    nextNameSuggestion(category, sub, subId, fallbackBase='Assessment') {
      const lsKey = `lastName:${this.classId}:${subId}`;
      const last = localStorage.getItem(lsKey);
      if (last) {
        const p = this.parseName(last);
        if (p.base) {
          const names = this.getExistingNames(category, sub);
          let maxIdx = 0;
          names.forEach(n => { const pn = this.parseName(n); if (pn.base.toLowerCase() === p.base.toLowerCase() && pn.index) maxIdx = Math.max(maxIdx, pn.index); });
          const nextIdx = (maxIdx || p.index || 0) + 1;
          return { suggested: `${p.base} ${nextIdx}`, base: p.base, index: nextIdx, lsKey };
        }
      }
      const names = this.getExistingNames(category, sub);
      if (names.length) {
        const p0 = this.parseName(names[0]);
        const base = p0.base || fallbackBase;
        let maxIdx = 0;
        names.forEach(n => { const pn = this.parseName(n); if (pn.base.toLowerCase() === base.toLowerCase() && pn.index) maxIdx = Math.max(maxIdx, pn.index); });
        const nextIdx = (maxIdx || 0) + 1;
        if (maxIdx === 0) return { suggested: base, base, index: 1, lsKey: `lastName:${this.classId}:${subId}` };
        return { suggested: `${base} ${nextIdx}`, base, index: nextIdx, lsKey: `lastName:${this.classId}:${subId}` };
      }
      return { suggested: `${fallbackBase} 1`, base: fallbackBase, index: 1, lsKey: `lastName:${this.classId}:${subId}` };
    }

    /**
     * Initialize persistence settings
     */
    initPersistence() {
      window.INPUT_PERSISTENCE_ENABLED = this.INPUT_PERSISTENCE_ENABLED;
      this.PERSIST_KEY = `gradeInputs:${this.classId}`;
      this.LOCK_KEY = `inputsLocked:${this.classId}`;
    }

    /**
     * Write current input values to localStorage
     */
    persistWrite() {
      if (!this.INPUT_PERSISTENCE_ENABLED) return;
      try {
        const obj = {};
        document.querySelectorAll('input.score').forEach(inp => {
          const sid = inp.getAttribute('data-student');
          const aid = inp.getAttribute('data-assessment');
          if (!sid || !aid) return;
          const v = inp.value;
          if (v !== '') obj[`${sid}:${aid}`] = v;
        });
        localStorage.setItem(this.PERSIST_KEY, JSON.stringify(obj));
      } catch (_) {}
    }

    /**
     * Schedule persist write with debouncing
     */
    schedulePersistWrite() {
      if (!this.INPUT_PERSISTENCE_ENABLED) return;
      if (this.persistTimer) clearTimeout(this.persistTimer);
      this.persistTimer = setTimeout(() => { this.persistTimer = null; this.persistWrite(); }, 300);
    }

    /**
     * Restore persisted input values
     */
    persistRestore() {
      if (!this.INPUT_PERSISTENCE_ENABLED) return;
      try {
        const raw = localStorage.getItem(this.PERSIST_KEY);
        if (!raw) return;
        const obj = JSON.parse(raw || '{}');
        Object.entries(obj).forEach(([k, v]) => {
          const [sid, aid] = k.split(':');
          const inp = document.querySelector(`input.score[data-student="${sid}"][data-assessment="${aid}"]`);
          if (inp) {
            inp.value = v;
            inp.dispatchEvent(new Event('input', { bubbles: true }));
          }
        });
      } catch (_) {}
    }

    /**
     * Clear persisted input values
     */
    persistClear() { 
      try { localStorage.removeItem(this.PERSIST_KEY); } catch (_) {} 
    }

    /**
     * Setup scroll position persistence
     */
    setupScrollPersistence() {
      window.SCROLL_PERSIST_ENABLED = this.SCROLL_PERSIST_ENABLED;
      
      let els = Array.from(document.querySelectorAll('[data-persist-scroll="true"]'));
      if (els.length === 0) {
        const auto = Array.from(document.querySelectorAll('.matrix-wrapper, .drawer-content, .matrix'));
        els = auto.filter(el => el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth);
      }
      
      els.forEach((el, idx) => {
        if (!el.id) el.id = `persist_scroll_auto_${idx}`;
        const key = `scrollPos:${this.classId}:${el.id}`;
        
        try {
          const raw = localStorage.getItem(key);
          if (raw) {
            const obj = JSON.parse(raw);
            if (obj && typeof obj.top === 'number') el.scrollTop = obj.top;
            if (obj && typeof obj.left === 'number') el.scrollLeft = obj.left;
          }
        } catch (_) {}
        
        el.addEventListener('scroll', () => {
          if (this.scrollTimers.has(el.id)) clearTimeout(this.scrollTimers.get(el.id));
          const t = setTimeout(() => {
            try { localStorage.setItem(key, JSON.stringify({ top: el.scrollTop, left: el.scrollLeft })); } catch(_) {}
            this.scrollTimers.delete(el.id);
          }, 150);
          this.scrollTimers.set(el.id, t);
        }, { passive: true });
      });
    }

    /**
     * Get assessment columns from table headers
     */
    getAssessmentColumns() {
      const heads = Array.from(document.querySelectorAll('th.assess-col'));
      return heads.map((th, idx) => ({
        idx,
        id: parseInt(th.getAttribute('data-assessment-id') || '0', 10) || 0,
        name: th.childNodes[0]?.nodeValue?.trim() || th.textContent.trim(),
        category: th.getAttribute('data-category') || '',
        subcategory: th.getAttribute('data-subcategory') || '',
        max: parseFloat(th.getAttribute('data-max') || '0') || 0,
        subweight: parseFloat(th.getAttribute('data-subweight') || '0') || 0
      })).filter(c => c.id);
    }

    /**
     * Get all student rows
     */
    getStudentRows() {
      return Array.from(this.tbody.querySelectorAll('tr'));
    }

    /**
     * Build subcategory groups from table headers
     */
    buildSubGroups() {
      const cols = this.getAssessmentColumns();
      const groups = {};
      cols.forEach(c => {
        const key = `${c.category}::${c.subcategory}`;
        if (!groups[key]) groups[key] = { 
          category: c.category, 
          subcategory: c.subcategory, 
          ids: [], 
          maxes: [], 
          maxTotal: 0, 
          subweight: c.subweight || 0 
        };
        groups[key].ids.push(c.id);
        groups[key].maxes.push(c.max);
        groups[key].maxTotal += (c.max || 0);
        if (!groups[key].subweight && c.subweight) groups[key].subweight = c.subweight;
      });
      this.SUB_GROUPS = groups;
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
      // Row highlighting
      this.tbody.addEventListener('focusin', (e) => {
        const tr = e.target && e.target.closest('tr');
        if (!tr) return;
        tr.classList.add('highlight');
      });
      
      this.tbody.addEventListener('focusout', (e) => {
        const tr = e.target && e.target.closest('tr');
        if (!tr) return;
        setTimeout(() => {
          if (!tr.contains(document.activeElement)) tr.classList.remove('highlight');
        }, 50);
      });

      // Input validation and dirty tracking
      this.tbody.addEventListener('input', (e) => {
        const inp = e.target;
        if (!inp.matches('input.score')) return;

        // Validate against max
        const maxAttr = inp.getAttribute('max');
        if (maxAttr != null && maxAttr !== '') {
          const maxVal = parseFloat(maxAttr);
          const cur = inp.value;
          if (cur !== '') {
            const num = parseFloat(cur);
            if (!isNaN(num) && isFinite(maxVal) && num > maxVal) {
              inp.value = String(maxVal);
              inp.classList.add('score-invalid');
              setTimeout(() => inp.classList.remove('score-invalid'), 1400);
              this.status.textContent = `Value limited to max ${maxVal}`;
            }
          }
        }

        const sid = parseInt(inp.getAttribute('data-student'), 10);
        const aid = parseInt(inp.getAttribute('data-assessment'), 10);
        const val = inp.value;
        this.dirty.set(`${sid}:${aid}`, { student_id: sid, assessment_id: aid, class_id: this.classId, score: val === '' ? null : parseFloat(val) });
        this.status.textContent = `${this.dirty.size} change(s) not saved`;
        this.schedulePersistWrite();

        // Handle recomputation
        const tr = inp.closest('tr');
        this.recomputeRow(tr);
        this.updateFinalGradeForRow(tr);
        
        if (this.serverComputeTimer) clearTimeout(this.serverComputeTimer);
        this.serverComputeTimer = setTimeout(() => { this.computeServerForAll(); this.serverComputeTimer = null; }, 800);
      });

      // Save button listener removed — save functionality intentionally removed
      
      // Recalculate button
      this.recalcBtn?.addEventListener('click', () => { this.recomputeAll(); });

      // Document click handler for various actions
      document.addEventListener('click', async (e) => {
        // Clear Inputs button
        const btnClear = e.target.closest('button[data-action="clear-inputs"]');
        if (btnClear) {
          e.preventDefault();
          const ok = await swalConfirm('Clear all inputs?', 'This will remove all unsaved scores from the inputs. Continue?', 'Clear');
          if (ok) this.clearAllInputs();
          return;
        }

        // Toggle lock button — lock/unlock all input fields (with confirmation)
        const btnToggle = e.target.closest('button[data-action="toggle-lock"]');
        if (btnToggle) {
          e.preventDefault();
          try {
            const wantLock = !this.inputsLocked;
            const title = wantLock ? 'Lock all inputs?' : 'Unlock inputs?';
            const text = wantLock ? 'Locking will disable editing and prevent creating new assessments. You can unlock later.' : 'Unlocking will re-enable editing.';
            const confirmText = wantLock ? 'Lock' : 'Unlock';
            const ok = await swalConfirm(title, text, confirmText);
            if (!ok) return;
            this.applyLockState(wantLock);
            // reflect state on all toggle buttons
            document.querySelectorAll('button[data-action="toggle-lock"]').forEach(b => b.classList.toggle('locked', !!this.inputsLocked));
          } catch(_) {
            // fallback: toggle without confirmation
            this.toggleLockInputs();
          }
          return;
        }

        // Submit button — save inputs and create snapshot
        const btnSubmit = e.target.closest('button[data-action="submit-inputs"]');
        if (btnSubmit) {
          e.preventDefault();
          try {
            this.saveAndSnapshot();
          } catch (err) {
            console.error('saveAndSnapshot failed', err);
          }
          return;
        }
        // Add assessment via dropdown
        const btnSel = e.target.closest('button[data-action="add-assessment-select"]');
        if (btnSel) {
          e.preventDefault();
          const selId = btnSel.getAttribute('data-select-id');
          const sel = document.getElementById(selId);
          if (!sel) return;
          const opt = sel.options[sel.selectedIndex];
          const sub = opt?.value || '';
          const category = sel.getAttribute('data-category') || '';
          const subId = parseInt(opt?.dataset?.subcategoryId || '0', 10) || 0;
          
          const vbtn = { getAttribute: (k) => {
            if (k === 'data-subcategory') return sub;
            if (k === 'data-category') return category;
            if (k === 'data-subcategory-id') return String(subId || '');
            return null;
          }};
          await this.handleAdd(vbtn);
          return;
        }

        // Edit assessment
        const editBtn = e.target.closest('button[data-action="edit-assessment"]');
        if (editBtn) {
          e.preventDefault();
          await this.handleEditAssessment(editBtn);
          return;
        }

        // Legacy: per-sub inline add buttons
        const btn = e.target.closest('button[data-action="add-assessment"]');
        if (btn) {
          e.preventDefault();
          await this.handleAdd(btn);
        }
      });

      // Initialize collapsible drawers
      this.initCollapsibleDrawers();
    }

    /**
     * Handle adding a new assessment
     */
    async handleAdd(btn) {
      const subcategory = btn.getAttribute('data-subcategory');
      const category = btn.getAttribute('data-category');
      const subcategoryId = parseInt(btn.getAttribute('data-subcategory-id') || '0', 10) || 0;
      const suggest = this.nextNameSuggestion(category, subcategory, subcategoryId);
      
      let name = await swalPromptText(`New assessment for ${subcategory}`, suggest.suggested);
      if (name == null) return;
      name = String(name).trim();
      if (!name) { await swalAlert('warning', 'Name required', 'Please enter an assessment name.'); return; }
      
      let maxStr = await swalPromptNumber('Max score (e.g., 100)', 100);
      if (maxStr == null) return;
      const max = parseFloat(maxStr);
      if (!isFinite(max) || max <= 0) { await swalAlert('warning', 'Invalid max score', 'Please enter a positive number.'); return; }
      if (!subcategoryId) { await swalAlert('error', 'Subcategory mapping missing', 'Please refresh this page and try again.'); return; }

      try {
        const payload = {
          name,
          subcategory_id: subcategoryId,
          max_score: max
        };
        const formBody = new URLSearchParams();
        Object.entries(payload).forEach(([k,v]) => {
          if (v !== undefined && v !== null && v !== '') formBody.append(k, String(v));
        });
        const headers2 = { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' };
        if (this.csrfToken) headers2['X-CSRFToken'] = this.csrfToken;
        
        const res = await fetch('/api/assessments/simple', {
          method: 'POST',
          headers: headers2,
          body: formBody.toString()
        });
        let out;
        try { out = await res.json(); } catch(_) { out = {}; }
        
        if (!res.ok) {
          const msg = out && out.error ? out.error : `Failed to create assessment (HTTP ${res.status})`;
          await swalAlert('error', 'Create failed', msg);
          return;
        }

        try {
          localStorage.setItem(`lastName:${this.classId}:${subcategoryId}`, name);
          const G = this.getGrouped();
          G[category] = G[category] || {};
          G[category][subcategory] = G[category][subcategory] || [];
          G[category][subcategory].push({ name, max_score: max });
        } catch(_) {}
        
        await swalAlert('success', 'Assessment created', `${name} added under ${subcategory}.`);
        window.location.reload();
      } catch(err) {
        await swalAlert('error', 'Network error', 'Could not create assessment.');
      }
    }

    /**
     * Handle editing an assessment
     */
    async handleEditAssessment(editBtn) {
      const assessmentId = parseInt(editBtn.getAttribute('data-assessment-id') || '0', 10) || 0;
      const category = editBtn.getAttribute('data-category') || '';
      const subcategory = editBtn.getAttribute('data-subcategory') || '';
      const currentMax = parseFloat(editBtn.getAttribute('data-max') || '0') || 0;

      if (!SwalLib) {
        let newMaxStr = window.prompt(`Edit max score for ${category} › ${subcategory}`, String(currentMax));
        if (newMaxStr == null) return;
        const newMax = parseFloat(newMaxStr);
        if (!isFinite(newMax) || newMax <= 0) { window.alert('Enter a positive number'); return; }
        try {
          const headers = { 'Content-Type': 'application/json' };
          if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;
          const res = await fetch(`/api/assessments/${assessmentId}/update_max`, { method: 'POST', headers, body: JSON.stringify({ max_score: newMax }) });
          if (!res.ok) { window.alert('Update failed'); return; }
          window.location.reload();
        } catch(_) { window.alert('Network error'); }
        return;
      }

      const res = await SwalLib.fire({
        title: `Edit max score — ${category} › ${subcategory}`,
        html: `<input id="swal-max" type="number" class="swal2-input" min="1" step="0.01" value="${currentMax}">`,
        showCancelButton: true,
        showDenyButton: true,
        confirmButtonText: 'Save',
        denyButtonText: 'Delete',
        preConfirm: () => {
          const val = SwalLib.getPopup().querySelector('#swal-max').value;
          return val;
        }
      });

      // Delete path
      if (res.isDenied) {
        const ok = await swalConfirm('Delete assessment?', 'This will permanently delete the assessment and its scores. Continue?', 'Delete');
        if (!ok) return;
        try {
          const headers = { 'Content-Type': 'application/json' };
          if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;
          const rdel = await fetch(`/api/assessments/${assessmentId}`, { method: 'DELETE', headers });
          let out = {};
          try { out = await rdel.json(); } catch(_) {}
          if (!rdel.ok) {
            const msg = out && out.error ? out.error : `Failed to delete (HTTP ${rdel.status})`;
            await swalAlert('error', 'Delete failed', msg);
            return;
          }
          await swalAlert('success', 'Deleted', 'Assessment was deleted.');
          window.location.reload();
        } catch(err) {
          await swalAlert('error', 'Network error', 'Could not delete assessment.');
        }
        return;
      }

      // Save path
      if (res.isConfirmed) {
        const newMaxStr = res.value;
        if (newMaxStr == null) return;
        const newMax = parseFloat(newMaxStr);
        if (!isFinite(newMax) || newMax <= 0) { await swalAlert('warning', 'Invalid max score', 'Please enter a positive number.'); return; }
        try {
          const headers = { 'Content-Type': 'application/json' };
          if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;
          const r = await fetch(`/api/assessments/${assessmentId}/update_max`, { method: 'POST', headers, body: JSON.stringify({ max_score: newMax }) });
          let out = {};
          try { out = await r.json(); } catch(_) {}
          if (!r.ok) {
            const msg = out && out.error ? out.error : `Failed to update max score (HTTP ${r.status})`;
            await swalAlert('error', 'Update failed', msg);
            return;
          }
          await swalAlert('success', 'Max score updated', `Assessment max score is now ${newMax}.`);
          window.location.reload();
        } catch(err) {
          await swalAlert('error', 'Network error', 'Could not update max score.');
        }
      }
    }

    /**
     * Save all inputs (or only changed inputs) and request server recompute + snapshot.
     * Sends POST to `/classes/<classId>/save_snapshot` with payload { scores: [...] }
     */
    async saveAndSnapshot() {
      const classId = this.classId || 0;
      if (!classId) {
        this.status.textContent = 'Missing class id';
        return;
      }

      // Gather scores: prefer sending only dirty entries; fall back to all inputs
      const scores = [];
      if (this.dirty && this.dirty.size) {
        // send only dirty map entries
        for (const v of this.dirty.values()) {
          scores.push({
            student_id: v.student_id,
            assessment_id: v.assessment_id,
            class_id: v.class_id || classId,
            score: v.score == null ? 0 : v.score,
          });
        }
      } else {
        // collect all inputs present in the DOM
        document.querySelectorAll('input.score').forEach(inp => {
          const sid = parseInt(inp.getAttribute('data-student') || '0', 10) || 0;
          const aid = parseInt(inp.getAttribute('data-assessment') || '0', 10) || 0;
          if (!sid || !aid) return;
          const val = inp.value;
          const sv = val === '' ? 0 : parseFloat(val);
          scores.push({ student_id: sid, assessment_id: aid, class_id: classId, score: sv });
        });
      }

      if (!scores.length) {
        this.status.textContent = 'No scores to save';
        return;
      }

      this.status.textContent = 'Saving and creating snapshot…';
      try {
        const headers = { 'Content-Type': 'application/json' };
        if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;
        const res = await fetch(`/classes/${classId}/save_snapshot`, { method: 'POST', headers, body: JSON.stringify({ scores }) });
        const out = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.status.textContent = out.error || 'Save failed';
          await swalAlert('error', 'Save failed', out.error || out.message || 'Unknown error');
        } else {
          this.status.textContent = 'All changes saved — snapshot created';
          // clear dirty state and persisted drafts
          try { this.dirty.clear(); } catch(_) {}
          try { this.persistClear(); } catch(_) {}
          await swalAlert('success', 'Saved', `Snapshot version ${out.version || ''} created.`);
          // request fresh compute values from server to update UI
          try { this.computeServerForAll(); } catch(_) {}
        }
      } catch (err) {
        console.error(err);
        this.status.textContent = 'Network error';
        await swalAlert('error', 'Network error', 'Could not save snapshot.');
      }
    }

    /**
     * Clear all grade input fields (and persisted drafts)
     */
    clearAllInputs() {
      // Clear DOM inputs
      document.querySelectorAll('input.score').forEach(inp => {
        inp.value = '';
        inp.dispatchEvent(new Event('input', { bubbles: true }));
      });
      // Clear dirty state and persisted drafts
      try { this.dirty.clear(); } catch(_) {}
      try { this.persistClear(); } catch(_) {}
      // Recompute derived cells and final grades
      try { this.recomputeAll(); this.updateFinalGrades(); } catch(_) {}
      if (this.status) this.status.textContent = 'Cleared inputs';
    }

    /**
     * Apply lock state to inputs (true = locked/disabled)
     */
    applyLockState(locked) {
      this.inputsLocked = !!locked;
      // Disable/enable input fields
      document.querySelectorAll('input.score').forEach(inp => { inp.disabled = !!this.inputsLocked; });
      // Disable/enable add/edit assessment controls and important buttons
      const controls = Array.from(document.querySelectorAll('button[data-action="add-assessment"], button[data-action="add-assessment-select"], button[data-action="edit-assessment"], #save-btn, #recalc-btn'));
      controls.forEach(el => { try { el.disabled = !!this.inputsLocked; } catch(_) {} });
      // No visual overlay — simply enable/disable inputs and controls when locked
      // Persist lock state
      try { localStorage.setItem(this.LOCK_KEY, this.inputsLocked ? '1' : '0'); } catch(_) {}
      // Update related UI buttons
      document.querySelectorAll('button[data-action="toggle-lock"]').forEach(b => {
        b.classList.toggle('locked', !!this.inputsLocked);
        b.textContent = this.inputsLocked ? 'Unlock Data' : 'Lock/Unlock Data';
      });
    }

    /**
     * Toggle the lock state for inputs
     */
    toggleLockInputs() {
      const newState = !this.inputsLocked;
      this.applyLockState(newState);
    }

    /**
     * Format number to specified decimal places
     */
    fmt(num, digits=2) {
      if (!isFinite(num)) return '';
      return Number(num).toFixed(digits);
    }

    /**
     * Recompute row values for a specific subcategory
     */
    recomputeRowForSub(tr, group) {
      if (!tr || !group) return;
      let total = 0;
      let hasValue = false;
      group.ids.forEach(id => {
        const inp = tr.querySelector(`input.score[data-assessment="${id}"]`);
        if (!inp) return;
        const v = inp.value === '' ? NaN : parseFloat(inp.value);
        if (!isNaN(v)) { total += v; hasValue = true; }
      });
      const maxTotal = group.maxTotal || 0;
      const eq = maxTotal > 0 ? (total / maxTotal) * 100 : 0;
      const weight = (group.subweight || 0);
      const reqpct = (eq * weight) / 100;
      const totalCell = tr.querySelector(`td.computed.total-col[data-category="${group.category}"][data-subcategory="${group.subcategory}"]`);
      const equivCell = tr.querySelector(`td.computed.equiv-col[data-category="${group.category}"][data-subcategory="${group.subcategory}"]`);
      const reqpctCell = tr.querySelector(`td.computed.reqpct-col[data-category="${group.category}"][data-subcategory="${group.subcategory}"]`);
      if (hasValue) {
        if (totalCell) totalCell.textContent = this.fmt(total, 2);
        if (equivCell) equivCell.textContent = this.fmt(eq, 2);
        if (reqpctCell) reqpctCell.textContent = this.fmt(reqpct, 2);
      } else {
        if (totalCell) totalCell.textContent = '';
        if (equivCell) equivCell.textContent = '';
        if (reqpctCell) reqpctCell.textContent = '';
      }
    }

    /**
     * Recompute category ratings for a row
     */
    recomputeCategoryRatings(tr) {
      if (!tr) return;
      const cats = Array.from(new Set(Object.values(this.SUB_GROUPS).map(g => g.category)));
      cats.forEach(cat => {
        let sum = 0;
        let any = false;
        tr.querySelectorAll(`td.computed.reqpct-col[data-category="${cat}"]`).forEach(td => {
          const txt = (td.textContent || '').trim();
          if (txt === '') return;
          const n = parseFloat(txt);
          if (!isNaN(n)) { sum += n; any = true; }
        });
        const ratingCell = tr.querySelector(`td.computed.rating-col[data-category="${cat}"]`);
        if (ratingCell) ratingCell.textContent = any ? this.fmt(sum, 2) : '';
      });
    }

    /**
     * Recompute all values for a row
     */
    recomputeRow(tr) {
      if (!tr) return;
      Object.values(this.SUB_GROUPS).forEach(g => this.recomputeRowForSub(tr, g));
      this.recomputeCategoryRatings(tr);
    }

    /**
     * Update final grade for a specific row
     */
    updateFinalGradeForRow(tr) {
      if (!tr) return;
      const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
      const lectureTd = tr.querySelector('td.computed.rating-col[data-category="LECTURE"]');
      const labTd = tr.querySelector('td.computed.rating-col[data-category="LABORATORY"]');
      const lecture = lectureTd ? parseFloat((lectureTd.textContent||'').trim()) : NaN;
      const lab = labTd ? parseFloat((labTd.textContent||'').trim()) : NaN;
      const finalRow = document.querySelector(`table.final-grade-table tbody tr[data-student-id="${sid}"]`);
      if (!finalRow) return;
      const rawCell = finalRow.querySelector('td.raw-grade');
      const totalCell = finalRow.querySelector('td.total-grade');
      // Only show final grade values once there is at least one entered score
      // (empty string means untouched). This prevents showing defaults when
      // the sheet is still blank.
      const hasAnyInputValue = Array.from(tr.querySelectorAll('input.score')).some(i => String(i.value).trim() !== '');

      const gradeMarkCell = finalRow.querySelector('td.grade-mark');
      const remarksCell = finalRow.querySelector('td.remarks');

      if (!hasAnyInputValue) {
        if (rawCell) rawCell.textContent = '';
        if (totalCell) totalCell.textContent = '';
        if (gradeMarkCell) gradeMarkCell.textContent = '';
        if (remarksCell) remarksCell.textContent = '';
        return;
      }

      const lecVal = isNaN(lecture) ? 0 : lecture;
      const labVal = isNaN(lab) ? 0 : lab;
      const raw = Math.round((labVal * 0.4 + lecVal * 0.6) * 100) / 100;
      if (rawCell) rawCell.textContent = raw.toFixed(2);
      // TOTAL GRADE formula: TOTAL = RAW * 0.625 + 37.5
      const totalGrade = Math.round((raw * 0.625 + 37.5) * 100) / 100;
      if (totalCell) totalCell.textContent = totalGrade.toFixed(2);

      // Compute GRADE MARK from TOTAL GRADE (VL7 equivalent)
      if (gradeMarkCell) {
        const t = totalGrade;
        let gm = '';
        if (t < 75) gm = '5.0';
        else if (t < 77) gm = '3.0';
        else if (t < 80) gm = '2.75';
        else if (t < 83) gm = '2.5';
        else if (t < 86) gm = '2.25';
        else if (t < 89) gm = '2.0';
        else if (t < 92) gm = '1.75';
        else if (t < 95) gm = '1.5';
        else gm = '1.25';
        gradeMarkCell.textContent = gm;
      }

      // Compute REMARKS: check for missing Project, Exam, or Lab Exam inputs.
      // Heuristic: group assessments by keywords in their header names. If any matching
      // assessment exists for this student row and its input is empty, mark as missing.
      if (remarksCell) {
        const heads = Array.from(document.querySelectorAll('th.assess-col'));
        const getIdsByKeywords = (keywords) => {
          return heads.map(h => {
            const id = h.getAttribute('data-assessment-id');
            const name = (h.childNodes[0]?.nodeValue || h.textContent || '').toLowerCase();
            return (id && keywords.some(k => name.includes(k))) ? id : null;
          }).filter(Boolean);
        };

        const projectIds = getIdsByKeywords(['project', 'proj']);
        const examIds = getIdsByKeywords(['exam', 'final', 'midterm', 'quiz']);
        const labIds = getIdsByKeywords(['lab', 'laboratory', 'lab exam']);

        const anyMissing = (ids) => {
          if (!ids || ids.length === 0) return false; // no matching assessments -> don't flag
          return ids.some(id => {
            const inp = tr.querySelector(`input.score[data-assessment="${id}"]`);
            return inp ? (String(inp.value).trim() === '') : false;
          });
        };

        let remarks = 'PASSED';
        if (anyMissing(projectIds)) remarks = 'NO PROJECT';
        else if (anyMissing(examIds)) remarks = 'NO EXAM';
        else if (anyMissing(labIds)) remarks = 'NO LAB EXAM';
        remarksCell.textContent = remarks;
      }
    }

    /**
     * Update all final grades
     */
    updateFinalGrades() {
      this.getStudentRows().forEach(tr => this.updateFinalGradeForRow(tr));
    }

    /**
     * Compute grades using server API
     */
    async computeServerForAll() {
      try {
        const groupsPayload = {};
        Object.entries(this.SUB_GROUPS).forEach(([k, g]) => {
          groupsPayload[k] = { 
            ids: g.ids.slice(), 
            maxes: g.maxes.slice(), 
            maxTotal: g.maxTotal || 0, 
            subweight: g.subweight || 0 
          };
        });
        const studentsPayload = this.getStudentRows().map(tr => {
          const sid = parseInt(tr.getAttribute('data-student-id')||'0',10)||0;
          const scores = {};
          tr.querySelectorAll('input.score').forEach(inp => {
            const aid = parseInt(inp.getAttribute('data-assessment')||'0',10)||0;
            const v = inp.value;
            if (v === '') return;
            const num = parseFloat(v);
            if (!isNaN(num)) scores[String(aid)] = num;
          });
          return { student_id: sid, scores };
        });

        const payload = { class_id: this.classId, groups: groupsPayload, students: studentsPayload };
        const headers = { 'Content-Type': 'application/json' };
        if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;
        const res = await fetch('/api/grade-entry/compute', { method: 'POST', headers, body: JSON.stringify(payload) });
        if (!res.ok) return;
        const out = await res.json();
        if (!out || !out.results) return;
        
        this.getStudentRows().forEach(tr => {
          const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
          const byGroup = out.results[sid] || {};
          Object.entries(byGroup).forEach(([gkey, vals]) => {
            const parts = gkey.split('::');
            const cat = parts[0] || '';
            const sub = parts[1] || '';
            const totalCell = tr.querySelector(`td.computed.total-col[data-category="${cat}"][data-subcategory="${sub}"]`);
            const equivCell = tr.querySelector(`td.computed.equiv-col[data-category="${cat}"][data-subcategory="${sub}"]`);
            const reqpctCell = tr.querySelector(`td.computed.reqpct-col[data-category="${cat}"][data-subcategory="${sub}"]`);
            if (totalCell && vals.total !== undefined) totalCell.textContent = Number(vals.total).toFixed(2);
            if (equivCell && vals.eq_pct !== undefined) equivCell.textContent = Number(vals.eq_pct).toFixed(2);
            if (reqpctCell) {
              if (vals.reqpct_display !== undefined) {
                reqpctCell.textContent = Number(vals.reqpct_display).toFixed(2);
              } else if (vals.reqpct !== undefined) {
                reqpctCell.textContent = Number(vals.reqpct).toFixed(2);
              }
            }
          });
          this.recomputeCategoryRatings(tr);
          this.updateFinalGradeForRow(tr);
        });
      } catch (err) {
        // silent fallback
      }
    }

    /**
     * Recompute all grades
     */
    recomputeAll() {
      // Run local recompute immediately (fast, client-side)
      this.getStudentRows().forEach(tr => this.recomputeRow(tr));
      // Do NOT call server compute here to avoid blocking UI on page load or user interaction.
      // Server compute is scheduled separately during init with a small delay.
    }

    /**
     * Initialize collapsible drawers
     */
    initCollapsibleDrawers() {
      const containers = Array.from(document.querySelectorAll('.collapsable-drawer-container'));
      containers.forEach((container, idx) => {
        const toggleButton = container.querySelector('.drawer-toggle');
        let content = container.querySelector('.drawer-content');
        if (!toggleButton || !content) return;

        if (!content.id) {
          content.id = `drawerContent_auto_${idx}`;
          toggleButton.setAttribute('aria-controls', content.id);
        }

        const storageKey = `drawerState:${content.id}`;
        const persisted = localStorage.getItem(storageKey);
        const defaultOpen = toggleButton.classList.contains('open') || content.classList.contains('open') || toggleButton.getAttribute('aria-expanded') === 'true';
        const isOpen = persisted === 'open' ? true : (persisted === 'closed' ? false : defaultOpen);
        
        toggleButton.classList.toggle('collapsed', !isOpen);
        toggleButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        content.classList.toggle('open', isOpen);
        content.setAttribute('aria-hidden', isOpen ? 'false' : 'true');

        toggleButton.addEventListener('click', () => {
          const nowOpen = content.classList.toggle('open');
          toggleButton.classList.toggle('collapsed', !nowOpen);
          toggleButton.setAttribute('aria-expanded', nowOpen ? 'true' : 'false');
          content.setAttribute('aria-hidden', nowOpen ? 'false' : 'true');
          try { localStorage.setItem(storageKey, nowOpen ? 'open' : 'closed'); } catch(_) {}
        });
      });
    }

    /**
     * Main initialization method called after setup
     */
    init() {
      try { this.persistRestore(); } catch(_) {}
      // restore lock state if present
      try {
        const lk = localStorage.getItem(this.LOCK_KEY);
        if (lk === '1' || lk === 'true') this.applyLockState(true);
        else this.applyLockState(false);
      } catch(_) {}
      this.recomputeAll();
      this.updateFinalGrades();
      // Schedule an initial server-side compute shortly after startup to populate authoritative values
      try {
        setTimeout(() => { try { this.computeServerForAll(); } catch(_){} }, 250);
      } catch(_) {}
    }
  }

  // Initialize when DOM is ready (or immediately if DOMContentLoaded already fired)
  const __initGradeSystem = () => {
    const gradeSystem = new GradeManagementSystem();
    gradeSystem.setup();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', __initGradeSystem);
  } else {
    // DOM is already ready — initialize immediately to avoid missing the event and leaving UI uninitialized
    __initGradeSystem();
  }

})();
