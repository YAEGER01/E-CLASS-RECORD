# Assessment Abbreviations and DROPPED Status Feature

## Overview
This feature enhances the grade remarks system to use abbreviations for missing assessments and adds support for marking students as DROPPED.

## Changes Made

### 1. Assessment Abbreviations

#### Frontend (instructor_grades_unified.js)
- Added `abbreviateAssessment()` function to convert assessment names to abbreviations:
  - PRELIM EXAM → NPE (No Prelim Exam)
  - MIDTERM EXAM → NME (No Midterm Exam)
  - FINAL EXAM → NFE (No Final Exam)
  - PROJECT → NO PROJECT
  - Other assessments → NO [ASSESSMENT NAME]

- Updated `updateFinalGradeForRow()` to:
  - Check ALL subcategories for missing scores
  - Build comma-separated list of abbreviations (e.g., "NPE, NME")
  - Display abbreviated remarks in the REMARKS column

#### Backend (instructor_routes.py)
- Added `abbreviate_assessment()` helper function with same logic as frontend
- Updated `api_get_release_grades()` to:
  - Collect ALL missing subcategories (not just first one)
  - Generate comma-separated abbreviations for remarks
  - Example: Student missing Prelim and Midterm → "NPE, NME"

- Updated `_release_grades_to_students_internal()` to:
  - Use same abbreviation logic when releasing grades
  - Ensure consistency between grade input and released grades

### 2. DROPPED Status

#### Frontend (instructor_grades_unified.html)
- Added DRP column to final grade table header
- Added checkbox for each student row:
  ```html
  <input type="checkbox" class="dropped-checkbox" 
         data-student="{{ s.id }}" 
         title="Mark as Dropped">
  ```

#### Frontend (instructor_grades_unified.js)
- Updated `updateFinalGradeForRow()` to:
  - Check if DROPPED checkbox is checked
  - If checked, set grade mark to 'DRP' and remarks to 'DROPPED'
  - Override any other grade calculations

- Added event listener in `setupEventListeners()`:
  - Listens for checkbox change events
  - Triggers grade recalculation when toggled
  - Updates status message

## Usage

### For Instructors

#### Setting Abbreviated Remarks
1. When entering grades, leave any assessment blank
2. The system will automatically detect which assessments are missing
3. The REMARKS column will show abbreviations:
   - Single missing: "NPE" or "NME" or "NFE"
   - Multiple missing: "NPE, NME" or "NME, NFE"
   - Grade Mark will show "INC" (Incomplete)

#### Marking Students as DROPPED
1. In the Final Grade table, find the DRP column
2. Check the checkbox for the student who dropped
3. The grade mark will automatically change to "DRP"
4. The remarks will change to "DROPPED"
5. When you release grades, the DROPPED status will be included

### Examples

#### Example 1: Missing Prelim Exam Only
- Student has no Prelim Exam score
- Grade Mark: INC
- Remarks: NPE

#### Example 2: Missing Multiple Assessments
- Student has no Prelim Exam and no Midterm Exam
- Grade Mark: INC
- Remarks: NPE, NME

#### Example 3: Dropped Student
- Instructor checks the DROPPED checkbox
- Grade Mark: DRP
- Remarks: DROPPED
- (Takes precedence over missing assessments)

## Technical Details

### Assessment Detection Logic
The system checks if ANY score in a subcategory is missing (null or blank):
```javascript
for (const [groupKey, groupData] of Object.entries(groups)) {
    const subcatName = groupKey.split('::').pop();
    const hasMissing = groupData.ids.some(aid => {
        const score = scores[aid];
        return score === null || score === undefined || score === '';
    });
    if (hasMissing) {
        missingSubcategories.push(subcatName);
    }
}
```

### Abbreviation Mapping
```python
def abbreviate_assessment(name):
    name_upper = name.upper()
    if "PRELIM" in name_upper and "EXAM" in name_upper:
        return "NPE"
    elif "MIDTERM" in name_upper and "EXAM" in name_upper:
        return "NME"
    elif "FINAL" in name_upper and "EXAM" in name_upper:
        return "NFE"
    elif "PROJECT" in name_upper:
        return "NO PROJECT"
    else:
        return f"NO {name_upper}"
```

## Files Modified

1. **static/js/instructor_grades_unified.js**
   - Added abbreviateAssessment() function
   - Updated updateFinalGradeForRow() for abbreviations and DROPPED
   - Added DROPPED checkbox event listener

2. **templates/instructor_grades_unified.html**
   - Added DRP column header
   - Added DROPPED checkbox for each student

3. **blueprints/instructor_routes.py**
   - Added abbreviate_assessment() helper function
   - Updated api_get_release_grades() for multiple missing assessments
   - Updated _release_grades_to_students_internal() for abbreviations

## Testing Checklist

- [ ] Create a class with assessments
- [ ] Enter scores for some students, leave some assessments blank
- [ ] Verify abbreviations appear correctly (NPE, NME, NFE, NO PROJECT)
- [ ] Test multiple missing assessments show comma-separated list
- [ ] Check DROPPED checkbox for a student
- [ ] Verify grade mark changes to DRP and remarks to DROPPED
- [ ] Uncheck DROPPED and verify grade recalculates normally
- [ ] Release grades and check grade sheet report shows correct remarks
- [ ] Test all three class types (MAJOR, MAJOR_LAB, MINOR)
- [ ] Verify INC grade mark appears for incomplete students

## Future Enhancements

1. **Persist DROPPED Status**: Consider adding a `is_dropped` column to student enrollment table
2. **Bulk DROPPED**: Add button to mark multiple students as DROPPED at once
3. **Custom Abbreviations**: Allow instructors to configure abbreviation patterns
4. **DROPPED History**: Track when student was marked as DROPPED and by whom
