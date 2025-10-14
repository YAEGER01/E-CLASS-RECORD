// Grade Setting Builder JavaScript

class GradeStructureBuilder {
    constructor() {
        this.structure = {
            name: 'Default Grading Structure',
            categories: []
        };
        this.currentClassId = null;
        this.currentStructureId = null;
        this.editingCategory = null;
        this.editingSubcategory = null;
        this.editingAssessment = null;

        this.initializeElements();
        this.bindEvents();
        this.updateWeightSummary();
    }

    initializeElements() {
        // Modal elements
        this.categoryModal = document.getElementById('category-modal');
        this.subcategoryModal = document.getElementById('subcategory-modal');
        this.assessmentModal = document.getElementById('assessment-modal');
        this.importModal = document.getElementById('import-modal');
        this.customCategoryModal = document.getElementById('custom-category-modal');

        // Form elements
        this.categoryForm = document.getElementById('category-form');
        this.subcategoryForm = document.getElementById('subcategory-form');
        this.assessmentForm = document.getElementById('assessment-form');

        // Structure elements
        this.structureNameInput = document.getElementById('structure-name');
        this.gradeStructureContainer = document.getElementById('grade-structure');

        // New category form elements
        this.categoryTypeSelect = document.getElementById('category-type');
        this.customCategoryNameInput = document.getElementById('custom-category-name');
        this.modalCustomNameInput = document.getElementById('modal-custom-name');
    }

