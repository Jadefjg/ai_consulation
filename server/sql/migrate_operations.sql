-- 运营扩展表迁移（可重复执行，适用于已有数据库）
USE db_ai_medical;
CREATE TABLE IF NOT EXISTS t_doctor_schedule (
  id INT AUTO_INCREMENT PRIMARY KEY, doctor_id INT NOT NULL, work_date DATE NOT NULL,
  time_slot VARCHAR(20) NOT NULL, capacity INT NOT NULL DEFAULT 1, status INT NOT NULL DEFAULT 1,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_schedule (doctor_id, work_date, time_slot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS t_notification (
  id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL, type VARCHAR(30) DEFAULT 'system', is_read INT NOT NULL DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP, KEY idx_notification_user (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS t_audit_log (
  id INT AUTO_INCREMENT PRIMARY KEY, actor_id INT NOT NULL, actor_role VARCHAR(20) NOT NULL,
  action VARCHAR(80) NOT NULL, target_type VARCHAR(40) NOT NULL, target_id INT NULL,
  detail TEXT, create_time DATETIME DEFAULT CURRENT_TIMESTAMP, KEY idx_audit_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
