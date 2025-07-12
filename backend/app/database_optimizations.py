"""
Database performance optimizations and PostgreSQL-specific configurations.
"""
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_postgresql_extensions(db: Session):
    """Create PostgreSQL extensions for enhanced functionality."""
    extensions = [
        "CREATE EXTENSION IF NOT EXISTS pg_trgm;",  # For trigram similarity search
        "CREATE EXTENSION IF NOT EXISTS btree_gin;",  # For GIN indexes on btree types
        "CREATE EXTENSION IF NOT EXISTS unaccent;",  # For accent-insensitive search
    ]

    for extension_sql in extensions:
        try:
            db.execute(text(extension_sql))
            logger.info(f"Created extension: {extension_sql}")
        except Exception as e:
            logger.warning(f"Could not create extension {extension_sql}: {e}")

    db.commit()


def create_custom_indexes(db: Session):
    """Create custom indexes for better performance."""
    custom_indexes = [
        # Full-text search index for question titles and descriptions
        """
        CREATE INDEX IF NOT EXISTS ix_questions_fulltext_search 
        ON questions USING gin(to_tsvector('english', title || ' ' || description));
        """,

        # Trigram index for fuzzy search on question titles
        """
        CREATE INDEX IF NOT EXISTS ix_questions_title_trigram 
        ON questions USING gin(title gin_trgm_ops);
        """,

        # Trigram index for user search
        """
        CREATE INDEX IF NOT EXISTS ix_users_username_trigram 
        ON users USING gin(username gin_trgm_ops);
        """,

        # Partial index for active users only
        """
        CREATE INDEX IF NOT EXISTS ix_users_active_only 
        ON users (username, email) WHERE is_active = true;
        """,

        # Partial index for unread notifications only
        """
        CREATE INDEX IF NOT EXISTS ix_notifications_unread_only 
        ON notifications (user_id, created_at DESC) WHERE is_read = false;
        """,

        # Index for question statistics updates
        """
        CREATE INDEX IF NOT EXISTS ix_questions_stats_update 
        ON questions (id, answer_count, vote_score, view_count);
        """,
    ]

    for index_sql in custom_indexes:
        try:
            db.execute(text(index_sql))
            logger.info("Created custom index successfully")
        except Exception as e:
            logger.warning(f"Could not create custom index: {e}")

    db.commit()


def create_database_functions(db: Session):
    """Create PostgreSQL functions for common operations."""
    functions = [
        # Function to update question statistics
        """
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
        """,

        # Function to update user reputation
        """
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
        """,

        # Function for full-text search
        """
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
        """,
    ]

    for function_sql in functions:
        try:
            db.execute(text(function_sql))
            logger.info("Created database function successfully")
        except Exception as e:
            logger.warning(f"Could not create database function: {e}")

    db.commit()


def create_database_triggers(db: Session):
    """Create database triggers for automatic updates."""
    triggers = [
        # Trigger to update question stats when answers are added/removed
        """
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
        
        DROP TRIGGER IF EXISTS trigger_answer_stats ON answers;
        CREATE TRIGGER trigger_answer_stats
            AFTER INSERT OR UPDATE OR DELETE ON answers
            FOR EACH ROW EXECUTE FUNCTION trigger_update_question_stats();
        """,

        # Trigger to update user reputation when votes change
        """
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
        
        DROP TRIGGER IF EXISTS trigger_vote_reputation ON votes;
        CREATE TRIGGER trigger_vote_reputation
            AFTER INSERT OR UPDATE OR DELETE ON votes
            FOR EACH ROW EXECUTE FUNCTION trigger_update_user_reputation();
        """,
    ]

    for trigger_sql in triggers:
        try:
            db.execute(text(trigger_sql))
            logger.info("Created database trigger successfully")
        except Exception as e:
            logger.warning(f"Could not create database trigger: {e}")

    db.commit()


def optimize_postgresql_settings(db: Session):
    """Apply PostgreSQL-specific performance settings."""
    settings = [
        "SET shared_preload_libraries = 'pg_stat_statements';",
        "SET track_activity_query_size = 2048;",
        "SET log_min_duration_statement = 1000;",  # Log slow queries
    ]

    for setting in settings:
        try:
            db.execute(text(setting))
            logger.info(f"Applied setting: {setting}")
        except Exception as e:
            logger.warning(f"Could not apply setting {setting}: {e}")


def setup_database_optimizations(db: Session):
    """Set up all database optimizations."""
    logger.info("Setting up database optimizations...")

    try:
        create_postgresql_extensions(db)
        create_custom_indexes(db)
        create_database_functions(db)
        create_database_triggers(db)
        optimize_postgresql_settings(db)

        logger.info("✅ Database optimizations completed successfully!")
    except Exception as e:
        logger.error(f"❌ Error setting up database optimizations: {e}")
        raise