    bindEvents() {
        // Structure name change
        this.structureNameInput?.addEventListener('input', (e) => {
            this.structure.name = e.target.value;
        });

        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target === this.categoryModal) this.closeCategoryModal();
            if (e.target === this.subcategoryModal) this.closeSubcategoryModal();
            if (e.target === this.assessmentModal) this.closeAssessmentModal();
            if (e.target === this.importModal) this.closeImportModal();
            if (e.target === this.customCategoryModal) this.closeCustomCategoryModal();
        });
    }

    // Category Management
    addCategory() {
        this.editingCategory = null;
        this.showCategoryModal();
    }

    editCategory(categoryId) {
        const category = this.findCategory(categoryId);
        if (!category) return;

        this.editingCategory = category;
        this.showCategoryModal(category);
    }

    showCategoryModal(category = null) {
        const title = document.getElementById('category-modal-title');
        const weightInput = document.getElementById('category-weight');
        const descriptionInput = document.getElementById('category-description');

        if (category) {
            title.textContent = 'Edit Category';
            // Set the category type based on the category name
            if (category.name.toUpperCase().includes('LECTURE')) {
                this.categoryTypeSelect.value = 'LECTURE';
            } else if (category.name.toUpperCase().includes('LABORATORY') || category.name.toUpperCase().includes('LAB')) {
                this.categoryTypeSelect.value = 'LABORATORY';
            } else {
                this.categoryTypeSelect.value = 'OTHER';
                this.customCategoryNameInput.value = category.name;
            }
            weightInput.value = category.weight;
            descriptionInput.value = category.description || '';
            this.customCategoryNameInput.style.display = this.categoryTypeSelect.value === 'OTHER' ? 'block' : 'none';
        } else {
            title.textContent = 'Add Category';
            this.categoryTypeSelect.value = '';
            this.customCategoryNameInput.value = '';
            weightInput.value = '';
            descriptionInput.value = '';
            this.customCategoryNameInput.style.display = 'none';
        }

        this.categoryModal.style.display = 'block';
        this.categoryModal.classList.add('show');
        this.categoryTypeSelect.focus();
    }

    closeCategoryModal() {
        this.categoryModal.classList.remove('show');
        setTimeout(() => {
            this.categoryModal.style.display = 'none';
        }, 300);
        this.categoryForm.reset();
    }

    saveCategory() {
        const categoryType = this.categoryTypeSelect.value;
        const customName = this.customCategoryNameInput.value.trim();
        const weightInput = document.getElementById('category-weight');
        const descriptionInput = document.getElementById('category-description');

        const weight = parseFloat(weightInput.value);
        const description = descriptionInput.value.trim();

        // Determine category name
        let categoryName = '';
        if (categoryType === 'OTHER') {
            if (!customName) {
                Swal.fire('Error', 'Custom category name is required when "Other" is selected', 'error');
                return;
            }
            categoryName = customName;
        } else if (categoryType === 'LECTURE') {
            categoryName = 'Lecture';
        } else if (categoryType === 'LABORATORY') {
            categoryName = 'Laboratory';
        } else {
            Swal.fire('Error', 'Please select a category type', 'error');
            return;
        }

        if (!weight || weight < 0) {
            Swal.fire('Error', 'Valid weight percentage is required', 'error');
            return;
        }

        if (this.editingCategory) {
            // Edit existing category
            this.editingCategory.name = categoryName;
            this.editingCategory.weight = weight;
            this.editingCategory.description = description;
            this.editingCategory.type = categoryType;
        } else {
            // Add new category
            const newCategory = {
                id: Date.now().toString(),
                name: categoryName,
                weight: weight,
                description: description,
                type: categoryType,
                subcategories: []
            };

            // Add predefined subcategories based on category type
            this.addPredefinedSubcategories(newCategory);

            this.structure.categories.push(newCategory);
        }

        this.closeCategoryModal();
        this.renderStructure();
        this.updateWeightSummary();
        this.validateWeights();

        Swal.fire('Success', `Category ${this.editingCategory ? 'updated' : 'added'} successfully`, 'success');
    }

    deleteCategory(categoryId) {
        Swal.fire({
            title: 'Delete Category?',
            text: 'This will also delete all subcategories and assessments. This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6b7280',
            confirmButtonText: 'Delete'
        }).then((result) => {
            if (result.isConfirmed) {
                this.structure.categories = this.structure.categories.filter(cat => cat.id !== categoryId);
                this.renderStructure();
                this.updateWeightSummary();
                this.validateWeights();
                Swal.fire('Deleted', 'Category has been deleted', 'success');
            }
        });
    }

    // Subcategory Management
    addSubcategory(categoryId) {
        this.editingSubcategory = null;
        this.currentCategoryId = categoryId;
        this.showSubcategoryModal();
    }

    editSubcategory(subcategoryId) {
        const subcategory = this.findSubcategory(subcategoryId);
        if (!subcategory) return;

        this.editingSubcategory = subcategory;
        this.showSubcategoryModal(subcategory);
    }

    showSubcategoryModal(subcategory = null) {
        const title = document.getElementById('subcategory-modal-title');
        const nameInput = document.getElementById('subcategory-name');
        const weightInput = document.getElementById('subcategory-weight');
        const maxScoreInput = document.getElementById('subcategory-max-score');
        const descriptionInput = document.getElementById('subcategory-description');

        if (subcategory) {
            title.textContent = 'Edit Subcategory';
            nameInput.value = subcategory.name;
            weightInput.value = subcategory.weight || '';
            maxScoreInput.value = subcategory.max_score;
            descriptionInput.value = subcategory.description || '';
        } else {
            title.textContent = 'Add Subcategory';
            nameInput.value = '';
            weightInput.value = '';
            maxScoreInput.value = '';
            descriptionInput.value = '';
        }

        this.subcategoryModal.style.display = 'block';
        this.subcategoryModal.classList.add('show');
        nameInput.focus();
    }

    closeSubcategoryModal() {
        this.subcategoryModal.classList.remove('show');
        setTimeout(() => {
            this.subcategoryModal.style.display = 'none';
        }, 300);
        this.subcategoryForm.reset();
    }

    saveSubcategory() {
        const nameInput = document.getElementById('subcategory-name');
        const weightInput = document.getElementById('subcategory-weight');
        const maxScoreInput = document.getElementById('subcategory-max-score');
        const descriptionInput = document.getElementById('subcategory-description');

        const name = nameInput.value.trim();
        const weight = weightInput.value.trim() ? parseFloat(weightInput.value) : null;
        const maxScore = parseFloat(maxScoreInput.value);
        const description = descriptionInput.value.trim();

        if (!name) {
            Swal.fire('Error', 'Subcategory name is required', 'error');
            return;
        }

        if (!maxScore || maxScore < 0) {
            Swal.fire('Error', 'Valid max score is required', 'error');
            return;
        }

        const category = this.structure.categories.find(cat => cat.id === this.currentCategoryId);
        if (!category) return;

        if (this.editingSubcategory) {
            // Edit existing subcategory
            this.editingSubcategory.name = name;
            this.editingSubcategory.weight = weight;
            this.editingSubcategory.max_score = maxScore;
            this.editingSubcategory.description = description;
        } else {
            // Add new subcategory
            const newSubcategory = {
                id: Date.now().toString(),
                name: name,
                weight: weight,
                max_score: maxScore,
                description: description,
                assessments: []
            };
            category.subcategories.push(newSubcategory);
        }

        this.closeSubcategoryModal();
        this.renderStructure();
        this.updateWeightSummary();
        this.validateWeights();

        Swal.fire('Success', `Subcategory ${this.editingSubcategory ? 'updated' : 'added'} successfully`, 'success');
    }

    deleteSubcategory(subcategoryId) {
        Swal.fire({
            title: 'Delete Subcategory?',
            text: 'This will also delete all assessments. This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6b7280',
            confirmButtonText: 'Delete'
        }).then((result) => {
            if (result.isConfirmed) {
                // Find and remove subcategory
                for (let category of this.structure.categories) {
                    category.subcategories = category.subcategories.filter(sub => sub.id !== subcategoryId);
                }
                this.renderStructure();
                this.updateWeightSummary();
                this.validateWeights();
                Swal.fire('Deleted', 'Subcategory has been deleted', 'success');
            }
        });
    }

    // Assessment Management
    addAssessment(subcategoryId) {
        this.editingAssessment = null;
        this.currentSubcategoryId = subcategoryId;
        this.showAssessmentModal();
    }

    editAssessment(assessmentId) {
        const assessment = this.findAssessment(assessmentId);
        if (!assessment) return;

        this.editingAssessment = assessment;
        this.showAssessmentModal(assessment);
    }

    showAssessmentModal(assessment = null) {
        const title = document.getElementById('assessment-modal-title');
        const nameInput = document.getElementById('assessment-name');
        const maxScoreInput = document.getElementById('assessment-max-score');
        const descriptionInput = document.getElementById('assessment-description');

        if (assessment) {
            title.textContent = 'Edit Assessment';
            nameInput.value = assessment.name;
            maxScoreInput.value = assessment.max_score;
            descriptionInput.value = assessment.description || '';
        } else {
            title.textContent = 'Add Assessment';
            nameInput.value = '';
            maxScoreInput.value = '';
            descriptionInput.value = '';
        }

        this.assessmentModal.style.display = 'block';
        this.assessmentModal.classList.add('show');
        nameInput.focus();
    }

    closeAssessmentModal() {
        this.assessmentModal.classList.remove('show');
        setTimeout(() => {
            this.assessmentModal.style.display = 'none';
        }, 300);
        this.assessmentForm.reset();
    }

    saveAssessment() {
        const nameInput = document.getElementById('assessment-name');
        const maxScoreInput = document.getElementById('assessment-max-score');
        const descriptionInput = document.getElementById('assessment-description');

        const name = nameInput.value.trim();
        const maxScore = parseFloat(maxScoreInput.value);
        const description = descriptionInput.value.trim();

        if (!name) {
            Swal.fire('Error', 'Assessment name is required', 'error');
            return;
        }

        if (!maxScore || maxScore < 0) {
            Swal.fire('Error', 'Valid max score is required', 'error');
            return;
        }

        // Find the subcategory
        let subcategory = null;
        for (let category of this.structure.categories) {
            subcategory = category.subcategories.find(sub => sub.id === this.currentSubcategoryId);
            if (subcategory) break;
        }

        if (!subcategory) return;

        if (this.editingAssessment) {
            // Edit existing assessment
            this.editingAssessment.name = name;
            this.editingAssessment.max_score = maxScore;
            this.editingAssessment.description = description;
        } else {
            // Add new assessment
            const newAssessment = {
                id: Date.now().toString(),
                name: name,
                max_score: maxScore,
                description: description
            };
            subcategory.assessments.push(newAssessment);
        }

        this.closeAssessmentModal();
        this.renderStructure();
        this.updateWeightSummary();

        Swal.fire('Success', `Assessment ${this.editingAssessment ? 'updated' : 'added'} successfully`, 'success');
    }

    deleteAssessment(assessmentId) {
        Swal.fire({
            title: 'Delete Assessment?',
            text: 'This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6b7280',
            confirmButtonText: 'Delete'
        }).then((result) => {
            if (result.isConfirmed) {
                // Find and remove assessment
                for (let category of this.structure.categories) {
                    for (let subcategory of category.subcategories) {
                        subcategory.assessments = subcategory.assessments.filter(ass => ass.id !== assessmentId);
                    }
                }
                this.renderStructure();
                this.updateWeightSummary();
                Swal.fire('Deleted', 'Assessment has been deleted', 'success');
            }
        });
    }

    // Structure Rendering
    renderStructure() {
        if (this.structure.categories.length === 0) {
            this.gradeStructureContainer.innerHTML = `
                <div class="empty-state">
                    <p>No categories added yet.</p>
                    <button class="btn-add" onclick="addCategory()">➕ Add Your First Category</button>
                </div>
            `;
            return;
        }

        let html = '';
        this.structure.categories.forEach((category, categoryIndex) => {
            const subcategoryCount = category.subcategories.length;
            const assessmentCount = category.subcategories.reduce((total, sub) => total + sub.assessments.length, 0);

            const typeIndicatorClass = this.getCategoryTypeClass(category.type);
            const typeIndicatorText = this.getCategoryTypeText(category.type);

            html += `
                <div class="category-item" data-category-id="${category.id}">
                    <div class="category-header" onclick="toggleCategory('${category.id}')">
                        <div class="category-title">
                            📁 ${category.name}
                            <span class="category-type-indicator ${typeIndicatorClass}">${typeIndicatorText}</span>
                            <span style="font-size: 12px; opacity: 0.8;">(${subcategoryCount} subcategories, ${assessmentCount} assessments)</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span class="category-weight">${category.weight}%</span>
                            <div class="category-actions">
                                <button class="btn-icon" onclick="event.stopPropagation(); editCategory('${category.id}')" title="Edit">✏️</button>
                                <button class="btn-icon" onclick="event.stopPropagation(); addSubcategory('${category.id}')" title="Add Subcategory">➕</button>
                                <button class="btn-icon" onclick="event.stopPropagation(); deleteCategory('${category.id}')" title="Delete">🗑️</button>
                            </div>
                        </div>
                    </div>
                    <div class="category-content" id="category-content-${category.id}">
                        ${this.renderSubcategories(category)}
                    </div>
                </div>
            `;
        });

        this.gradeStructureContainer.innerHTML = html;
    }

    renderSubcategories(category) {
        if (category.subcategories.length === 0) {
            return `
                <div class="empty-state" style="padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <p>No subcategories added yet.</p>
                    <button class="btn-secondary" onclick="addSubcategory('${category.id}')" style="font-size: 12px; padding: 6px 12px;">➕ Add Subcategory</button>
                </div>
            `;
        }

        let html = '';
        category.subcategories.forEach((subcategory, subcategoryIndex) => {
            const assessmentCount = subcategory.assessments.length;

            html += `
                <div class="subcategory-item" data-subcategory-id="${subcategory.id}">
                    <div class="subcategory-header" onclick="toggleSubcategory('${category.id}', '${subcategory.id}')">
                        <div class="subcategory-title">
                            📋 ${subcategory.name}
                            <span style="font-size: 11px; opacity: 0.8;">(${assessmentCount} assessments)</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            ${subcategory.weight ? `<span class="subcategory-weight">${subcategory.weight}%</span>` : `<span class="subcategory-weight" style="background: #6b7280;">${subcategory.max_score} pts</span>`}
                            <div class="subcategory-actions">
                                <button class="btn-icon" onclick="event.stopPropagation(); editSubcategory('${subcategory.id}')" title="Edit" style="font-size: 10px; padding: 4px 8px;">✏️</button>
                                <button class="btn-icon" onclick="event.stopPropagation(); addAssessment('${subcategory.id}')" title="Add Assessment" style="font-size: 10px; padding: 4px 8px;">➕</button>
                                <button class="btn-icon" onclick="event.stopPropagation(); deleteSubcategory('${subcategory.id}')" title="Delete" style="font-size: 10px; padding: 4px 8px;">🗑️</button>
                            </div>
                        </div>
                    </div>
                    <div class="subcategory-content" id="subcategory-content-${category.id}-${subcategory.id}">
                        ${this.renderAssessments(subcategory)}
                    </div>
                </div>
            `;
        });

        return html;
    }

    renderAssessments(subcategory) {
        if (subcategory.assessments.length === 0) {
            return `
                <div class="empty-state" style="padding: 15px; background: #f8f9fa; border-radius: 6px;">
                    <p>No assessments added yet.</p>
                    <button class="btn-secondary" onclick="addAssessment('${subcategory.id}')" style="font-size: 11px; padding: 5px 10px;">➕ Add Assessment</button>
                </div>
            `;
        }

        let html = '';
        subcategory.assessments.forEach((assessment, assessmentIndex) => {
            html += `
                <div class="assessment-item" data-assessment-id="${assessment.id}">
                    <div class="assessment-info">
                        <div class="assessment-name">📝 ${assessment.name}</div>
                        <div class="assessment-score">Max Score: ${assessment.max_score} pts</div>
                        ${assessment.description ? `<div style="font-size: 11px; color: #6b7280; margin-top: 2px;">${assessment.description}</div>` : ''}
                    </div>
                    <div class="assessment-actions">
                        <button class="btn-icon" onclick="editAssessment('${assessment.id}')" title="Edit" style="font-size: 10px; padding: 4px 8px;">✏️</button>
                        <button class="btn-icon" onclick="deleteAssessment('${assessment.id}')" title="Delete" style="font-size: 10px; padding: 4px 8px;">🗑️</button>
                    </div>
                </div>
            `;
        });

        return html;
    }

    // UI Toggle Functions
    toggleCategory(categoryId) {
        const content = document.getElementById(`category-content-${categoryId}`);
        if (content) {
            content.classList.toggle('expanded');
        }
    }

    toggleSubcategory(categoryId, subcategoryId) {
        const content = document.getElementById(`subcategory-content-${categoryId}-${subcategoryId}`);
        if (content) {
            content.classList.toggle('expanded');
        }
    }

    // Helper Functions
    findCategory(categoryId) {
        return this.structure.categories.find(cat => cat.id === categoryId);
    }

    findSubcategory(subcategoryId) {
        for (let category of this.structure.categories) {
            const subcategory = category.subcategories.find(sub => sub.id === subcategoryId);
            if (subcategory) return subcategory;
        }
        return null;
    }

    findAssessment(assessmentId) {
        for (let category of this.structure.categories) {
            for (let subcategory of category.subcategories) {
                const assessment = subcategory.assessments.find(ass => ass.id === assessmentId);
                if (assessment) return assessment;
            }
        }
        return null;
    }

    // Weight Management
    updateWeightSummary() {
        const totalWeight = this.structure.categories.reduce((total, cat) => total + (cat.weight || 0), 0);
        const categoryCount = this.structure.categories.length;
        const assessmentCount = this.structure.categories.reduce((total, cat) => {
            return total + cat.subcategories.reduce((subTotal, sub) => subTotal + sub.assessments.length, 0);
        }, 0);

        // Display raw total weight
        const rawTotalWeight = totalWeight;

        // Apply normalization for display if needed
        const displayWeight = this.getNormalizedDisplayWeight(rawTotalWeight);

        document.getElementById('total-weight').textContent = `${displayWeight}%`;
        document.getElementById('category-count').textContent = categoryCount;
        document.getElementById('assessment-count').textContent = assessmentCount;

        // Update weight indicators
        const totalWeightElement = document.getElementById('total-weight');
        totalWeightElement.className = 'weight-value';

        if (Math.abs(rawTotalWeight - 100) < 0.1) {
            totalWeightElement.classList.add('weight-valid');
        } else if (rawTotalWeight > 100) {
            totalWeightElement.classList.add('weight-invalid');
        }

        // Show normalization info if needed
        this.updateNormalizationInfo(rawTotalWeight, displayWeight);
    }

    // Get normalized display weight
    getNormalizedDisplayWeight(rawWeight) {
        if (Math.abs(rawWeight - 100) < 0.1) {
            return 100.0;
        }
        return rawWeight;
    }

    // Update normalization information display
    updateNormalizationInfo(rawWeight, displayWeight) {
        // Remove existing normalization info
        const existingInfo = document.querySelector('.normalization-info');
        if (existingInfo) {
            existingInfo.remove();
        }

        // Add normalization info if weights don't sum to 100%
        if (Math.abs(rawWeight - 100) >= 0.1) {
            const weightSummary = document.getElementById('weight-summary');
            const infoDiv = document.createElement('div');
            infoDiv.className = 'normalization-info';
            infoDiv.innerHTML = `
                <small style="color: #6b7280; font-size: 11px;">
                    ${rawWeight > 100 ? '⚠️ Total exceeds 100%. Grades will be normalized.' : '⚠️ Total under 100%. System will normalize to 100%.'}
                </small>
            `;
            weightSummary.appendChild(infoDiv);
        }
    }

    validateWeights() {
        const totalWeight = this.structure.categories.reduce((total, cat) => total + (cat.weight || 0), 0);

        if (Math.abs(totalWeight - 100) < 0.1) {
            this.showWeightNotification('✅ Perfect! Total weight is exactly 100%', 'success');
        } else if (totalWeight > 100) {
            this.showWeightNotification(`⚠️ Warning: Total weight is ${totalWeight.toFixed(1)}% (over 100%)`, 'warning');
        } else {
            this.showWeightNotification(`⚠️ Warning: Total weight is ${totalWeight.toFixed(1)}% (under 100%)`, 'warning');
        }

        return Math.abs(totalWeight - 100) < 0.1;
    }

    showWeightNotification(message, type) {
        // Remove existing notifications
        const existing = document.querySelector('.weight-notification');
        if (existing) {
            existing.remove();
        }

        const notification = document.createElement('div');
        notification.className = `weight-notification ${type}`;
        notification.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 5px;">Weight Validation</div>
            <div>${message}</div>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    // Import/Export Functions
    exportStructure() {
        const jsonString = JSON.stringify(this.structure, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.structure.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_structure.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        Swal.fire('Exported', 'Structure has been exported successfully', 'success');
    }

    importStructure() {
        this.importModal.style.display = 'block';
        this.importModal.classList.add('show');
    }

    closeImportModal() {
        this.importModal.classList.remove('show');
        setTimeout(() => {
            this.importModal.style.display = 'none';
        }, 300);
        document.getElementById('import-json').value = '';
    }

    processImport() {
        const jsonInput = document.getElementById('import-json');
        const jsonText = jsonInput.value.trim();

        if (!jsonText) {
            Swal.fire('Error', 'Please paste JSON structure', 'error');
            return;
        }

        try {
            const importedStructure = JSON.parse(jsonText);

            if (!importedStructure.name || !Array.isArray(importedStructure.categories)) {
                Swal.fire('Error', 'Invalid structure format', 'error');
                return;
            }

            this.structure = importedStructure;
            this.closeImportModal();
            this.renderStructure();
            this.updateWeightSummary();
            this.validateWeights();

            Swal.fire('Imported', 'Structure has been imported successfully', 'success');
        } catch (error) {
            Swal.fire('Error', 'Invalid JSON format', 'error');
        }
    }

    // Save/Load Functions
    async saveStructure() {
        if (!this.validateWeights()) {
            Swal.fire({
                title: 'Invalid Weights',
                text: 'Please ensure all category weights sum to 100% before saving.',
                icon: 'warning',
                confirmButtonText: 'OK'
            });
            return;
        }

        try {
            const response = await fetch('/api/grade-structure/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    class_id: this.currentClassId,
                    structure_name: this.structure.name,
                    structure_json: JSON.stringify(this.structure)
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.currentStructureId = result.structure_id;

                Swal.fire('Saved', 'Grade structure has been saved successfully', 'success');
            } else {
                throw new Error('Failed to save structure');
            }
        } catch (error) {
            console.error('Error saving structure:', error);
            Swal.fire('Error', 'Failed to save structure. Please try again.', 'error');
        }
    }

    async loadStructure() {
        try {
            const response = await fetch(`/api/grade-structure/get/${this.currentClassId}`);

            if (response.ok) {
                const result = await response.json();

                if (result.structure) {
                    this.structure = JSON.parse(result.structure.structure_json);
                    this.currentStructureId = result.structure.id;
                    this.structureNameInput.value = this.structure.name;

                    this.renderStructure();
                    this.updateWeightSummary();
                    this.validateWeights();

                    Swal.fire('Loaded', 'Structure has been loaded successfully', 'success');
                } else {
                    Swal.fire('No Structure', 'No saved structure found for this class', 'info');
                }
            } else {
                throw new Error('Failed to load structure');
            }
        } catch (error) {
            console.error('Error loading structure:', error);
            Swal.fire('Error', 'Failed to load structure. Please try again.', 'error');
        }
    }

    // Preview Function
    previewStructure() {
        // This would open a modal showing how the structure will look in the grading table
        Swal.fire({
            title: 'Structure Preview',
            html: this.generatePreviewHTML(),
            width: '800px',
            showConfirmButton: false,
            showCloseButton: true
        });
    }

    generatePreviewHTML() {
        let html = `
            <div style="text-align: center; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #059669;">${this.structure.name}</h3>
                <p style="margin: 0; color: #6b7280;">Preview of grading input table structure</p>
            </div>
            <div style="max-height: 400px; overflow-y: auto;">
        `;

        this.structure.categories.forEach(category => {
            html += `
                <div style="margin-bottom: 15px; border: 1px solid #e1e5e9; border-radius: 6px; overflow: hidden;">
                    <div style="background: #059669; color: white; padding: 10px 15px; font-weight: 600;">
                        ${category.name} (${category.weight}%)
                    </div>
                    <div style="padding: 10px;">
            `;

            category.subcategories.forEach(subcategory => {
                html += `
                    <div style="margin-bottom: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                        <div style="font-weight: 600; margin-bottom: 5px;">${subcategory.name}</div>
                `;

                if (subcategory.assessments.length > 0) {
                    html += '<div style="margin-left: 15px;">';
                    subcategory.assessments.forEach(assessment => {
                        html += `
                            <div style="display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #e1e5e9;">
                                <span>${assessment.name}</span>
                                <span style="color: #6b7280;">/ ${assessment.max_score} pts</span>
                            </div>
                        `;
                    });
                    html += '</div>';
                }

                html += '</div>';
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    // Initialize with class ID from URL or parameter
    setClassId(classId) {
        this.currentClassId = classId;
    }

    // Handle category type selection change
    handleCategoryTypeChange() {
        const categoryType = this.categoryTypeSelect.value;
        const customCategoryGroup = document.getElementById('custom-category-group');

        if (categoryType === 'OTHER') {
            customCategoryGroup.style.display = 'block';
            this.customCategoryNameInput.focus();
        } else {
            customCategoryGroup.style.display = 'none';
            this.customCategoryNameInput.value = '';
        }
    }

    // Show custom category name modal
    showCustomCategoryModal() {
        this.customCategoryModal.style.display = 'block';
        this.customCategoryModal.classList.add('show');
        this.modalCustomNameInput.focus();
    }

    // Close custom category modal
    closeCustomCategoryModal() {
        this.customCategoryModal.classList.remove('show');
        setTimeout(() => {
            this.customCategoryModal.style.display = 'none';
        }, 300);
    }

    // Save custom category name from modal
    saveCustomCategoryName() {
        const customName = this.modalCustomNameInput.value.trim();

        if (!customName) {
            Swal.fire('Error', 'Custom category name is required', 'error');
            return;
        }

        this.customCategoryNameInput.value = customName;
        this.categoryTypeSelect.value = 'OTHER';
        this.closeCustomCategoryModal();

        // Show the custom category input field
        document.getElementById('custom-category-group').style.display = 'block';
    }

    // Add predefined subcategories based on category type
    addPredefinedSubcategories(category) {
        if (category.type === 'LECTURE') {
            // Lecture subcategories
            const lectureSubcategories = [
                { name: 'Attendance', max_score: 100 },
                { name: 'Attitude', max_score: 100 },
                { name: 'Recitation', max_score: 100 },
                { name: 'Homework', max_score: 100 },
                { name: 'Quizzes', max_score: 100 },
                { name: 'Project', max_score: 100 },
                { name: 'Prelim Exam', max_score: 100 },
                { name: 'Midterm Exam', max_score: 100 },
                { name: 'Final Exam', max_score: 100 }
            ];

            category.subcategories = lectureSubcategories.map(sub => ({
                id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
                name: sub.name,
                weight: null, // Will be distributed among assessments
                max_score: sub.max_score,
                description: `${sub.name} assessments`,
                assessments: []
            }));
        } else if (category.type === 'LABORATORY') {
            // Laboratory subcategories
            const labSubcategories = [
                { name: 'Lab Participation', max_score: 100 },
                { name: 'Lab Homework', max_score: 100 },
                { name: 'Lab Exercise', max_score: 100 },
                { name: 'Prelim Lab Exam', max_score: 100 },
                { name: 'Midterm Lab Exam', max_score: 100 },
                { name: 'Final Lab Exam', max_score: 100 }
            ];

            category.subcategories = labSubcategories.map(sub => ({
                id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
                name: sub.name,
                weight: null, // Will be distributed among assessments
                max_score: sub.max_score,
                description: `${sub.name} assessments`,
                assessments: []
            }));
        }
    }

    // Get category type CSS class
    getCategoryTypeClass(type) {
        switch (type) {
            case 'LECTURE': return 'category-type-lecture';
            case 'LABORATORY': return 'category-type-laboratory';
            case 'OTHER': return 'category-type-other';
            default: return '';
        }
    }

    // Get category type display text
    getCategoryTypeText(type) {
        switch (type) {
            case 'LECTURE': return 'Lecture';
            case 'LABORATORY': return 'Lab';
            case 'OTHER': return 'Custom';
            default: return '';
        }
    }
}

// Global instance
let builder;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    builder = new GradeStructureBuilder();

    // Get class ID from URL parameter or wherever it's passed
    const urlParams = new URLSearchParams(window.location.search);
    const classId = urlParams.get('class_id');
    if (classId) {
        builder.setClassId(classId);
    }
});

// Global functions to handle onclick events
function addCategory() {
    builder.addCategory();
}

function editCategory(categoryId) {
    builder.editCategory(categoryId);
}

function deleteCategory(categoryId) {
    builder.deleteCategory(categoryId);
}

function addSubcategory(categoryId) {
    builder.addSubcategory(categoryId);
}

function editSubcategory(subcategoryId) {
    builder.editSubcategory(subcategoryId);
}

function deleteSubcategory(subcategoryId) {
    builder.deleteSubcategory(subcategoryId);
}

function addAssessment(subcategoryId) {
    builder.addAssessment(subcategoryId);
}

function editAssessment(assessmentId) {
    builder.editAssessment(assessmentId);
}

function deleteAssessment(assessmentId) {
    builder.deleteAssessment(assessmentId);
}

function saveCategory() {
    builder.saveCategory();
}

function closeCategoryModal() {
    builder.closeCategoryModal();
}

function saveSubcategory() {
    builder.saveSubcategory();
}

function closeSubcategoryModal() {
    builder.closeSubcategoryModal();
}

function saveAssessment() {
    builder.saveAssessment();
}

function closeAssessmentModal() {
    builder.closeAssessmentModal();
}

function saveStructure() {
    builder.saveStructure();
}

function loadStructure() {
    builder.loadStructure();
}

function previewStructure() {
    builder.previewStructure();
}

function validateWeights() {
    builder.validateWeights();
}

function exportStructure() {
    builder.exportStructure();
}

function importStructure() {
    builder.importStructure();
}

function closeImportModal() {
    builder.closeImportModal();
}

function processImport() {
    builder.processImport();
}

function handleCategoryTypeChange() {
    builder.handleCategoryTypeChange();
}

function showCustomCategoryModal() {
    builder.showCustomCategoryModal();
}

function closeCustomCategoryModal() {
    builder.closeCustomCategoryModal();
}

function saveCustomCategoryName() {
    builder.saveCustomCategoryName();
}