-- StackIt Database Schema
-- PostgreSQL 12+ compatible
-- Generated from SQLAlchemy models

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- User roles enum
CREATE TYPE userrole AS ENUM ('guest', 'user', 'admin');

-- Notification types enum
CREATE TYPE notificationtype AS ENUM (
    'answer_to_question',
    'comment_on_answer', 
    'mention',
    'answer_accepted',
    'vote_received'
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    role userrole NOT NULL DEFAULT 'user',
    reputation_score INTEGER NOT NULL DEFAULT 0,
    questions_count INTEGER NOT NULL DEFAULT 0,
    answers_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7),
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Questions table
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    view_count INTEGER NOT NULL DEFAULT 0,
    vote_score INTEGER NOT NULL DEFAULT 0,
    answer_count INTEGER NOT NULL DEFAULT 0,
    is_closed BOOLEAN NOT NULL DEFAULT false,
    has_accepted_answer BOOLEAN NOT NULL DEFAULT false,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    accepted_answer_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Answers table
CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    vote_score INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,
    is_accepted BOOLEAN NOT NULL DEFAULT false,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add foreign key constraint for accepted_answer_id
ALTER TABLE questions 
ADD CONSTRAINT fk_questions_accepted_answer 
FOREIGN KEY (accepted_answer_id) REFERENCES answers(id) ON DELETE SET NULL;

-- Question tags junction table
CREATE TABLE question_tags (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(question_id, tag_id)
);

-- Votes table
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    is_upvote BOOLEAN NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    answer_id INTEGER NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, answer_id)
);

-- Comments table
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    answer_id INTEGER NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type notificationtype NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    triggered_by_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    related_question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    related_answer_id INTEGER REFERENCES answers(id) ON DELETE CASCADE,
    related_comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance optimization

-- Users table indexes
CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_active_role ON users(is_active, role);
CREATE INDEX ix_users_username_email ON users(username, email);
CREATE INDEX ix_users_reputation_desc ON users(reputation_score DESC);
CREATE INDEX ix_users_username_trigram ON users USING gin(username gin_trgm_ops);
CREATE INDEX ix_users_active_only ON users(username, email) WHERE is_active = true;

-- Questions table indexes
CREATE INDEX ix_questions_title ON questions(title);
CREATE INDEX ix_questions_author_id ON questions(author_id);
CREATE INDEX ix_questions_created_status ON questions(created_at, is_closed);
CREATE INDEX ix_questions_vote_score_desc ON questions(vote_score DESC);
CREATE INDEX ix_questions_accepted_answers ON questions(has_accepted_answer, created_at);
CREATE INDEX ix_questions_author_created ON questions(author_id, created_at);
CREATE INDEX ix_questions_title_trigram ON questions USING gin(title gin_trgm_ops);
CREATE INDEX ix_questions_fulltext_search ON questions USING gin(to_tsvector('english', title || ' ' || description));

-- Answers table indexes
CREATE INDEX ix_answers_question_id ON answers(question_id);
CREATE INDEX ix_answers_author_id ON answers(author_id);
CREATE INDEX ix_answers_question_created ON answers(question_id, created_at);
CREATE INDEX ix_answers_accepted ON answers(is_accepted, question_id);
CREATE INDEX ix_answers_vote_score_desc ON answers(vote_score DESC);
CREATE INDEX ix_answers_author_created ON answers(author_id, created_at);

-- Tags table indexes
CREATE INDEX ix_tags_name ON tags(name);

-- Question tags table indexes
CREATE INDEX ix_question_tags_question_id ON question_tags(question_id);
CREATE INDEX ix_question_tags_tag_id ON question_tags(tag_id);

-- Votes table indexes
CREATE INDEX ix_votes_user_id ON votes(user_id);
CREATE INDEX ix_votes_answer_id ON votes(answer_id);

