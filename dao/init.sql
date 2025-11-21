CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
    token VARCHAR(255)
);

CREATE TABLE auth_platforms (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    credential VARCHAR(255),
    UNIQUE(user_id, platform),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cid VARCHAR(32) UNIQUE NOT NULL,
    owner_id BIGINT NOT NULL,
    title TEXT,
    context LONGTEXT,
    description TEXT,
    catagory VARCHAR(255),
    date DATE NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE post_references (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_cid VARCHAR(32) NOT NULL,
    ref_cid VARCHAR(32) NOT NULL,
    FOREIGN KEY (post_cid) REFERENCES posts(cid) ON DELETE CASCADE
);
