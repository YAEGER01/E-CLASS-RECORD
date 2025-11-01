// Grade computation test based on TEMPLATE.xlsx logic
document.addEventListener('DOMContentLoaded', function() {
    const structureJson = {
        "LABORATORY": [
            {
                "name": "LAB TINGS",
                "weight": 50,
                "assessments": [
                    {"name": "Wan Ting", "max_score": 50, "id": 1},
                    {"name": "Tu Ting", "max_score": 50, "id": 2}
                ]
            },
            {
                "name": "LAB TINGALINGS",
                "weight": 50,
                "assessments": [
                    {"name": "Ting", "max_score": 100, "id": 3}
                ]
            }
        ],
        "LECTURE": []
    };

    // Display structure
    document.getElementById('structure-json').textContent = JSON.stringify(structureJson, null, 2);

    // Mock student data
    const mockStudents = [
        {id: 1, name: "Student A", scores: {1: 45, 2: 40, 3: 85}},
        {id: 2, name: "Student B", scores: {1: 50, 2: 50, 3: 100}},
        {id: 3, name: "Student C", scores: {1: 25, 2: 30, 3: 60}}
    ];

    // Populate table
    const tbody = document.getElementById('mock-tbody');
    mockStudents.forEach(student => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${student.name}</td>
            <td>${student.scores[1] || 0}</td>
            <td>${student.scores[2] || 0}</td>
            <td>${student.scores[3] || 0}</td>
            <td id="grade-${student.id}">--</td>
            <td id="equiv-${student.id}">--</td>
        `;
        tbody.appendChild(row);
    });

    // Compute function
    function computeGrade(scores) {
        let labTotal = 0;

        // LABORATORY computation
        structureJson.LABORATORY.forEach(sub => {
            let subTotal = 0;
            let subMax = 0;
            sub.assessments.forEach(assess => {
                const score = scores[assess.id] || 0;
                subTotal += score;
                subMax += assess.max_score;
            });
            const subPercentage = subMax > 0 ? (subTotal / subMax * 100) : 0;
            const weightedSub = subPercentage * (sub.weight / 100);
            labTotal += weightedSub;
        });

        // LECTURE is empty, so lecTotal = 0
        const lecTotal = 0;

        // Final percentage: Lab 40% + Lec 60%
        const finalPercentage = labTotal * 0.4 + lecTotal * 0.6;

        // Transmutation: score * 0.625 + 37.5
        const transmuted = finalPercentage * 0.625 + 37.5;

        // Grade equivalent
        let equiv;
        if (transmuted < 75) equiv = "5.0";
        else if (transmuted < 77) equiv = "3.0";
        else if (transmuted < 80) equiv = "2.75";
        else if (transmuted < 83) equiv = "2.5";
        else if (transmuted < 86) equiv = "2.25";
        else if (transmuted < 89) equiv = "2.0";
        else if (transmuted < 92) equiv = "1.75";
        else if (transmuted < 95) equiv = "1.5";
        else equiv = "1.25";

        return {
            labScore: labTotal.toFixed(2),
            lecScore: lecTotal.toFixed(2),
            finalPercentage: finalPercentage.toFixed(2),
            transmuted: transmuted.toFixed(2),
            equivalent: equiv
        };
    }

    // Compute button
    document.getElementById('compute-btn').addEventListener('click', function() {
        const results = document.getElementById('results');
        results.innerHTML = '<h2>Computation Results</h2>';

        mockStudents.forEach(student => {
            const grade = computeGrade(student.scores);
            document.getElementById(`grade-${student.id}`).textContent = grade.finalPercentage + '%';
            document.getElementById(`equiv-${student.id}`).textContent = grade.equivalent;

            results.innerHTML += `
                <div class="student-result">
                    <h3>${student.name}</h3>
                    <p>Lab Score: ${grade.labScore}%, Lec Score: ${grade.lecScore}%</p>
                    <p>Final %: ${grade.finalPercentage}%, Transmuted: ${grade.transmuted}, Equivalent: ${grade.equivalent}</p>
                </div>
            `;
        });
    });
});