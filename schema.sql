-- ============================================
-- Gym Management System - PostgreSQL Schema
-- ============================================
-- Run with: psql -U postgres -f schema.sql

DROP DATABASE IF EXISTS gym_db;
CREATE DATABASE gym_db;

-- Connect to the new database (psql meta-command)
\c gym_db

DROP TYPE IF EXISTS gender_type;
CREATE TYPE gender_type AS ENUM ('Male', 'Female', 'Other');

DROP TYPE IF EXISTS payment_mode_type;
CREATE TYPE payment_mode_type AS ENUM ('Cash', 'Card', 'UPI', 'Online');

DROP TYPE IF EXISTS condition_type;
CREATE TYPE condition_type AS ENUM ('New', 'Good', 'Needs Repair', 'Out of Service');

-- ---------------------------------------------
-- Table: trainers
-- ---------------------------------------------
CREATE TABLE trainers (
    trainer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100),
    salary DECIMAL(10,2),
    joining_date DATE
);

-- ---------------------------------------------
-- Table: membership_plans
-- ---------------------------------------------
CREATE TABLE membership_plans (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(50) NOT NULL,
    duration_months INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description VARCHAR(255)
);

-- ---------------------------------------------
-- Table: members
-- ---------------------------------------------
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    gender gender_type,
    phone VARCHAR(15),
    email VARCHAR(100),
    address VARCHAR(255),
    join_date DATE,
    plan_id INT REFERENCES membership_plans(plan_id) ON DELETE SET NULL,
    trainer_id INT REFERENCES trainers(trainer_id) ON DELETE SET NULL
);

-- ---------------------------------------------
-- Table: payments
-- ---------------------------------------------
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_mode payment_mode_type DEFAULT 'Cash'
);

-- ---------------------------------------------
-- Table: equipment
-- ---------------------------------------------
CREATE TABLE equipment (
    equipment_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    quantity INT DEFAULT 1,
    purchase_date DATE,
    condition_status condition_type DEFAULT 'Good'
);

-- ---------------------------------------------
-- Table: attendance
-- ---------------------------------------------
CREATE TABLE attendance (
    attendance_id SERIAL PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(member_id) ON DELETE CASCADE,
    check_in_date DATE NOT NULL,
    check_in_time TIME,
    check_out_time TIME
);

-- ---------------------------------------------
-- Table: deleted_history
-- Archives a full snapshot of any record right before it's deleted,
-- so old member/plan/trainer/equipment IDs still make sense later
-- even though SERIAL keeps incrementing.
-- ---------------------------------------------
CREATE TABLE deleted_history (
    history_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL,   -- 'member', 'trainer', 'plan', 'equipment'
    original_id INT NOT NULL,
    data JSONB NOT NULL,                -- full row snapshot at time of deletion
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Sample Data
-- ============================================

INSERT INTO membership_plans (plan_name, duration_months, price, description) VALUES
('Monthly Basic', 1, 1500.00, 'Access to gym floor and equipment'),
('Quarterly Standard', 3, 4000.00, 'Gym access + group classes'),
('Half-Yearly Premium', 6, 7500.00, 'Gym access + trainer sessions + classes'),
('Annual Gold', 12, 14000.00, 'Full access + personal trainer + diet plan');

INSERT INTO trainers (name, specialization, phone, email, salary, joining_date) VALUES
('Ramesh Thapa', 'Strength Training', '9800000001', 'ramesh@gym.com', 35000.00, '2023-01-15'),
('Sita Gurung', 'Yoga & Flexibility', '9800000002', 'sita@gym.com', 30000.00, '2023-03-10'),
('Bikash Rai', 'Cardio & Weight Loss', '9800000003', 'bikash@gym.com', 32000.00, '2022-11-20');

INSERT INTO members (name, age, gender, phone, email, address, join_date, plan_id, trainer_id) VALUES
('Arjun Shrestha', 24, 'Male', '9811111111', 'arjun@mail.com', 'Kathmandu', '2024-01-05', 4, 1),
('Priya Adhikari', 28, 'Female', '9811111112', 'priya@mail.com', 'Lalitpur', '2024-02-10', 2, 2),
('Suman Karki', 22, 'Male', '9811111113', 'suman@mail.com', 'Bhaktapur', '2024-03-01', 1, 3),
('Anita Magar', 30, 'Female', '9811111114', 'anita@mail.com', 'Kathmandu', '2024-01-20', 3, 2),
('Deepak Bhattarai', 26, 'Male', '9811111115', 'deepak@mail.com', 'Kathmandu', '2024-04-15', 1, 1);

INSERT INTO payments (member_id, amount, payment_date, payment_mode) VALUES
(1, 14000.00, '2024-01-05', 'Online'),
(2, 4000.00, '2024-02-10', 'Card'),
(3, 1500.00, '2024-03-01', 'Cash'),
(4, 7500.00, '2024-01-20', 'UPI'),
(5, 1500.00, '2024-04-15', 'Cash');

INSERT INTO equipment (name, category, quantity, purchase_date, condition_status) VALUES
('Treadmill', 'Cardio', 5, '2022-06-01', 'Good'),
('Dumbbells Set', 'Strength', 10, '2022-06-01', 'Good'),
('Bench Press', 'Strength', 3, '2023-01-15', 'Good'),
('Yoga Mats', 'Flexibility', 20, '2023-05-10', 'New'),
('Stationary Bike', 'Cardio', 4, '2021-09-20', 'Needs Repair');

INSERT INTO attendance (member_id, check_in_date, check_in_time, check_out_time) VALUES
(1, '2024-06-01', '06:00:00', '07:30:00'),
(2, '2024-06-01', '17:00:00', '18:00:00'),
(3, '2024-06-02', '06:30:00', '07:15:00'),
(1, '2024-06-02', '06:05:00', '07:20:00');
