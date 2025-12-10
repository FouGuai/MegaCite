-- 初始化数据库脚本: 可直接粘贴到 mysql 客户端执行
-- 本脚本会创建数据库 `megacite`（若不存在），并建立所需表及约束。
CREATE DATABASE IF NOT EXISTS `megacite` DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
USE `megacite`;

-- 为避免重复执行报错，先删除可能已存在的表（按外键依赖顺序）
DROP TABLE IF EXISTS post_references;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS auth_platforms;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    token VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE auth_platforms (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    credential VARCHAR(255) DEFAULT NULL,
    UNIQUE KEY ux_user_platform (user_id, platform),
    CONSTRAINT fk_auth_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cid VARCHAR(32) UNIQUE NOT NULL,
    owner_id BIGINT NOT NULL,
    title TEXT,
    `context` LONGTEXT,
    description TEXT,
    catagory VARCHAR(255),
    date DATE NOT NULL,
    CONSTRAINT fk_post_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE post_references (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_cid VARCHAR(32) NOT NULL,
    ref_cid VARCHAR(32) NOT NULL,
    INDEX idx_post_cid (post_cid),
    INDEX idx_ref_cid (ref_cid),
    CONSTRAINT fk_ref_post FOREIGN KEY (post_cid) REFERENCES posts(cid) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 可选：如果希望引用也关联到 posts 表的 cid 上，
-- 可以在 post_references 上添加另一个外键约束：
-- ALTER TABLE post_references ADD CONSTRAINT fk_ref_to_post FOREIGN KEY (ref_cid) REFERENCES posts(cid) ON DELETE RESTRICT;


-- 改密码
-- ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '114514';
ALTER USER 'root'@'localhost' IDENTIFIED BY '114514';
FLUSH PRIVILEGES;