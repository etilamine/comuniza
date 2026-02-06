# Comuniza - Community Sharing Platform

## Project Overview

**Comuniza** is a Django-based web platform designed to facilitate community sharing of items, books, tools, and equipment within private groups. The platform enables users to create communities, share items, manage loans, and build reputation through a trusted borrowing system.

## Core Architecture

### Technology Stack
- **Backend**: Django 4.2.11 with Django REST Framework
- **Database**: MySQL/MariaDB with optimized indexing
- **Cache**: Redis with multi-layer caching strategy
- **Task Queue**: Celery for background processing
- **Frontend**: Django templates with HTMX for dynamic interactions
- **Authentication**: Django Allauth with social login support
- **Containerization**: Docker with multi-stage builds

### Key Features

#### 1. User Management & Privacy
- **Privacy-focused authentication** with email-based login
- **Auto-generated usernames** (Reddit-style) for anonymity
- **Granular privacy controls** for profile, email, and activity visibility
- **Hashed contact information** for enhanced privacy
- **Social authentication** via Google and GitHub

#### 2. Community Groups
- **Private/public groups** with location-based organization
- **Membership management** with roles (member/admin) and invitations
- **Group-specific settings** for loan visibility and item approval
- **Geographic mapping** with city/country coordinates

#### 3. Item Management
- **Comprehensive item catalog** with categories, conditions, and metadata
- **Book-specific features** including ISBN lookup and automatic cover fetching
- **Multi-image support** with primary image selection
- **Wishlist functionality** for tracking desired items
- **Item reviews and ratings** system

#### 4. Loan System
- **Complete loan lifecycle** from request to return
- **Flexible loan terms** with deposits and extensions
- **Condition tracking** for pickup and return
- **Privacy controls** for loan visibility
- **Automated status updates** and notifications

#### 5. Reputation & Trust
- **User reputation scoring** based on loan history
- **Trust algorithm** considering ratings, timeliness, and reliability
- **Badge system** for achievements and milestones
- **Two-way reviews** between lenders and borrowers

#### 6. Advanced Features
- **Real-time notifications** via email and in-app messaging
- **Search functionality** across items and users
- **Performance optimization** with ultra-caching system
- **Comprehensive admin interface** with management commands

## Database Schema

### Core Models
- **User**: Custom user model with privacy features (`apps/users/models.py:24`)
- **Group**: Community management with location data (`apps/groups/models.py:12`)
- **Item**: Detailed item catalog with book-specific metadata (`apps/items/models.py:53`)
- **Loan**: Complete loan transaction tracking (`apps/loans/models.py:14`)
- **UserReputation**: Aggregated trust scoring (`apps/loans/models.py:361`)

### Key Relationships
- Users can own multiple items and participate in multiple groups
- Items can be shared across multiple groups
- Loans connect borrowers, lenders, items, and groups
- Reviews impact reputation scores for both parties

## Development Infrastructure

### Docker Configuration
- **Multi-stage builds** for optimized production images
- **Development environment** with hot reload support
- **Service orchestration** including database, Redis, and email testing
- **Volume management** for persistent data

### Deployment Strategy
- **Environment-specific configurations** (development/production)
- **Health checks** for all services
- **Automated migrations** and static file collection
- **Non-root user execution** for security

## Performance Optimizations

### Caching Strategy
- **Multi-layer caching** with Redis backend
- **Ultra-cache system** for item details and lists (`apps/core/ultra_cache.py`)
- **Cache invalidation** on data changes
- **Query optimization** with proper indexing

### Database Design
- **Optimized indexes** for common query patterns
- **Efficient relationships** with proper foreign keys
- **Bulk operations** for improved performance
- **Connection pooling** with configurable timeouts

## Security Features

### Privacy Protection
- **Email/phone hashing** for verification without exposure (`apps/users/utils/privacy.py`)
- **Granular visibility controls** for all user data
- **Secure authentication** with email verification
- **Role-based permissions** throughout the platform

### Data Security
- **SQL injection prevention** via Django ORM
- **CSRF protection** with proper middleware
- **Secure file uploads** with validation
- **Environment-based configuration** for secrets

## Notification System

### Real-time Updates
- **Celery-powered background tasks** for email delivery
- **In-app messaging** for loan activities
- **Email templates** for various user actions
- **Configurable notification preferences**

## Badge & Gamification

### Achievement System
- **Automatic badge awarding** for milestones (`apps/badges/services.py`)
- **Reputation-based badges** (Top Lender, Reliable Borrower)
- **Activity tracking** for community engagement
- **Leaderboard functionality** for competitive elements

## API & Integration

### REST API
- **Django REST Framework** for API endpoints
- **Swagger documentation** with drf-yasg
- **CORS support** for frontend integration
- **Filtering and pagination** for large datasets

### External Services
- **Book cover fetching** from Open Library API (`apps/books/services.py`)
- **Social authentication** providers
- **Email service integration** with MailCatcher for development

## Monitoring & Maintenance

### Management Commands
- **Database migration utilities** with safe migration scripts
- **Cache warming** for improved performance (`apps/core/cache_warming.py`)
- **User management** tools for administrators
- **Data cleanup** and maintenance commands

### Logging & Debugging
- **Comprehensive logging** throughout the application
- **Debug toolbar** integration for development
- **Error tracking** with proper exception handling
- **Performance monitoring** with query analysis

## Project Structure

```
comuniza-dev/src/
├── apps/                    # Django applications
│   ├── users/              # User management and privacy
│   ├── groups/             # Community groups
│   ├── items/              # Item catalog and management
│   ├── loans/              # Loan system and reputation
│   ├── notifications/      # Notification system
│   ├── messaging/          # In-app messaging
│   ├── badges/             # Achievement system
│   ├── search/             # Search functionality
│   ├── books/              # Book-specific services
│   └── core/               # Core utilities and caching
├── core/                   # Django project configuration
│   ├── settings/           # Environment-specific settings
│   └── urls.py             # Root URL configuration
├── templates/              # Django templates
├── static/                 # Static assets
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container configuration
├── Makefile               # Development commands
└── requirements.txt       # Python dependencies
```

## Quick Start

### Development Environment
```bash
# Start development environment
make dev

# Build containers
make build

# Run database migrations
make migrate

# Create superuser
make superuser

# View logs
make logs
```

### Production Environment
```bash
# Start production environment
make prod

# Run production migrations
make migrate-prod

# Collect static files
make collectstatic-prod
```

## Code Quality & Recent Improvements

Recent optimizations to ensure production-ready, maintainable codebase:

### Code Cleanup
- Removed all DEBUG logging statements from production code
- Cleaned up TODO comments with clear implementation notes
- Optimized `.gitignore` for better maintainability and security
- Removed non-existent entries and duplicate configurations

### Development Experience
- Improved code maintainability and professional presentation
- Enhanced logging for production environments while maintaining development support
- Documented features not yet implemented with clear notes
- Collaborated on improving existing codebase structure and organization

### Security & Best Practices
- Environment variable configuration for all sensitive data
- No hardcoded credentials or API keys in codebase
- Proper error handling and exception logging
- Followed Django and Python best practices throughout

## Future Extensibility

The platform is designed for growth with:
- **Modular app structure** for easy feature additions
- **Plugin-ready architecture** for third-party integrations
- **Scalable database design** for increased load
- **API-first approach** for mobile app development

Comuniza represents a comprehensive solution for community-based sharing, combining robust technical architecture with user-centric design principles to foster trust and collaboration within local communities.
