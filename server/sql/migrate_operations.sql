-- 运营扩展表迁移（可重复执行，适用于已有数据库）
USE db_ai_medical;
CREATE TABLE IF NOT EXISTS t_doctor_schedule (
  id INT AUTO_INCREMENT PRIMARY KEY, doctor_id INT NOT NULL, work_date DATE NOT NULL,
  time_slot VARCHAR(20) NOT NULL, capacity INT NOT NULL DEFAULT 1, status INT NOT NULL DEFAULT 1,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_schedule (doctor_id, work_date, time_slot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_doctor_consult_followup (
  id INT AUTO_INCREMENT PRIMARY KEY, consult_id INT NOT NULL, user_id INT NOT NULL,
  content TEXT NOT NULL, create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_followup_consult (consult_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_symptom_assessment (
  id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, session_id INT NULL,
  symptoms_json TEXT NOT NULL, onset_time VARCHAR(100), duration VARCHAR(100), severity INT DEFAULT 1,
  temperature VARCHAR(20), extra_json TEXT, create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_symptom_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_ai_consult_review (
  id INT AUTO_INCREMENT PRIMARY KEY, session_id INT NOT NULL, consult_id INT NOT NULL, user_id INT NOT NULL,
  doctor_id INT NULL, ai_summary TEXT NOT NULL, review_status INT NOT NULL DEFAULT 0,
  doctor_comment TEXT, record_id INT NULL, create_time DATETIME DEFAULT CURRENT_TIMESTAMP, review_time DATETIME NULL,
  KEY idx_ai_review_doctor (doctor_id, review_status), KEY idx_ai_review_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_followup_plan (id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,doctor_id INT NOT NULL,title VARCHAR(200) NOT NULL,frequency_days INT NOT NULL DEFAULT 30,next_date DATE NOT NULL,status INT NOT NULL DEFAULT 1,notes TEXT,create_time DATETIME DEFAULT CURRENT_TIMESTAMP,KEY idx_followup_plan_user(user_id));
CREATE TABLE IF NOT EXISTS t_followup_task (id INT AUTO_INCREMENT PRIMARY KEY,plan_id INT NOT NULL,due_date DATE NOT NULL,response TEXT,status INT NOT NULL DEFAULT 0,completed_time DATETIME,KEY idx_followup_task_plan(plan_id));
CREATE TABLE IF NOT EXISTS t_chronic_record (id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,doctor_id INT,disease VARCHAR(100) NOT NULL,target_json TEXT,status INT NOT NULL DEFAULT 1,create_time DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS t_chronic_metric (id INT AUTO_INCREMENT PRIMARY KEY,chronic_id INT NOT NULL,metric VARCHAR(50) NOT NULL,value VARCHAR(100) NOT NULL,measured_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS t_risk_assessment (id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,source VARCHAR(30) DEFAULT 'rule',score INT NOT NULL,level VARCHAR(20) NOT NULL,factors_json TEXT,create_time DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS t_knowledge_version (id INT AUTO_INCREMENT PRIMARY KEY,file_id INT NOT NULL,version INT NOT NULL,content_hash VARCHAR(64) NOT NULL,status INT NOT NULL DEFAULT 0,reviewer_id INT,review_comment TEXT,create_time DATETIME DEFAULT CURRENT_TIMESTAMP,review_time DATETIME,KEY idx_kv_file(file_id));
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
