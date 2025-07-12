# StackIt FastAPI Backend

A complete, production-ready FastAPI backend for a Q&A forum platform with comprehensive database integration, authentication, and real-time features.

## 🚀 Features

### Core Functionality
- **User Management**: Registration, authentication, profiles, and role-based access control
- **Q&A System**: Create, edit, and manage questions and answers
- **Voting System**: Upvote/downvote answers with reputation tracking
- **Tagging System**: Categorize questions with multi-select tags
- **Comment System**: Comment on answers for additional discussion
- **Real-time Notifications**: PostgreSQL-based notification system

### Technical Features
- **JWT Authentication**: Secure token-based authentication
- **Database Integration**: Complete SQLAlchemy ORM with PostgreSQL
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Error Handling**: Comprehensive error handling and logging
- **Performance Optimization**: Database indexing and query optimization
- **Data Validation**: Pydantic schemas with comprehensive validation
- **Migration System**: Alembic-based database migrations

## 🏗️ Architecture

```
backend/
├── app/
│   ├── api/v1/              # API route handlers
│   ├── auth/                # Authentication system
│   ├── core/                # Core utilities (logging, exceptions)
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic request/response models
│   ├── config.py            # Application configuration
│   ├── database.py          # Database connection and session management
│   └── main.py              # FastAPI application entry point
├── alembic/                 # Database migration files
├── logs/                    # Application logs
├── tests/                   # Test files
├── manage_db.py             # Database management CLI
├── setup_database.py       # Automated database setup
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd StackIt-odoo/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database (automated)
python setup_database.py

# Start development server
uvicorn app.main:app --reload
```

### Access Points
- **API Base**: http://localhost:8000/api/v1
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Documentation

### Authentication
```bash
# Register new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=SecurePass123!"
```

### Questions
```bash
# Create question
curl -X POST "http://localhost:8000/api/v1/questions/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "How to use FastAPI with PostgreSQL?",
    "description": "I need help setting up FastAPI with PostgreSQL...",
    "tag_names": ["fastapi", "postgresql", "python"]
  }'

# List questions
curl "http://localhost:8000/api/v1/questions/?page=1&size=10"
```

### Complete API Reference
See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for comprehensive API documentation.

## 🗄️ Database

### Schema Overview
- **8 core tables** with proper relationships
- **25+ optimized indexes** for performance
- **PostgreSQL-specific optimizations** with extensions
- **Complete referential integrity** with cascade rules

### Management Commands
```bash
# Database operations
python manage_db.py check-connection
python manage_db.py create-tables
python manage_db.py seed-data
python manage_db.py setup-optimizations

# Migrations
python manage_db.py generate-migration -m "Description"
python manage_db.py migrate
python manage_db.py current
```

### Database Documentation
- [DATABASE_DESIGN.md](DATABASE_DESIGN.md) - Detailed schema design
- [DATABASE_README.md](DATABASE_README.md) - Setup and usage guide
- [DATABASE_SUMMARY.md](DATABASE_SUMMARY.md) - Complete overview

## 🔧 Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/stackit_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Docker Setup
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
python manage_db.py migrate
```

## 🧪 Testing

```bash
# Run all tests
python test_database.py

# Run specific test types
python test_database.py --manual
python test_database.py --pytest

# Database integrity tests
python manage_db.py check-connection
```

## 📊 Performance Features

### Database Optimizations
- **Comprehensive indexing** for all query patterns
- **Full-text search** with PostgreSQL GIN indexes
- **Automated statistics** updates via triggers
- **Connection pooling** and health monitoring

### API Performance
- **Request/response logging** with timing
- **Error tracking** and monitoring
- **Rate limiting** based on user reputation
- **Efficient pagination** for large datasets

## 🔒 Security

### Authentication & Authorization
- **JWT tokens** with configurable expiration
- **Password hashing** with bcrypt
- **Role-based access control** (Guest, User, Admin)
- **Email verification** requirements

### Data Protection
- **SQL injection prevention** via parameterized queries
- **Input validation** with Pydantic schemas
- **CORS configuration** for frontend integration
- **Security logging** for audit trails

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up HTTPS with reverse proxy
- [ ] Configure database SSL
- [ ] Set up monitoring and logging
- [ ] Configure automated backups

## 📈 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database health
python manage_db.py check-connection
```

### Logging
- **Structured logging** with JSON format option
- **Performance monitoring** for slow queries
- **Security event logging** for authentication
- **Error tracking** with detailed stack traces

## 🔄 Development Workflow

### Adding New Features
1. **Database Changes**: Update models → Generate migration → Apply migration
2. **API Changes**: Create schemas → Add endpoints → Update documentation
3. **Testing**: Write tests → Run test suite → Verify functionality

### Code Quality
```bash
# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy app/
```

## 📖 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup and deployment guide
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
- **[DATABASE_DESIGN.md](DATABASE_DESIGN.md)** - Database schema documentation
- **Interactive Docs** - Available at `/docs` endpoint

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

### Troubleshooting
- Check [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting section
- Review application logs in `logs/` directory
- Verify database connection with `python manage_db.py check-connection`

### Resources
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database Management**: `python manage_db.py --help`

---

**Built with ❤️ using FastAPI, PostgreSQL, and modern Python practices.**
