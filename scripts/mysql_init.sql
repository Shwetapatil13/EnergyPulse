-- MySQL init script (run once on first start)
CREATE DATABASE IF NOT EXISTS energypulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'energyuser'@'%' IDENTIFIED WITH mysql_native_password BY 'energypass123';
GRANT ALL PRIVILEGES ON energypulse.* TO 'energyuser'@'%';
FLUSH PRIVILEGES;
