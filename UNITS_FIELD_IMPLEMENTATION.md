# Units Field Implementation

## Overview
Added a "units" field to the class creation system that accepts decimal values (e.g., 3, 3.0, 2.5) to track subject units. The units field is now integrated throughout the system and displayed in the grade sheet report.

## Changes Made

### 1. Database Schema (db/add_units_column.sql)
- **Created migration file** to add `units` column to the `classes` table
- Column type: `DECIMAL(4,1)` - allows values like 3.0, 2.5, etc.
- Column is nullable to support existing records
- Positioned after `subject_code` column

**To apply the migration:**
```sql
-- Run this SQL command on your database
SOURCE db/add_units_column.sql;
```

### 2. Frontend Form (templates/instructor_classes.html)
- **Added units input field** to the class creation form (Step 2)
- Field specifications:
  - Type: `number`
  - Step: `0.5` (allows half-unit increments)
  - Min: `0.5`
  - Max: `10`
  - Required field with placeholder "e.g., 3"
- **Updated JavaScript functions:**
  - `handleFormSubmit()` - Now validates and includes units
  - `showPreviewModal()` - Displays units in preview
  - `confirmAddClass()` - Sends units to API (parsed as float)
  - `editClass()` - Populates units field when editing

### 3. Backend API Routes (blueprints/instructor_routes.py)

#### Create Class Route (`/api/instructor/classes` POST)
- Added `units` to required fields validation
- Updated SQL INSERT query to include units column
- Added units to returned class object

#### Update Class Route (`/api/instructor/classes/<id>` PUT)
- Added `units` to required fields validation
- Updated SQL UPDATE query to include units column
- Added units to returned class object

#### Get Classes Route (`/api/instructor/classes` GET)
- Updated class data serialization to include units field
- Units are now returned for all class listings

### 4. Grade Sheet Report (templates/grade_sheet_report.html)
- **Added units display** in the course details section
- Positioned between "Description" and "Period" fields
- Shows "N/A" if units value is not set
- Format: `<span>Units</span> <span>{{ value }}</span>`

### 5. Reports Backend (blueprints/reports_routes.py)
- **Updated SQL query** to fetch units from classes table
- **Added units extraction** from query result (handles both tuple and dict formats)
- **Added units to class_info** dictionary passed to template

## Usage

### Creating a New Class
1. Navigate to the "Add New Class" form
2. Fill in all required fields including the new "Units" field
3. Enter units value (e.g., 3, 3.0, 2.5)
4. The system will validate and store the units value

### Viewing Units
- **Class listings**: Units are now included in the class data returned by the API
- **Grade sheet report**: Units are displayed in the course details section

## Testing Checklist

- [ ] Apply the database migration (add_units_column.sql)
- [ ] Create a new class with units value (e.g., 3.0)
- [ ] Edit an existing class and update units
- [ ] View the grade sheet report and verify units are displayed
- [ ] Test with decimal values (e.g., 2.5, 3.5)
- [ ] Test validation (required field)

## Database Migration

**Important:** Before using this feature, you must run the migration:

```bash
# Option 1: Using MySQL client
mysql -u your_username -p your_database < db/add_units_column.sql

# Option 2: From MySQL console
USE e_class_record;
SOURCE db/add_units_column.sql;

# Option 3: Direct SQL command
ALTER TABLE `classes` ADD COLUMN `units` DECIMAL(4,1) NULL DEFAULT NULL AFTER `subject_code`;
```

## Files Modified

1. `db/add_units_column.sql` - NEW (migration file)
2. `templates/instructor_classes.html` - Updated form and JavaScript
3. `blueprints/instructor_routes.py` - Updated create/update/get routes
4. `templates/grade_sheet_report.html` - Added units display
5. `blueprints/reports_routes.py` - Updated query and data extraction

## Notes

- The units field accepts decimal values with one decimal place precision
- Values like 3 and 3.0 are both valid and will be stored as 3.0
- Existing classes without units will show "N/A" in reports
- The field is required for new classes but nullable in the database for backwards compatibility
