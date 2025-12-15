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

  // escape for safe insertion into html strings
  const escapeHtml = (s) => {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
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
      this.classType = 'MAJOR';
      this.isMinor = false;
      this.latestSummaries = {};

      // Configuration
      this.INPUT_PERSISTENCE_ENABLED = true;
      this.SCROLL_PERSIST_ENABLED = true;
      this.PERSIST_KEY = '';
      this.inputsLocked = false;
      this._tempAssessmentCounter = -1;
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
        this.applyClassTypeDecorations();
        // If page is in limited (student) view, prune final-grade table and hide controls
        try { this.applyLimitedViewConstraints(); } catch(_) {}
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
      // Respect limited-view flags set by server when students open the page
      this.limitedView = String(this.dataEl?.dataset?.limitedView || '0') === '1';
      this.currentStudentId = String(parseInt(this.dataEl?.dataset?.currentStudent || '0', 10) || 0);
      const typeAttr = this.dataEl?.dataset?.classType || 'MAJOR';
      this.classType = String(typeAttr).toUpperCase();
      this.isMinor = this.classType === 'MINOR';
      this.actionsBox = document.getElementById('structure-actions');

      // Return false if tbody is not found
      return !!this.tbody;
    }

    /**
     * Apply client-side constraints when the page is opened in limited (student) view
     * - Remove other students from final-grade table
     * - Hide save/recalc/actions controls
     */
    applyLimitedViewConstraints() {
      if (!this.limitedView) return;
      const cs = String(this.currentStudentId || '0');
      try {
        // Remove other students from final-grade table
        const finalTbody = document.querySelector('table.final-grade-table tbody');
        if (finalTbody) {
          Array.from(finalTbody.querySelectorAll('tr')).forEach(tr => {
            const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
            if (sid !== cs) tr.remove();
          });
        }

        // For the main grade matrix: unlock empty inputs for the current student,
        // and lock (readonly) inputs that already have values so students can't overwrite existing scores.
        const tbodyRows = Array.from(this.tbody.querySelectorAll('tr'));
        tbodyRows.forEach(tr => {
          const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
          if (sid !== cs) {
            // remove other student rows entirely
            tr.remove();
            return;
          }
          // For current student row, enable all inputs (including those with existing values)
          tr.querySelectorAll('input.score').forEach(inp => {
            try {
              inp.removeAttribute('disabled');
              inp.readOnly = false;
              inp.classList.remove('score-locked');
            } catch(_) {}
          });
        });
      } catch(_) {}

      // Hide server-affecting controls (save/submit) — student changes are local-only
      try { if (this.saveBtn) this.saveBtn.style.display = 'none'; } catch(_) {}
      try { if (this.recalcBtn) this.recalcBtn.style.display = 'none'; } catch(_) {}
      try { document.querySelectorAll('button[data-action="submit-inputs"]').forEach(b=>b.style.display='none'); } catch(_) {}
      try { const actions = document.getElementById('structure-actions'); if (actions) actions.style.display = 'none'; } catch(_) {}

      // Add a client-only 'Add Temp Assessment' button to allow theoretical inputs
      try {
        if (!document.getElementById('add-temp-assessment-btn')) {
          const btn = document.createElement('button');
          btn.id = 'add-temp-assessment-btn';
          btn.type = 'button';
          btn.className = 'btn btn-sm btn-outline-secondary';
          btn.textContent = 'Add Temp Assessment';
          btn.style.marginLeft = '8px';
          btn.addEventListener('click', (ev) => { ev.preventDefault(); this.addTemporaryAssessment(); });
          const container = document.getElementById('structure-actions') || document.getElementById('page-data') || document.body;
          container.appendChild(btn);
        }
      } catch(_) {}
    }

    /**
     * Add a temporary, client-only assessment column. These use negative IDs and
     * are not sent to the server; they are removed on page refresh.
     */
    addTemporaryAssessment() {
      try {
        // generate a new negative ID
        const aid = this._tempAssessmentCounter = (this._tempAssessmentCounter - 1);
        const strAid = String(aid);

        // Find header row to append to
        const thead = document.querySelector('table.matrix thead');
        if (!thead) return;
        // choose last header row that contains assess-col
        let headerRow = null;
        Array.from(thead.querySelectorAll('tr')).forEach(r => { if (r.querySelector('th.assess-col')) headerRow = r; });
        if (!headerRow) headerRow = thead.querySelector('tr') || thead;

        const th = document.createElement('th');
        th.className = 'assess-col temporary';
        th.setAttribute('data-assessment-id', strAid);
        th.setAttribute('data-category', 'LECTURE');
        th.setAttribute('data-subcategory', 'TEMP');
        th.setAttribute('data-max', '100');
        th.setAttribute('data-subweight', '0');
        th.textContent = `Temp ${Math.abs(aid)}`;
        headerRow.appendChild(th);

        // Add corresponding cells for each student row (should be only current student)
        const rows = Array.from(this.tbody.querySelectorAll('tr'));
        rows.forEach(tr => {
          const td = document.createElement('td');
          td.className = 'assess-col-cell';
          const inp = document.createElement('input');
          inp.type = 'number';
          inp.className = 'score';
          inp.setAttribute('data-assessment', strAid);
          inp.setAttribute('data-student', tr.getAttribute('data-student-id') || tr.getAttribute('data-student') || '0');
          inp.setAttribute('max', '100');
          inp.value = '';
          td.appendChild(inp);
          tr.appendChild(td);
        });

        // Rebuild groups and recompute locally
        try { this.buildSubGroups(); } catch(_) {}
        try { this.recomputeAll(); this.updateFinalGrades(); } catch(_) {}
      } catch (err) { console.error('addTemporaryAssessment failed', err); }
    }

    /**
     * Get grouped assessments from JSON element
     */
    async computeServerForAll() {
      // Do not call server when in limited (student) view — keep computations local-only
      if (this.limitedView) {
        try { this.recomputeAll(); this.updateFinalGrades(); } catch(_) {}
        return;
      }
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

        if (this.isMinor && out.summaries && typeof out.summaries === 'object') {
          this.latestSummaries = out.summaries;
        } else {
          this.latestSummaries = {};
        }
        
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
     * Suggest a next assessment name for a given category/subcategory
     * Returns an object { suggested, base, index, lsKey }
     */
    nextNameSuggestion(category, subcategory, subcategoryId) {
      const baseCandidate = (subcategory && String(subcategory).trim()) || 'Assessment';
      const lsKey = `nextName:${this.classId}:${subcategory || ''}`;
      let maxIdx = 0;
      let seenExact = false;

      try {
        const heads = Array.from(document.querySelectorAll('th.assess-col')).map(th => th.textContent.trim()).filter(Boolean);
        heads.forEach(h => {
          if (!h) return;
          if (h === baseCandidate) { seenExact = true; return; }
          const m = h.match(new RegExp(`^${baseCandidate}\\s*(\\d+)$`, 'i'));
          if (m && m[1]) {
            const idx = parseInt(m[1], 10);
            if (!isNaN(idx)) maxIdx = Math.max(maxIdx, idx);
          }
        });
      } catch (_) {}

      if (maxIdx > 0) return { suggested: `${baseCandidate} ${maxIdx + 1}`, base: baseCandidate, index: maxIdx + 1, lsKey };
      if (seenExact) return { suggested: `${baseCandidate} 2`, base: baseCandidate, index: 2, lsKey };
      return { suggested: `${baseCandidate} 1`, base: baseCandidate, index: 1, lsKey };
    }

    /**
     * Parse an assessment name and extract a base and numeric index if present.
     * e.g. 'Assessment 2' -> { base: 'Assessment', index: 2 }
     */
    parseName(name) {
      const out = {};
      if (!name) return out;
      const s = String(name).trim();
      // Match trailing integer with optional separator (space or hyphen)
      const m = s.match(/^(.*?)[\s\-]*([0-9]+)$/);
      if (m) {
        const base = (m[1] || '').trim() || s;
        const idx = parseInt(m[2], 10);
        out.base = base;
        if (!isNaN(idx)) out.index = idx;
      } else {
        out.base = s;
      }
      return out;
    }

    /**
     * Return grouped assessments object parsed from the `#ga-json` script or cached value.
     * Ensures a plain object is always returned.
     */
    getGrouped() {
      try {
        if (this.GROUPED_CACHE && typeof this.GROUPED_CACHE === 'object') return this.GROUPED_CACHE;
        const gaEl = document.getElementById('ga-json');
        if (!gaEl) return (this.GROUPED_CACHE = {});
        try {
          const parsed = JSON.parse(gaEl.textContent || gaEl.innerText || '{}') || {};
          this.GROUPED_CACHE = parsed;
          return parsed;
        } catch (e) {
          this.GROUPED_CACHE = {};
          return {};
        }
      } catch (_) {
        return {};
      }
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
      let rows = Array.from(this.tbody.querySelectorAll('tr'));
      if (this.limitedView && this.currentStudentId) {
        const cs = String(this.currentStudentId);
        rows = rows.filter(tr => {
          const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
          return sid === cs;
        });
      }
      return rows;
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

    applyClassTypeDecorations() {
      const rawHdr = document.querySelector('table.final-grade-table thead th.raw-grade-header');
      const totalHdr = document.querySelector('table.final-grade-table thead th.total-grade-header');
      if (!rawHdr || !totalHdr) return;
      if (this.isMinor) {
        rawHdr.textContent = 'INITIAL GRADE';
        totalHdr.textContent = 'FINAL GRADE';
      } else {
        rawHdr.textContent = 'RAW GRADE';
        totalHdr.textContent = 'TOTAL GRADE';
      }
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
        if (this.limitedView) {
          // In limited (student) view, do local recompute only — do NOT call server compute
          this.serverComputeTimer = setTimeout(() => { try { this.recomputeAll(); this.updateFinalGrades(); } catch(_){}; this.serverComputeTimer = null; }, 400);
        } else {
          this.serverComputeTimer = setTimeout(() => { this.computeServerForAll(); this.serverComputeTimer = null; }, 800);
        }
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
            const ok = await this.saveAndSnapshot();
            if (ok) {
              // Lock inputs after successful submit so instructor must unlock to edit again
              try { this.applyLockState(true); } catch(_) {}
              // reflect state on all toggle buttons
              document.querySelectorAll('button[data-action="toggle-lock"]').forEach(b => b.classList.toggle('locked', !!this.inputsLocked));
            }
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
      
      // Single Swal modal collecting name, max score, and quantity
      let nameFinal, maxFinal, qtyFinal;
      if (!SwalLib) {
        let name = await swalPromptText(`New assessment for ${subcategory}`, suggest.suggested);
        if (name == null) return;
        name = String(name).trim();
        if (!name) { await swalAlert('warning', 'Name required', 'Please enter an assessment name.'); return; }
        let maxStr = await swalPromptNumber('Max score (e.g., 100)', 100);
        if (maxStr == null) return;
        const max = parseFloat(maxStr);
        if (!isFinite(max) || max <= 0) { await swalAlert('warning', 'Invalid max score', 'Please enter a positive number.'); return; }
        let qtyStr = window.prompt('Quantity to create (e.g. 1)', '1');
        if (qtyStr == null) return;
        const qty = parseInt(qtyStr, 10) || 1;
        nameFinal = name;
        maxFinal = max;
        qtyFinal = Math.max(1, Math.min(qty, 50));
      } else {
        const html = `
          <div style="text-align:left">
            <label style="font-weight:600;font-size:13px;margin-bottom:6px;display:block">Assessment name</label>
            <input id="swal-name" class="swal2-input" value="${escapeHtml(suggest.suggested)}">

            <label style="font-weight:600;font-size:13px;margin-top:8px;margin-bottom:6px;display:block">Max score</label>
            <input id="swal-max" type="number" class="swal2-input" min="1" step="0.01" value="100">

            <label style="font-weight:600;font-size:13px;margin-top:8px;margin-bottom:6px;display:block">Quantity</label>
            <input id="swal-qty" type="number" class="swal2-input" min="1" step="1" value="1">
          </div>
        `;
        const res = await SwalLib.fire({
          title: `New assessment for ${escapeHtml(subcategory)}`,
          html: html,
          showCancelButton: true,
          confirmButtonText: 'Create',
          focusConfirm: false,
          preConfirm: () => {
            const popup = SwalLib.getPopup();
            const n = popup.querySelector('#swal-name')?.value || '';
            const m = popup.querySelector('#swal-max')?.value || '';
            const q = popup.querySelector('#swal-qty')?.value || '1';
            return { name: n, max: m, qty: q };
          }
        });
        if (!res || !res.isConfirmed) return;
        nameFinal = String((res.value && res.value.name) || '').trim();
        maxFinal = parseFloat((res.value && res.value.max) || '');
        qtyFinal = parseInt((res.value && res.value.qty) || '1', 10) || 1;
        qtyFinal = Math.max(1, Math.min(qtyFinal, 50)); // safety cap
        if (!nameFinal) { await swalAlert('warning', 'Name required', 'Please enter an assessment name.'); return; }
        if (!isFinite(maxFinal) || maxFinal <= 0) { await swalAlert('warning', 'Invalid max score', 'Please enter a positive number.'); return; }
      }
      if (!subcategoryId) { await swalAlert('error', 'Subcategory mapping missing', 'Please refresh this page and try again.'); return; }

      // Prepare the sequence of names to create
      try {
        const parsed = this.parseName(nameFinal || '');
        const base = parsed.base || suggest.base || 'Assessment';
        const startIdx = parsed.index || (suggest && suggest.index) || 1;
        const toCreate = [];
        if ((qtyFinal === 1) && !parsed.index) {
          // preserve exact user input when quantity is 1 and user didn't include an index
          toCreate.push(nameFinal);
        } else {
          for (let i = 0; i < qtyFinal; i++) {
            const idx = startIdx + i;
            toCreate.push(`${base} ${idx}`);
          }
        }

        // Show loading modal while performing requests
        if (SwalLib) {
          // show loading modal but do not await it (we will close programmatically)
          SwalLib.fire({ title: 'Creating assessments...', allowOutsideClick: false, didOpen: () => { SwalLib.showLoading(); } });
        }

        const headers2Base = { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' };
        if (this.csrfToken) headers2Base['X-CSRFToken'] = this.csrfToken;

        const G = this.getGrouped();
        G[category] = G[category] || {};
        G[category][subcategory] = G[category][subcategory] || [];

        const created = [];
        const failed = [];
        for (let i = 0; i < toCreate.length; i++) {
          const cname = toCreate[i];
          const payload = { name: cname, subcategory_id: subcategoryId, max_score: maxFinal };
          const formBody = new URLSearchParams();
          Object.entries(payload).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') formBody.append(k, String(v)); });
          try {
            const r = await fetch('/api/assessments/simple', { method: 'POST', headers: headers2Base, body: formBody.toString() });
            let out = {};
            try { out = await r.json(); } catch (_) { out = {}; }
            if (!r.ok) {
              failed.push({ name: cname, status: r.status, error: out && out.error });
            } else {
              created.push(cname);
              try { G[category][subcategory].push({ name: cname, max_score: maxFinal }); } catch(_) {}
            }
          } catch (err) {
            failed.push({ name: cname, error: err && err.message });
          }
        }

        try { localStorage.setItem(`lastName:${this.classId}:${subcategoryId}`, String(toCreate[toCreate.length - 1] || '')); } catch(_) {}

        if (SwalLib) SwalLib.close();

        if (created.length && !failed.length) {
          await swalAlert('success', 'Assessments created', `${created.length} assessment(s) added under ${subcategory}.`);
          window.location.reload();
          return;
        }
        if (created.length && failed.length) {
          await swalAlert('warning', 'Partial success', `${created.length} created, ${failed.length} failed.`);
          window.location.reload();
          return;
        }
        // none created
        await swalAlert('error', 'Create failed', failed.length ? (failed[0].error || `Failed to create ${failed[0].name}`) : 'Unknown error');
      } catch (err) {
        if (SwalLib) SwalLib.close();
        console.error('handleAdd failed', err);
        const msg = err && err.message ? String(err.message) : 'Could not create assessment(s).';
        await swalAlert('error', 'Network error', msg);
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
          const res = await fetch(`/assessments/${assessmentId}/update_max`, { method: 'POST', headers, body: JSON.stringify({ max_score: newMax }) });
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
          const rdel = await fetch(`/assessments/${assessmentId}`, { method: 'DELETE', headers });
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
          const r = await fetch(`/assessments/${assessmentId}/update_max`, { method: 'POST', headers, body: JSON.stringify({ max_score: newMax }) });
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
     * Sends POST to `/classes/<classId>/save-snapshot` with payload { scores: [...] }
     */
    async saveAndSnapshot() {
      // Prevent saving from limited (student) view — limited view is for local/theoretical edits only
      if (this.limitedView) {
        try { await swalAlert('info', 'Limited view', 'Changes in limited view are local-only and will not be saved to the official gradebook.'); } catch(_) {}
        this.status.textContent = 'Limited view — no save performed';
        return false;
      }
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
        const res = await fetch(`/classes/${classId}/save-snapshot`, { method: 'POST', headers, body: JSON.stringify({ scores }) });
        const out = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.status.textContent = out.error || 'Save failed';
          await swalAlert('error', 'Save failed', out.error || out.message || 'Unknown error');
          return false;
        } else {
          this.status.textContent = 'All changes saved — snapshot created';
          // clear dirty state and persisted drafts
          try { this.dirty.clear(); } catch(_) {}
          try { this.persistClear(); } catch(_) {}
          await swalAlert('success', 'Saved', `Snapshot version ${out.version || ''} created.`);
          // request fresh compute values from server to update UI
          try { this.computeServerForAll(); } catch(_) {}
          return true;
        }
      } catch (err) {
        console.error(err);
        this.status.textContent = 'Network error';
        await swalAlert('error', 'Network error', 'Could not save snapshot.');
        return false;
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
      this.latestSummaries = {};
      // Recompute derived cells and final grades
      try { this.recomputeAll(); this.updateFinalGrades(); } catch(_) {}
      if (this.status) this.status.textContent = 'Cleared inputs';
    }

    /**
     * Apply lock state to inputs (true = locked/disabled)
     */
    applyLockState(locked) {
      this.inputsLocked = !!locked;
      // If in limited (student) view, we should not disable inputs (students can edit locally)
      const effectiveLocked = this.limitedView ? false : !!this.inputsLocked;
      // Disable/enable input fields
      document.querySelectorAll('input.score').forEach(inp => { try { inp.disabled = effectiveLocked; } catch(_) {} });
      // Disable/enable add/edit assessment controls and important buttons
      const controls = Array.from(document.querySelectorAll('button[data-action="add-assessment"], button[data-action="add-assessment-select"], button[data-action="edit-assessment"], #save-btn, #recalc-btn'));
      controls.forEach(el => { try { el.disabled = effectiveLocked; } catch(_) {} });
      // No visual overlay — simply enable/disable inputs and controls when locked
      // Persist lock state
      try { localStorage.setItem(this.LOCK_KEY, this.inputsLocked ? '1' : '0'); } catch(_) {}
      // Update related UI buttons (reflect the logical locked state even if inputs stay enabled in limited view)
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

      // Resolve final grade cells; fall back to global selectors if structure differs
      let gradeMarkCell = finalRow.querySelector('td.grade-mark');
      if (!gradeMarkCell) gradeMarkCell = document.querySelector(`table.final-grade-table td.grade-mark[data-student="${sid}"]`);
      let remarksCell = finalRow.querySelector('td.remarks');
      if (!remarksCell) remarksCell = document.querySelector(`table.final-grade-table td.remarks[data-student="${sid}"]`);

      if (!hasAnyInputValue) {
        if (rawCell) rawCell.textContent = '';
        if (totalCell) totalCell.textContent = '';
        if (gradeMarkCell) gradeMarkCell.textContent = '';
        if (remarksCell) remarksCell.textContent = '';
        return;
      }

      const lecVal = isNaN(lecture) ? 0 : lecture;
      const labVal = isNaN(lab) ? 0 : lab;
      const baseRaw = Math.round((labVal * 0.4 + lecVal * 0.6) * 100) / 100;
      const summary = (this.latestSummaries && this.latestSummaries[sid]) ? this.latestSummaries[sid] : null;
      let rawValue = baseRaw;
      let totalGrade;
      if (this.isMinor) {
        totalGrade = Math.round((baseRaw * 0.5 + 50) * 100) / 100;
      } else {
        totalGrade = Math.round((baseRaw * 0.625 + 37.5) * 100) / 100;
      }

      if (summary) {
        if (typeof summary.initial_grade === 'number') {
          rawValue = Math.round(summary.initial_grade * 100) / 100;
        }
        if (typeof summary.final_grade === 'number') {
          totalGrade = Math.round(summary.final_grade * 100) / 100;
        }
      }

      if (rawCell) rawCell.textContent = rawValue.toFixed(2);
      if (totalCell) totalCell.textContent = totalGrade.toFixed(2);

      // Compute GRADE MARK from TOTAL GRADE (VL7 equivalent)
      if (gradeMarkCell) {
        const t = totalGrade;
        let gm = '';
        if (summary && summary.equivalent !== undefined && summary.equivalent !== null && summary.equivalent !== '') {
          gm = String(summary.equivalent);
        } else if (!isNaN(t)) {
          if (t < 75) gm = '5.0';
          else if (t < 77) gm = '3.0';
          else if (t < 80) gm = '2.75';
          else if (t < 83) gm = '2.5';
          else if (t < 86) gm = '2.25';
          else if (t < 89) gm = '2.0';
          else if (t < 92) gm = '1.75';
          else if (t < 95) gm = '1.5';
          else gm = '1.25';
        }
        gradeMarkCell.textContent = gm;
      }

      // Compute REMARKS: check for missing assessments based on existing subcategories.
      // Check if any subcategory contains keywords, and if so, check if all assessments in that subcategory are filled.
      if (remarksCell) {
        const heads = Array.from(document.querySelectorAll('th.assess-col'));
        const subcats = {};
        heads.forEach(h => {
          const sub = h.getAttribute('data-subcategory') || '';
          if (!sub) return;
          if (!subcats[sub]) subcats[sub] = [];
          subcats[sub].push(h.getAttribute('data-assessment-id'));
        });

        const checkSubcategoryMissing = (keywords) => {
          for (const [subName, ids] of Object.entries(subcats)) {
            const subLower = subName.toLowerCase();
            if (keywords.some(k => subLower.includes(k))) {
              // This subcategory matches, check if any assessment in it is missing
              const anyMissing = ids.some(id => {
                const inp = tr.querySelector(`input.score[data-assessment="${id}"]`);
                return inp ? (String(inp.value).trim() === '') : false;
              });
              if (anyMissing) return true;
            }
          }
          return false;
        };

        // Determine remarks based on grade mark and missing assessments
        let remarks = 'PASSED';
        try {
          const gmText = (gradeMarkCell && gradeMarkCell.textContent) ? String(gradeMarkCell.textContent).trim() : '';
          const gmNum = parseFloat(gmText);
          if (!isNaN(gmNum)) {
            // Passing if grade mark <= 3.00, fail otherwise
            if (gmNum > 3.0) remarks = 'FAILED';
          } else {
            // Non-numeric grade mark values
            if (gmText === 'INC') remarks = 'INCOMPLETE';
            else if (gmText === 'DRP') remarks = 'DROPPED';
            else if (gmText === '5.0') remarks = 'FAILED';
          }
        } catch(_) {}

        // Check for missing assessments in any subcategory
        if (remarks === 'PASSED' || remarks === 'FAILED') {
          for (const [subName, ids] of Object.entries(subcats)) {
            const anyMissing = ids.some(id => {
              const inp = tr.querySelector(`input.score[data-assessment="${id}"]`);
              return inp ? (String(inp.value).trim() === '') : false;
            });
            if (anyMissing) {
              remarks = `NO ${subName.toUpperCase()}`;
              break; // Show the first missing subcategory
            }
          }
        }

        // Apply remark text
        remarksCell.textContent = remarks;

        // Color coding: failed=red, minimum(3.00)=orange, between 1.75 and 3.00=yellow, otherwise passed=green
        try {
          const clsList = ['text-passed','text-failed','text-minimum','text-mid'];
          remarksCell.classList.remove(...clsList);
          if (gradeMarkCell) gradeMarkCell.classList.remove(...clsList);

          // Determine class from grade mark if available
          const gmText = (gradeMarkCell && gradeMarkCell.textContent) ? String(gradeMarkCell.textContent).trim() : '';
          const gmNum = parseFloat(gmText);

          let clsToApply = null;
          if (remarks === 'FAILED') {
            clsToApply = 'text-failed';
          } else if (!isNaN(gmNum)) {
            if (gmNum > 3.0) clsToApply = 'text-failed';
            else if (Math.abs(gmNum - 3.0) < 1e-9) clsToApply = 'text-minimum';
            else if (gmNum > 1.75 && gmNum < 3.0) clsToApply = 'text-mid';
            else clsToApply = 'text-passed';
          } else {
            // Non-numeric grade mark -> leave as passed unless explicitly failed
            if (gmText === 'INC' || gmText === 'DRP' || gmText === '5.0') clsToApply = 'text-failed';
            else clsToApply = 'text-passed';
          }

          if (clsToApply) {
            try { remarksCell.classList.add(clsToApply); } catch(_) {}
            try { if (gradeMarkCell) gradeMarkCell.classList.add(clsToApply); } catch(_) {}
          }
        } catch(_) {}
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
      // Do not call server when in limited (student) view — keep computations local-only
      if (this.limitedView) {
        try { this.recomputeAll(); this.updateFinalGrades(); } catch(_) {}
        return;
      }
      try {
        const groupsPayload = {};
        Object.entries(this.SUB_GROUPS).forEach(([k, g]) => {
          groupsPayload[k] = {
            ids: Array.isArray(g.ids) ? g.ids.slice() : [],
            maxes: Array.isArray(g.maxes) ? g.maxes.slice() : [],
            maxTotal: g.maxTotal || 0,
            subweight: g.subweight || 0
          };
        });

        const studentsPayload = this.getStudentRows().map(tr => {
          const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
          const scores = {};
          tr.querySelectorAll('input.score').forEach(inp => {
            const aid = String(parseInt(inp.getAttribute('data-assessment')||'0',10)||0);
            scores[aid] = inp.value === '' ? null : Number(inp.value);
          });
          return { sid, scores };
        });

        const payload = { groups: groupsPayload, students: studentsPayload };
        const headers = { 'Content-Type': 'application/json' };
        if (this.csrfToken) headers['X-CSRFToken'] = this.csrfToken;

        const res = await fetch('/api/grade-entry/compute', { method: 'POST', headers, body: JSON.stringify(payload) });
        if (!res.ok) return;
        const out = await res.json();

        if (this.isMinor && out.summaries && typeof out.summaries === 'object') {
          this.latestSummaries = out.summaries;
        } else {
          this.latestSummaries = {};
        }

        this.getStudentRows().forEach(tr => {
          const sid = String(parseInt(tr.getAttribute('data-student-id')||'0',10)||0);
          const byGroup = (out.results && out.results[sid]) ? out.results[sid] : {};
          Object.entries(byGroup).forEach(([gkey, vals]) => {
            const parts = gkey.split('::');
            const cat = parts[0] || '';
            const sub = parts[1] || '';
            const totalCell = tr.querySelector(`td.computed.total-col[data-category="${cat}"][data-subcategory="${sub}"]`);
            const equivCell = tr.querySelector(`td.computed.equiv-col[data-category="${cat}"][data-subcategory="${sub}"]`);
            const reqpctCell = tr.querySelector(`td.computed.reqpct-col[data-category="${cat}"][data-subcategory="${sub}"]`);
            if (totalCell && vals.total !== undefined && vals.total !== null) totalCell.textContent = Number(vals.total).toFixed(2);
            if (equivCell && vals.eq_pct !== undefined && vals.eq_pct !== null) equivCell.textContent = Number(vals.eq_pct).toFixed(2);
            if (reqpctCell) {
              if (vals.reqpct_display !== undefined && vals.reqpct_display !== null) {
                reqpctCell.textContent = Number(vals.reqpct_display).toFixed(2);
              } else if (vals.reqpct !== undefined && vals.reqpct !== null) {
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
        if (!this.limitedView) {
          setTimeout(() => { try { this.computeServerForAll(); } catch(_){} }, 250);
        }
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
