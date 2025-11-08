// JS for instructor_grades_unified.html: Compute TOTAL using backend API

document.addEventListener('DOMContentLoaded', function() {
  // Find all rows in the grade matrix
  const tbody = document.getElementById('tbody');
  if (!tbody) return;

  // Helper: get assessment input values for a row and subcategory
  function getAssessmentScores(tr, group) {
    return (group.ids || []).map(id => {
      const inp = tr.querySelector(`input.score[data-assessment="${id}"]`);
      return inp && inp.value !== '' ? parseFloat(inp.value) : 0;
    });
  }

  // Use backend API to compute TOTAL for a subcategory in a row
  async function computeTotalAPI(scores) {
    try {
      const res = await fetch('/api/grade-entry/compute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scores })
      });
      if (!res.ok) return null;
      const data = await res.json();
      return data && typeof data.TOTAL === 'number' ? data.TOTAL : null;
    } catch {
      return null;
    }
  }

  // Build subcategory groups from table headers (reuse logic from inline script if needed)
  function buildSubGroups() {
    const heads = Array.from(document.querySelectorAll('th.assess-col'));
    const groups = {};
    heads.forEach(th => {
      const category = th.getAttribute('data-category');
      const subcategory = th.getAttribute('data-subcategory');
      const id = parseInt(th.getAttribute('data-assessment-id') || '0', 10);
      const max = parseFloat(th.getAttribute('data-max') || '0') || 0;
      const subweight = parseFloat(th.getAttribute('data-subweight') || '0') || 0;
      const key = `${category}::${subcategory}`;
      if (!groups[key]) groups[key] = { category, subcategory, ids: [], maxes: [], maxTotal: 0, subweight };
      groups[key].ids.push(id);
      groups[key].maxes.push(max);
      groups[key].maxTotal += max;
      if (!groups[key].subweight && subweight) groups[key].subweight = subweight;
    });
    return groups;
  }
  const SUB_GROUPS = buildSubGroups();

  // Update TOTAL cell for a row and subcategory using backend
  async function updateTotalCell(tr, group) {
    const scores = getAssessmentScores(tr, group);
    // Compute locally first for immediate UI feedback
    const localTotal = (scores || []).reduce((acc, v) => acc + (Number.isFinite(v) ? v : 0), 0);
    const totalCell = tr.querySelector(`td.computed.total-col[data-category="${group.category}"][data-subcategory="${group.subcategory}"]`);
    if (totalCell) totalCell.textContent = localTotal.toFixed(2);
    // Then optionally verify with backend; if backend returns a numeric TOTAL, overwrite (non-blocking)
    computeTotalAPI(scores).then(total => {
      if (total !== null && totalCell) {
        totalCell.textContent = Number(total).toFixed(2);
      }
    }).catch(() => {});
  }

  // Recompute all TOTALs on page load
  async function recomputeAllTotals() {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    for (const tr of rows) {
      for (const group of Object.values(SUB_GROUPS)) {
        await updateTotalCell(tr, group);
      }
    }
  }

  // Listen for input changes and update TOTAL for the affected row/subcategory
  tbody.addEventListener('input', function(e) {
    const inp = e.target;
    if (!inp.matches('input.score')) return;
    const tr = inp.closest('tr');
    for (const group of Object.values(SUB_GROUPS)) {
      if (group.ids.includes(parseInt(inp.getAttribute('data-assessment')))) {
        updateTotalCell(tr, group);
      }
    }
  });

  // Initial compute
  recomputeAllTotals();
});
