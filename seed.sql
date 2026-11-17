-- =======================================================
-- Smart To-Do List Assistant - Seed Data
-- Database: smart_todo
-- Includes: 1 User, 5 Categories, 15 Diverse Tasks
-- =======================================================

USE smart_todo;

-- Disable foreign key checks for clean truncation / re-seeding
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE tasks;
TRUNCATE TABLE categories;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------
-- 1. Insert Default User
-- -------------------------------------------------------
INSERT INTO users (id, name, email, created_at) VALUES 
(1, 'Alex Morgan', 'alex.morgan@university.edu', NOW());

-- -------------------------------------------------------
-- 2. Insert 5 Categories with Theme Colors
-- -------------------------------------------------------
INSERT INTO categories (id, user_id, name, color) VALUES 
(1, 1, 'Core CS & Algorithms', '#6366F1'),  -- Indigo
(2, 1, 'Web & Full Stack',    '#06B6D4'),  -- Cyan
(3, 1, 'Mathematics & Stats', '#10B981'),  -- Emerald
(4, 1, 'Database Systems',    '#F59E0B'),  -- Amber
(5, 1, 'Career & Capstone',   '#EC4899');  -- Pink

-- -------------------------------------------------------
-- 3. Insert 15 Diverse Tasks
-- Mix of:
--  - Overdue (yesterday/2 days ago)
--  - Due Today (in a few hours)
--  - Due Tomorrow & Upcoming (2-7 days)
--  - High, Medium, Low Priorities
--  - Pending, In Progress, Completed Statuses
-- -------------------------------------------------------

INSERT INTO tasks 
(id, user_id, category_id, title, description, priority, due_date, estimated_minutes, status, created_at, completed_at) 
VALUES 
-- [1] Overdue - High Priority (Needs immediate attention)
(1, 1, 1, 'Prepare for CS301 Midterm Exam', 'Review dynamic programming, recursion trees, and greedy graph heuristics.', 'High', DATE_SUB(NOW(), INTERVAL 1 DAY), 120, 'Pending', DATE_SUB(NOW(), INTERVAL 4 DAY), NULL),

-- [2] Overdue - Medium Priority
(2, 1, 4, 'Submit SQL Optimization Homework', 'Write EXPLAIN ANALYZE queries on composite B-Tree indexes.', 'Medium', DATE_SUB(NOW(), INTERVAL 12 HOUR), 45, 'In Progress', DATE_SUB(NOW(), INTERVAL 3 DAY), NULL),

-- [3] Due Today - High Priority (Urgent student deadline)
(3, 1, 2, 'Fix Authentication Bug in Flask App', 'Token expiry issue in session cookie causing intermittent 401 errors.', 'High', DATE_ADD(NOW(), INTERVAL 3 HOUR), 60, 'Pending', DATE_SUB(NOW(), INTERVAL 1 DAY), NULL),

-- [4] Due Today - Medium Priority
(4, 1, 3, 'Linear Algebra Problem Set #4', 'Eigenvalues, eigenvectors, and singular value decomposition exercises.', 'Medium', DATE_ADD(NOW(), INTERVAL 7 HOUR), 90, 'Pending', DATE_SUB(NOW(), INTERVAL 2 DAY), NULL),

-- [5] Due Today - Low Priority (Quick win)
(5, 1, 5, 'Update LinkedIn Profile & Project Links', 'Add GitHub repositories for Capstone project and link live demo.', 'Low', DATE_ADD(NOW(), INTERVAL 9 HOUR), 20, 'Pending', DATE_SUB(NOW(), INTERVAL 2 DAY), NULL),

-- [6] Due Tomorrow - High Priority
(6, 1, 1, 'Implement Red-Black Tree Deletion', 'Finish C++ implementation of node rebalancing cases 1 through 4.', 'High', DATE_ADD(NOW(), INTERVAL 1 DAY), 90, 'Pending', DATE_SUB(NOW(), INTERVAL 1 DAY), NULL),

-- [7] Due Tomorrow - Medium Priority
(7, 1, 2, 'Design Responsive CSS Dashboard Grid', 'Use modern CSS Grid and Flexbox with responsive breakpoints for tablet and mobile.', 'Medium', DATE_ADD(DATE_ADD(NOW(), INTERVAL 1 DAY), INTERVAL 4 HOUR), 45, 'In Progress', DATE_SUB(NOW(), INTERVAL 1 DAY), NULL),

-- [8] Due in 2 Days - Medium Priority
(8, 1, 4, 'Normalize Database Schema to 3NF', 'Eliminate transitive dependencies in student enrollment schema draft.', 'Medium', DATE_ADD(NOW(), INTERVAL 2 DAY), 60, 'Pending', NOW(), NULL),

-- [9] Due in 3 Days - High Priority
(9, 1, 5, 'Draft Software Engineering Internship Resume', 'Tailor bullet points to emphasize MySQL, Python Flask, and REST API development.', 'High', DATE_ADD(NOW(), INTERVAL 3 DAY), 75, 'Pending', NOW(), NULL),

-- [10] Due in 4 Days - Low Priority
(10, 1, 3, 'Review Probability Density Functions', 'Read Chapter 6 of textbook and summarize Chebyshev bounds.', 'Low', DATE_ADD(NOW(), INTERVAL 4 DAY), 30, 'Pending', NOW(), NULL),

-- [11] Due in 5 Days - Medium Priority
(11, 1, 2, 'Build RESTful API Endpoints for Tasks', 'Implement CRUD controllers with json responses and error handlers.', 'Medium', DATE_ADD(NOW(), INTERVAL 5 DAY), 60, 'Pending', NOW(), NULL),

-- [12] Due in 7 Days - Low Priority
(12, 1, 5, 'Schedule Capstone Mentorship Meeting', 'Email faculty mentor with sprint progress and agenda items.', 'Low', DATE_ADD(NOW(), INTERVAL 7 DAY), 15, 'Pending', NOW(), NULL),

-- [13] Completed - High Priority (Done yesterday)
(13, 1, 1, 'Solve LeetCode Top 50 Graph Problems', 'Completed BFS, DFS, Dijkstra, and Topological Sort challenges.', 'High', DATE_SUB(NOW(), INTERVAL 1 DAY), 90, 'Completed', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 18 HOUR)),

-- [14] Completed - Medium Priority (Done 2 days ago)
(14, 1, 4, 'Set Up Local MySQL 8.0 Instance', 'Configured database credentials, created database users and tables.', 'Medium', DATE_SUB(NOW(), INTERVAL 2 DAY), 30, 'Completed', DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),

-- [15] Completed - Low Priority (Done 3 days ago)
(15, 1, 3, 'Watch Calculus II Lecture Recording', 'Watched integration by parts and trigonometric substitution recap.', 'Low', DATE_SUB(NOW(), INTERVAL 3 DAY), 45, 'Completed', DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY));

