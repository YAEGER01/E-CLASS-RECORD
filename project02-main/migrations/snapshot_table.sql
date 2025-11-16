CREATE TABLE grade_snapshots (
  id INT AUTO_INCREMENT PRIMARY KEY,
  class_id INT NOT NULL,
  version INT NOT NULL,
  status ENUM('draft','final') NOT NULL DEFAULT 'draft',
  snapshot_json JSON NOT NULL,
  created_by INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  released_at DATETIME NULL,
  INDEX idx_class_version (class_id, version),
  INDEX idx_class_status (class_id, status),
  CONSTRAINT fk_snapshots_class FOREIGN KEY (class_id) REFERENCES classes(id)
);
