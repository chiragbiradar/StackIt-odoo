# StackIt Database Design Documentation

## Overview

This document provides a comprehensive overview of the database schema design for StackIt, a minimal Q&A forum platform. The design follows PostgreSQL best practices and is optimized for the specific requirements outlined in the PRD.

## Database Schema Overview

The StackIt database consists of 8 main entities designed to support a Q&A platform with user management, content creation, voting, and real-time notifications.

### Core Entities

1. **Users** - User accounts and authentication
2. **Questions** - User-submitted questions
3. **Answers** - Responses to questions
4. **Tags** - Content categorization system
5. **QuestionTags** - Many-to-many relationship between questions and tags
6. **Votes** - User voting on answers
7. **Comments** - Comments on answers
8. **Notifications** - Real-time user notifications

## Entity Relationship Diagram

```
Users (1) ----< Questions (1) ----< Answers (1) ----< Votes
  |                |                    |
  |                |                    |
  |                |                    +----< Comments
  |                |
  |                +----< QuestionTags >----< Tags
  |
  +----< Notifications
```

## Detailed Schema Design

### 1. Users Table

**Purpose**: Store user accounts, authentication data, and profile information.

**Key Design Decisions**:
- Separate `username` and `email` for flexibility
- Role-based access control with enum
- Reputation system for gamification
- Soft statistics (questions_count, answers_count) for performance

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `username`: Unique username (50 chars, indexed)
- `email`: Unique email address (255 chars, indexed)
- `hashed_password`: Bcrypt hashed password
- `full_name`: Optional display name
- `bio`: User biography (TEXT)
- `avatar_url`: Profile picture URL
- `is_active`: Account status flag
- `is_verified`: Email verification status
- `role`: Enum (GUEST, USER, ADMIN)
- `reputation_score`: Calculated reputation points
- `questions_count`: Denormalized question count
- `answers_count`: Denormalized answer count
- `created_at`, `updated_at`: Timestamps

**Indexes**:
- Primary key on `id`
- Unique indexes on `username` and `email`
- Composite index on `(is_active, role)` for admin queries
- Composite index on `(username, email)` for search
- B-tree index on `reputation_score` for leaderboards

### 2. Questions Table

**Purpose**: Store user questions with rich text content and metadata.

**Key Design Decisions**:
- Rich text support for descriptions
- Denormalized statistics for performance
- Soft delete capability with `is_closed`
- Self-referencing for accepted answers

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `title`: Question title (200 chars, indexed)
- `description`: Rich text content (TEXT)
- `view_count`: Number of views
- `vote_score`: Calculated vote score
- `answer_count`: Number of answers
- `is_closed`: Whether question accepts new answers
- `has_accepted_answer`: Quick lookup flag
- `author_id` (FK): Reference to Users table
- `accepted_answer_id` (FK): Reference to Answers table (nullable)
- `created_at`, `updated_at`: Timestamps

**Indexes**:
- Primary key on `id`
- Foreign key index on `author_id`
- Composite index on `(created_at, is_closed)` for listing
- B-tree index on `vote_score` for sorting
- Composite index on `(has_accepted_answer, created_at)`
- Composite index on `(author_id, created_at)` for user's questions
- GIN index on `title` for full-text search (PostgreSQL specific)

### 3. Answers Table

**Purpose**: Store user answers to questions with voting support.

**Key Design Decisions**:
- Rich text content support
- Denormalized vote scores for performance
- Comment count for UI display
- Acceptance status for question resolution

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `content`: Rich text answer content (TEXT)
- `vote_score`: Net vote score (upvotes - downvotes)
- `comment_count`: Number of comments
- `is_accepted`: Whether this is the accepted answer
- `question_id` (FK): Reference to Questions table
- `author_id` (FK): Reference to Users table
- `created_at`, `updated_at`: Timestamps

**Indexes**:
- Primary key on `id`
- Composite index on `(question_id, created_at)` for question answers
- Composite index on `(is_accepted, question_id)` for accepted answers
- B-tree index on `vote_score` for sorting
- Composite index on `(author_id, created_at)` for user's answers

### 4. Tags Table

**Purpose**: Categorization system for questions.

**Key Design Decisions**:
- Unique tag names for consistency
- Color coding for UI display
- Usage statistics for popularity tracking
- Extensible description field

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `name`: Unique tag name (50 chars, indexed)
- `description`: Tag description (TEXT)
- `color`: Hex color code for display
- `usage_count`: Number of times used
- `created_at`, `updated_at`: Timestamps

**Indexes**:
- Primary key on `id`
- Unique index on `name`

### 5. QuestionTags Table (Junction Table)

**Purpose**: Many-to-many relationship between Questions and Tags.

**Key Design Decisions**:
- Separate junction table for flexibility
- Composite unique constraint to prevent duplicates
- Cascade deletes for data integrity

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `question_id` (FK): Reference to Questions table
- `tag_id` (FK): Reference to Tags table
- `created_at`, `updated_at`: Timestamps

**Constraints**:
- Unique constraint on `(question_id, tag_id)`
- Foreign key constraints with CASCADE delete

### 6. Votes Table

**Purpose**: User voting system for answers.

**Key Design Decisions**:
- Boolean flag for upvote/downvote simplicity
- One vote per user per answer constraint
- Cascade deletes for data integrity

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `is_upvote`: Boolean (true = upvote, false = downvote)
- `user_id` (FK): Reference to Users table
- `answer_id` (FK): Reference to Answers table
- `created_at`, `updated_at`: Timestamps