-- Comments table indexes
CREATE INDEX ix_comments_answer_id ON comments(answer_id);
CREATE INDEX ix_comments_author_id ON comments(author_id);
CREATE INDEX ix_comments_answer_created ON comments(answer_id, created_at);

-- Notifications table indexes
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_notifications_user_unread ON notifications(user_id, is_read, created_at);
CREATE INDEX ix_notifications_type_created ON notifications(notification_type, created_at);
CREATE INDEX ix_notifications_user_created_desc ON notifications(user_id, created_at DESC);
CREATE INDEX ix_notifications_unread_only ON notifications(user_id, created_at DESC) WHERE is_read = false;

-- Database functions for common operations

-- Function to update question statistics
CREATE OR REPLACE FUNCTION update_question_stats(question_id_param INTEGER)
RETURNS void AS $$
BEGIN
    UPDATE questions 
    SET 
        answer_count = (
            SELECT COUNT(*) FROM answers WHERE question_id = question_id_param
        ),
        vote_score = COALESCE((
            SELECT SUM(CASE WHEN v.is_upvote THEN 1 ELSE -1 END)
            FROM votes v
            JOIN answers a ON v.answer_id = a.id
            WHERE a.question_id = question_id_param
        ), 0)
    WHERE id = question_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to update user reputation
CREATE OR REPLACE FUNCTION update_user_reputation(user_id_param INTEGER)
RETURNS void AS $$
BEGIN
    UPDATE users 
    SET reputation_score = COALESCE((
        SELECT SUM(CASE WHEN v.is_upvote THEN 10 ELSE -2 END)
        FROM votes v
        JOIN answers a ON v.answer_id = a.id
        WHERE a.author_id = user_id_param
    ), 0) + COALESCE((
        SELECT COUNT(*) * 15
        FROM answers a
        WHERE a.author_id = user_id_param AND a.is_accepted = true
    ), 0)
    WHERE id = user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function for full-text search
CREATE OR REPLACE FUNCTION search_questions(search_term TEXT)
RETURNS TABLE(
    id INTEGER,
    title VARCHAR(200),
    description TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        q.id,
        q.title,
        q.description,
        ts_rank(to_tsvector('english', q.title || ' ' || q.description), 
               plainto_tsquery('english', search_term)) as rank
    FROM questions q
    WHERE to_tsvector('english', q.title || ' ' || q.description) 
          @@ plainto_tsquery('english', search_term)
    ORDER BY rank DESC, q.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updates

-- Trigger function to update question stats
CREATE OR REPLACE FUNCTION trigger_update_question_stats()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM update_question_stats(NEW.question_id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM update_question_stats(OLD.question_id);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM update_question_stats(NEW.question_id);
        IF NEW.question_id != OLD.question_id THEN
            PERFORM update_question_stats(OLD.question_id);
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for answer statistics
CREATE TRIGGER trigger_answer_stats
    AFTER INSERT OR UPDATE OR DELETE ON answers
    FOR EACH ROW EXECUTE FUNCTION trigger_update_question_stats();

-- Trigger function to update user reputation
CREATE OR REPLACE FUNCTION trigger_update_user_reputation()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM update_user_reputation((SELECT author_id FROM answers WHERE id = NEW.answer_id));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM update_user_reputation((SELECT author_id FROM answers WHERE id = OLD.answer_id));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM update_user_reputation((SELECT author_id FROM answers WHERE id = NEW.answer_id));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for vote reputation updates
CREATE TRIGGER trigger_vote_reputation
    AFTER INSERT OR UPDATE OR DELETE ON votes
    FOR EACH ROW EXECUTE FUNCTION trigger_update_user_reputation();

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update timestamp triggers to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_answers_updated_at BEFORE UPDATE ON answers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tags_updated_at BEFORE UPDATE ON tags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_question_tags_updated_at BEFORE UPDATE ON question_tags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_votes_updated_at BEFORE UPDATE ON votes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
