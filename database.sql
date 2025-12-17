-- Food Waste Prediction System Database Schema

CREATE DATABASE IF NOT EXISTS food_waste_db;
USE food_waste_db;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Households table
CREATE TABLE households (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    household_name VARCHAR(150) NOT NULL,
    num_members INT DEFAULT 1,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Food categories
CREATE TABLE food_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    perishability_level ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    avg_shelf_life_days INT DEFAULT 7
);

-- Insert default food categories
INSERT INTO food_categories (category_name, perishability_level, avg_shelf_life_days) VALUES
('Vegetables', 'High', 7),
('Fruits', 'High', 5),
('Dairy', 'High', 7),
('Meat', 'High', 3),
('Fish', 'High', 2),
('Grains', 'Low', 180),
('Bread & Bakery', 'Medium', 5),
('Canned Goods', 'Low', 365),
('Frozen Foods', 'Low', 90),
('Beverages', 'Medium', 30),
('Condiments', 'Low', 180),
('Snacks', 'Medium', 60);

-- Food items table
CREATE TABLE food_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    household_id INT NOT NULL,
    category_id INT NOT NULL,
    item_name VARCHAR(150) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    purchase_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    initial_quantity DECIMAL(10, 2) NOT NULL,
    status ENUM('Active', 'Consumed', 'Wasted', 'Donated') DEFAULT 'Active',
    waste_risk_score DECIMAL(5, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES food_categories(id),
    INDEX idx_household_id (household_id),
    INDEX idx_status (status),
    INDEX idx_expiry_date (expiry_date),
    INDEX idx_waste_risk (waste_risk_score)
);

-- Consumption logs table
CREATE TABLE consumption_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    food_item_id INT NOT NULL,
    consumption_date DATE NOT NULL,
    quantity_consumed DECIMAL(10, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    INDEX idx_food_item_id (food_item_id),
    INDEX idx_consumption_date (consumption_date)
);

-- Waste records table
CREATE TABLE waste_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    food_item_id INT NOT NULL,
    household_id INT NOT NULL,
    waste_date DATE NOT NULL,
    quantity_wasted DECIMAL(10, 2) NOT NULL,
    waste_reason ENUM('Expired', 'Spoiled', 'Over-purchased', 'Forgot', 'Other') NOT NULL,
    estimated_value DECIMAL(10, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE,
    INDEX idx_household_id (household_id),
    INDEX idx_waste_date (waste_date)
);

-- Alerts table
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    food_item_id INT NOT NULL,
    household_id INT NOT NULL,
    alert_type ENUM('High Risk', 'Medium Risk', 'Expiring Soon', 'Expired') NOT NULL,
    alert_message TEXT NOT NULL,
    recommendation TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE,
    INDEX idx_household_id (household_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);

-- Recommendations table
CREATE TABLE recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    food_item_id INT NOT NULL,
    recommendation_type ENUM('Use Soon', 'Preserve', 'Donate', 'Recipe Suggestion') NOT NULL,
    recommendation_text TEXT NOT NULL,
    priority INT DEFAULT 1,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    INDEX idx_food_item_id (food_item_id),
    INDEX idx_priority (priority)
);

-- User preferences table
CREATE TABLE user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    alert_frequency ENUM('Real-time', 'Daily', 'Weekly') DEFAULT 'Daily',
    email_notifications BOOLEAN DEFAULT TRUE,
    waste_threshold DECIMAL(5, 2) DEFAULT 50.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Create views for analytics

-- Waste summary by category
CREATE VIEW waste_by_category AS
SELECT 
    fc.category_name,
    COUNT(wr.id) as waste_count,
    SUM(wr.quantity_wasted) as total_quantity_wasted,
    SUM(wr.estimated_value) as total_value_wasted,
    wr.household_id
FROM waste_records wr
JOIN food_items fi ON wr.food_item_id = fi.id
JOIN food_categories fc ON fi.category_id = fc.id
GROUP BY fc.category_name, wr.household_id;

-- Monthly waste trends
CREATE VIEW monthly_waste_trends AS
SELECT 
    DATE_FORMAT(waste_date, '%Y-%m') as month,
    household_id,
    COUNT(*) as waste_incidents,
    SUM(quantity_wasted) as total_waste,
    SUM(estimated_value) as total_value_lost
FROM waste_records
GROUP BY DATE_FORMAT(waste_date, '%Y-%m'), household_id
ORDER BY month DESC;

-- Food items at risk
CREATE VIEW items_at_risk AS
SELECT 
    fi.id,
    fi.item_name,
    fi.quantity,
    fi.unit,
    fi.expiry_date,
    fi.waste_risk_score,
    fc.category_name,
    DATEDIFF(fi.expiry_date, CURDATE()) as days_until_expiry,
    fi.household_id
FROM food_items fi
JOIN food_categories fc ON fi.category_id = fc.id
WHERE fi.status = 'Active' 
    AND fi.waste_risk_score > 50
ORDER BY fi.waste_risk_score DESC, fi.expiry_date ASC;