**Constraints**:
- Unique constraint on `(user_id, answer_id)`
- Foreign key constraints with CASCADE delete

### 7. Comments Table

**Purpose**: Comments on answers for additional discussion.

**Key Design Decisions**:
- Simple text content (no rich text for comments)
- Hierarchical structure possible with future parent_id
- Cascade deletes for data integrity

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `content`: Comment text content (TEXT)
- `answer_id` (FK): Reference to Answers table
- `author_id` (FK): Reference to Users table
- `created_at`, `updated_at`: Timestamps

**Indexes**:
- Primary key on `id`
- Composite index on `(answer_id, created_at)` for answer comments
- Index on `author_id` for user's comments

### 8. Notifications Table

**Purpose**: Real-time notification system for user engagement.

**Key Design Decisions**:
- Flexible notification types with enum
- Optional references to related entities
- Read/unread status tracking
- Triggered by user tracking

**Columns**:
- `id` (PK): Auto-incrementing primary key
- `title`: Notification title (200 chars)
- `message`: Notification content (TEXT)
- `notification_type`: Enum for different notification types
- `is_read`: Read status flag
- `user_id` (FK): Recipient user
- `triggered_by_user_id` (FK): User who triggered notification
- `related_question_id` (FK): Optional question reference
- `related_answer_id` (FK): Optional answer reference
- `related_comment_id` (FK): Optional comment reference
- `created_at`, `updated_at`: Timestamps

**Indexes**:
- Primary key on `id`
- Composite index on `(user_id, is_read, created_at)` for unread notifications
- Composite index on `(notification_type, created_at)` for type filtering
- Composite index on `(user_id, created_at)` for user's notifications

## Performance Optimizations

### 1. Indexing Strategy

**Primary Indexes**:
- All foreign keys are indexed for join performance
- Unique constraints on business keys (username, email, tag names)
- Composite indexes for common query patterns

**Query-Specific Indexes**:
- Questions by creation date and status
- Answers by question and creation date
- Unread notifications by user
- User reputation rankings

**PostgreSQL-Specific Optimizations**:
- GIN indexes for full-text search on question titles
- Trigram indexes for fuzzy search capabilities
- Partial indexes for active users and unread notifications only

### 2. Denormalization

**Strategic Denormalization**:
- Vote scores stored in answers table (calculated via triggers)
- Answer counts stored in questions table
- User statistics (question/answer counts, reputation)
- Tag usage counts

**Benefits**:
- Faster read queries for common operations
- Reduced complex joins for statistics
- Better user experience with quick loading

### 3. Database Functions and Triggers

**Automated Statistics Updates**:
- Triggers to update question statistics when answers change
- Triggers to update user reputation when votes change
- Functions for complex calculations

**Search Functions**:
- Full-text search function for questions
- Fuzzy search capabilities with trigrams

## Data Integrity and Constraints

### 1. Foreign Key Constraints

All relationships use foreign key constraints with appropriate cascade rules:
- CASCADE DELETE: For dependent data (votes, comments, notifications)
- SET NULL: For optional references (accepted_answer_id)

### 2. Check Constraints

- Email format validation
- Positive values for counts and scores where appropriate
- Valid color codes for tags

### 3. Unique Constraints

- Username and email uniqueness
- One vote per user per answer
- One tag per question (via junction table)

## Scalability Considerations

### 1. Horizontal Scaling

**Read Replicas**:
- Read-heavy queries can be distributed to replicas
- Statistics and search queries are good candidates

**Partitioning Strategy**:
- Questions and answers can be partitioned by date
- Notifications can be partitioned by user_id ranges

### 2. Caching Strategy

**Application-Level Caching**:
- Popular questions and their answers
- User profiles and statistics
- Tag lists and usage counts

**Database-Level Caching**:
- PostgreSQL query result caching
- Materialized views for complex aggregations

### 3. Archive Strategy

**Data Lifecycle**:
- Old notifications can be archived or deleted
- Inactive user data can be moved to cold storage
- Question/answer history can be compressed

## Security Considerations

### 1. Data Protection

**Sensitive Data**:
- Passwords are hashed using bcrypt
- Email addresses are indexed but not exposed in logs
- User PII is protected with appropriate access controls

**SQL Injection Prevention**:
- All queries use parameterized statements
- SQLAlchemy ORM provides built-in protection
- Input validation at application layer

### 2. Access Control

**Role-Based Security**:
- User roles control access to admin functions
- Row-level security can be implemented for multi-tenancy
- API-level authorization for all operations

## Migration and Deployment

### 1. Database Migrations

**Alembic Integration**:
- Version-controlled schema changes
- Rollback capabilities for failed deployments
- Automated migration testing

**Migration Strategy**:
- Backward-compatible changes when possible
- Data migration scripts for complex changes
- Zero-downtime deployment support

### 2. Environment Management

**Configuration Management**:
- Environment-specific database settings
- Connection pooling configuration
- Performance tuning parameters

**Monitoring and Alerting**:
- Query performance monitoring
- Connection pool monitoring
- Disk space and backup monitoring

## Conclusion

This database design provides a solid foundation for the StackIt Q&A platform, balancing normalization with performance optimization. The schema supports all requirements from the PRD while providing room for future growth and feature additions.

The design emphasizes:
- **Performance**: Through strategic indexing and denormalization
- **Scalability**: With partitioning and caching strategies
- **Maintainability**: Through clear relationships and constraints
- **Security**: With proper data protection and access controls
- **Flexibility**: For future feature additions and modifications
