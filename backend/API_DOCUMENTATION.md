# StackIt API Documentation

## Overview

The StackIt API is a RESTful web service built with FastAPI that provides a complete backend for a Q&A forum platform. It includes user authentication, question and answer management, voting, tagging, comments, and real-time notifications.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

**POST** `/auth/login`

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "is_verified": true
  }
}
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login user | No |
| POST | `/auth/logout` | Logout user | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| POST | `/auth/refresh` | Refresh access token | Yes |

### User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users/` | List users (paginated) | No |
| GET | `/users/me` | Get my profile | Yes |
| PUT | `/users/me` | Update my profile | Yes |
| POST | `/users/me/change-password` | Change password | Yes |
| GET | `/users/{user_id}` | Get user profile | No |
| GET | `/users/{user_id}/stats` | Get user statistics | No |
| DELETE | `/users/{user_id}` | Delete user (Admin only) | Yes |

### Questions

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/questions/` | List questions (paginated) | No |
| POST | `/questions/` | Create question | Yes |
| GET | `/questions/{question_id}` | Get question details | No |
| PUT | `/questions/{question_id}` | Update question | Yes |
| DELETE | `/questions/{question_id}` | Delete question | Yes |

### Answers

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/answers/` | List answers (paginated) | No |
| POST | `/answers/` | Create answer | Yes |
| GET | `/answers/{answer_id}` | Get answer details | No |
| PUT | `/answers/{answer_id}` | Update answer | Yes |
| POST | `/answers/{answer_id}/accept` | Accept/unaccept answer | Yes |
| DELETE | `/answers/{answer_id}` | Delete answer | Yes |

### Voting

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/votes/` | Cast vote on answer | Yes |
| PUT | `/votes/{vote_id}` | Update vote | Yes |
| DELETE | `/votes/{vote_id}` | Remove vote | Yes |
| GET | `/votes/answer/{answer_id}/my-vote` | Get my vote on answer | Yes |

### Tags

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/tags/` | List tags (paginated) | No |
| GET | `/tags/popular` | Get popular tags | No |
| GET | `/tags/search` | Search tags | No |
| POST | `/tags/` | Create tag (Admin only) | Yes |
| GET | `/tags/{tag_id}` | Get tag details | No |
| GET | `/tags/name/{tag_name}` | Get tag by name | No |
| PUT | `/tags/{tag_id}` | Update tag (Admin only) | Yes |
| DELETE | `/tags/{tag_id}` | Delete tag (Admin only) | Yes |
| GET | `/tags/{tag_id}/questions` | Get questions with tag | No |

### Comments

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/comments/` | List comments (paginated) | No |
| POST | `/comments/` | Create comment | Yes |
| GET | `/comments/{comment_id}` | Get comment details | No |
| PUT | `/comments/{comment_id}` | Update comment | Yes |
| DELETE | `/comments/{comment_id}` | Delete comment | Yes |

### Notifications

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/notifications/` | List my notifications | Yes |
| GET | `/notifications/summary` | Get notification summary | Yes |
| GET | `/notifications/{notification_id}` | Get notification details | Yes |
| PUT | `/notifications/{notification_id}` | Mark as read/unread | Yes |
| POST | `/notifications/mark-all-read` | Mark all as read | Yes |
| POST | `/notifications/bulk-update` | Bulk update notifications | Yes |
| DELETE | `/notifications/{notification_id}` | Delete notification | Yes |

## Request/Response Examples

### Create Question

**POST** `/questions/`

```json
{
  "title": "How to implement JWT authentication in FastAPI?",
  "description": "I'm building a FastAPI application and need to implement JWT authentication. What's the best approach?",
  "tag_names": ["fastapi", "jwt", "authentication", "python"]
}
```

**Response:**
```json
{
  "id": 1,
  "title": "How to implement JWT authentication in FastAPI?",
  "description": "I'm building a FastAPI application...",
  "view_count": 0,
  "vote_score": 0,
  "answer_count": 0,
  "is_closed": false,
  "has_accepted_answer": false,
  "author_id": 1,
  "accepted_answer_id": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "author": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe",
    "avatar_url": null,
    "reputation_score": 150
  },
  "tags": [
    {
      "id": 1,
      "name": "fastapi",
      "description": "FastAPI Python web framework",
      "color": "#009688",
      "usage_count": 25
    }
  ]
}
```

### Create Answer

**POST** `/answers/`

```json
{
  "question_id": 1,
  "content": "You can implement JWT authentication in FastAPI using the `python-jose` library..."
}
```

### Cast Vote

**POST** `/votes/`

```json
{
  "answer_id": 1,
  "is_upvote": true
}
```

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (default: 1)
- `size`: Items per page (default: 20, max: 100)

**Example:**
```
GET /questions/?page=2&size=10
```

**Response includes pagination metadata:**
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "size": 10,
  "pages": 15,
  "has_next": true,
  "has_prev": true
}
```

## Filtering and Searching

### Questions
- `search`: Search in title and description
- `tags`: Filter by tag names (multiple allowed)
- `author_id`: Filter by author
- `has_accepted_answer`: Filter by accepted answer status
- `is_closed`: Filter by closed status
- `sort_by`: Sort field (created_at, vote_score, view_count, answer_count)
- `order`: Sort order (asc, desc)

### Users
- `search`: Search by username or full name
- `sort_by`: Sort field (created_at, username, reputation_score)
- `order`: Sort order (asc, desc)

### Tags
- `search`: Search by tag name
- `sort_by`: Sort field (name, usage_count, created_at)
- `order`: Sort order (asc, desc)
- `min_usage`: Minimum usage count

## Error Handling

The API returns consistent error responses:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "type": "ErrorType"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Access denied
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., duplicate username)
- `DATABASE_ERROR`: Database operation failed
- `RATE_LIMIT_ERROR`: Rate limit exceeded

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

The API implements rate limiting based on user reputation:

- **New users** (< 100 reputation): Limited requests per day
- **Regular users** (100+ reputation): Higher limits
- **High reputation users** (1000+ reputation): Even higher limits
- **Admins**: Unlimited requests

## Real-time Features

The API supports real-time notifications using PostgreSQL's LISTEN/NOTIFY mechanism with py-pg-notify integration.

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## SDK and Client Libraries

The API follows OpenAPI 3.0 specification, making it easy to generate client libraries for various programming languages using tools like:
- OpenAPI Generator
- Swagger Codegen
- AutoRest

## Webhooks (Future Feature)

Planned webhook support for external integrations:
- New question posted
- Answer accepted
- User reputation milestones
- Moderation events
