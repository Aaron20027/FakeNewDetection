-- Step 1: Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS PhNewsCheckerDB;


-- Step 2: Use the database
USE PhNewsCheckerDB;


-- Step 3: Create the tables
-- users_tbl
CREATE TABLE IF NOT EXISTS users_tbl(
	user_id INT PRIMARY KEY AUTO_INCREMENT,	
	username VARCHAR(50) NOT NULL UNIQUE,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	email VARCHAR(100) NOT NULL UNIQUE, 
	enabled BOOLEAN DEFAULT 1,
	password_hash VARCHAR(255) NOT NULL,
	role ENUM('A', 'C') NOT NULL, --dont update
	data_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, --dont update
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- articles_tbl
CREATE TABLE IF NOT EXISTS articles_tbl(
	article_id INT AUTO_INCREMENT PRIMARY KEY,	
	title TEXT NOT NULL,
	article_text LONGTEXT NOT NULL,
	label TINYINT(1) NOT NULL,
	sentiment ENUM('positive', 'neutral', 'negative') NOT NULL, 
	sentiment_intensity ENUM(
    'Strongly Positive', 'Weakly Positive', 
    'Neutral', 
    'Strongly Negative', 'Weakly Negative'
  	) NOT NULL,
  	sources TEXT,
	submitted_by INT NOT NULL, 
  	submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	factchecked_by INT,
	factchecked_at DATETIME,
	status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	



	FOREIGN KEY (submitted_by) REFERENCES users_tbl(user_id),
  FOREIGN KEY (factchecked_by) REFERENCES users_tbl(user_id)
);

-- audit_logs_tbl
CREATE TABLE IF NOT EXISTS audit_logs_tbl(
	audit_log_id INT AUTO_INCREMENT PRIMARY KEY,
	performed_by INT NOT NULL, -- FK TO USER
	action VARCHAR(100) NOT NULL,
	user_agent VARCHAR(255) NOT NULL,
	ip_address VARCHAR(45) NOT NULL,
	timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

	FOREIGN KEY (performed_by) REFERENCES users_tbl(user_id)
);

-- model_versions_tbl
CREATE TABLE IF NOT EXISTS model_versions_tbl(
	model_id INT AUTO_INCREMENT PRIMARY KEY,
	file_path VARCHAR(255) NOT NULL,
	trained_by INT NOT NULL, -- FK TO USER TABLE
	trained_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	model_accuracy DECIMAL(5, 2) NOT NULL,
	model_precision DECIMAL(5, 2) NOT NULL,
	model_recall DECIMAL(5, 2) NOT NULL,
	model_f1_score DECIMAL(5, 2) NOT NULL,
	is_active TINYINT(1) NOT NULL,

	FOREIGN KEY (trained_by) REFERENCES users_tbl(user_id)
);

CREATE TABLE IF NOT EXISTS predicted_articles_tbl(
	predicted_article_id INT AUTO_INCREMENT PRIMARY KEY,	
	article_text LONGTEXT NOT NULL,
	label TINYINT(1) NOT NULL,
	sentiment ENUM('positive', 'neutral', 'negative') NOT NULL, 
	sentiment_intensity ENUM(
    'Strongly Positive', 'Weakly Positive', 
    'Neutral', 
    'Strongly Negative', 'Weakly Negative'
  	) NOT NULL,
  	predicted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);




-- optional
-- comments_tbl
-- sessions_tbl

