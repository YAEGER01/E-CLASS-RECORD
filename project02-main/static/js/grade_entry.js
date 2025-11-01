document.addEventListener('DOMContentLoaded', async () => {
  const classId = window.location.pathname.split('/').pop();
  const assessmentsList = document.getElementById('assessments-list');
  const createBtn = document.getElementById('create-assessment');
  const aName = document.getElementById('a-name');
  const aSub = document.getElementById('a-sub');
  const aMax = document.getElementById('a-max');
  const aDate = document.getElementById('a-date');
  const assSaveStatus = document.getElementById('ass-save-status');
  const scoresArea = document.getElementById('scores-area');
  const bulkSave = document.getElementById('bulk-save');
  const scoresStatus = document.getElementById('scores-status');

  async function loadAssessments() {
    assessmentsList.textContent = 'Loading...';
    try {
      const res = await fetch(`/api/assessments?class_id=${classId}`);
      const data = await res.json();
      assessmentsList.innerHTML = '';
      data.assessments.forEach(a => {
        const div = document.createElement('div');
        div.textContent = `${a.name} — ${a.subcategory || 'N/A'} — Max: ${a.max_score}`;
        div.dataset.id = a.id;
        div.style.cursor = 'pointer';
        div.addEventListener('click', () => loadStudentsForAssessment(a.id, a.name));
        assessmentsList.appendChild(div);
      });
    } catch (e) {
      assessmentsList.textContent = 'Failed to load assessments';
    }
  }

  async function loadStudentsForAssessment(aid, aname) {
    scoresArea.innerHTML = `<h3>Scores for ${aname}</h3><div id="students-list">Loading students...</div>`;
    try {
      const res = await fetch(`/api/scores?assessment_id=${aid}`);
      const data = await res.json();
      const studentsList = document.getElementById('students-list');
      studentsList.innerHTML = '';
      // If API returned scores array, render editable rows
      (data.scores || []).forEach(s => {
        const row = document.createElement('div');
        row.innerHTML = `Student ${s.student_id}: <input data-score-id="${s.id}" data-student-id="${s.student_id}" value="${s.score}" />`;
        studentsList.appendChild(row);
      });
      // allow adding new rows
      const addRow = document.createElement('div');
      addRow.innerHTML = `Add: Student ID <input id="new-student" /> Score <input id="new-score" /> <button id="add-row">Add</button>`;
      studentsList.appendChild(addRow);
      document.getElementById('add-row').addEventListener('click', () => {
        const sid = document.getElementById('new-student').value;
        const sc = document.getElementById('new-score').value;
        if (!sid) return;
        const row = document.createElement('div');
        row.innerHTML = `Student ${sid}: <input data-student-id="${sid}" value="${sc}" />`;
        studentsList.insertBefore(row, addRow);
      });
    } catch (e) {
      scoresArea.textContent = 'Failed to load scores';
    }
  }

  createBtn.addEventListener('click', async () => {
    assSaveStatus.textContent = 'Saving...';
    try {
      const payload = {
        name: aName.value,
        class_id: parseInt(classId),
        subcategory: aSub.value,
        max_score: parseFloat(aMax.value) || 100,
        assessment_date: aDate.value || null
      };
      const res = await fetch('/api/assessments', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const out = await res.json();
      if (res.ok) { assSaveStatus.textContent = 'Saved'; loadAssessments(); } else { assSaveStatus.textContent = out.error || 'Save failed'; }
    } catch (e) { assSaveStatus.textContent = 'Network error'; }
  });

  bulkSave.addEventListener('click', async () => {
    scoresStatus.textContent = 'Collecting...';
    try {
      // collect all inputs under students-list
      const studentsList = document.getElementById('students-list');
      if (!studentsList) return scoresStatus.textContent = 'No assessment selected';
      const rows = Array.from(studentsList.querySelectorAll('div'));
      const scores = [];
      rows.forEach(r => {
        const inp = r.querySelector('input');
        if (!inp) return;
        const sid = inp.dataset.studentId || inp.getAttribute('data-student-id') || inp.value;
        const sc = inp.value;
        if (sid && sc !== undefined) scores.push({student_id: parseInt(sid), assessment_id: parseInt(window.location.pathname.split('/').pop()), score: parseFloat(sc)});
      });
      const res = await fetch('/api/scores', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({scores})});
      const out = await res.json();
      if (res.ok) scoresStatus.textContent = 'Saved'; else scoresStatus.textContent = out.error || 'Save failed';
    } catch (e) { scoresStatus.textContent = 'Network error'; }
  });

  await loadAssessments();
});