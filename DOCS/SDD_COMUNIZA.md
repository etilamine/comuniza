# Software Design Document (SDD)
# Comuniza - Community Sharing Platform

## 1. Introduction

### 1.1 Purpose
This document describes the software architecture and design of Comuniza, a privacy-focused community sharing platform built on Django with sustainable, permacomputing principles.

### 1.2 Scope
The design covers the complete system architecture including backend services, database design, API structure, security implementation, and future extensibility for mobile and federated features.

### 1.3 Design Philosophy
- **Permacomputing**: Low energy, sustainable, maintainable 10+ years
- **Privacy-First**: User data protection and anonymity by design
- **Volunteer-Friendly**: Simple technology stack, easy to understand
- **Anarchistic**: No vendor lock-in, open standards

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
├─────────────────────┬───────────────────┬───────────────────┤
│   Web Frontend      │   Mobile App      │   Admin Interface │
│   Django Templates  │   Flutter (Phase 2)│   Django Admin    │
│   + HTMX + Alpine   │   + SQLite Cache  │   + Custom Tools  │
└─────────────────────┴───────────────────┴───────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                    Application Layer                           │
├─────────────────────┬───────────────────┬───────────────────┤
│   Django Views      │   REST API        │   Background Tasks │
│   + HTMX Handlers   │   DRF ViewSets    │   Celery Workers   │
│   + Template Render │   + JWT Auth      │   + Event Processing│
└─────────────────────┴───────────────────┴───────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                     Business Layer                            │
├─────────────────────┬───────────────────┬───────────────────┤
│   Domain Services   │   Event System    │   Security Layer   │
│   + LoanService     │   + EventBus      │   + Encryption     │
│   + BadgeService    │   + Handlers      │   + Rate Limiting  │
│   + NotificationSvc │   + Async Tasks   │   + Audit Logging  │
└─────────────────────┴───────────────────┴───────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                     Data Layer                                │
├─────────────────────┬───────────────────┬───────────────────┤
│   Database          │   Cache Layer     │   File Storage    │
│   PostgreSQL        │   Redis           │   Local Files     │
│   + Optimized Index │   + Ultra Cache   │   + Image Processing│
└─────────────────────┴───────────────────┴───────────────────┘
```

### 2.2 Architectural Patterns

#### 2.2.1 Domain-Driven Design (DDD)
- **Bounded Contexts**: Each Django app represents a bounded context
- **Domain Services**: Business logic encapsulated in service classes
- **Event-Driven Architecture**: Decoupled communication via domain events

#### 2.2.2 Clean Architecture Principles
- **Dependency Inversion**: Core business logic independent of frameworks
- **Separation of Concerns**: Clear boundaries between layers
- **Testability**: Each layer independently testable

#### 2.2.3 Event-Driven Architecture
- **Domain Events**: Business events published via EventBus
- **Async Processing**: Celery handlers for non-blocking operations
- **Loose Coupling**: Services communicate via events, not direct calls

## 3. Component Design

### 3.1 Django Apps Architecture

#### 3.1.1 Core Apps Structure
```
apps/
├── users/              # User management and privacy
│   ├── models.py       # CustomUser, PrivacySettings
│   ├── services.py     # UserService, PrivacyService
│   └── utils/          # Privacy utilities, hashing
├── groups/             # Community groups
│   ├── models.py       # Group, GroupMembership
│   ├── services.py     # GroupService, MembershipService
│   └── managers.py     # Custom query managers
├── items/              # Item catalog and management
│   ├── models.py       # Item, ItemCategory, ItemImage
│   ├── services.py     # ItemService, BookService
│   └── managers.py     # Item query managers
├── loans/              # Loan system and reputation
│   ├── models.py       # Loan, LoanSettings, UserReputation
│   ├── services.py     # LoanService, ReputationService
│   └── managers.py     # Loan query managers
├── messaging/          # E2EE communication
│   ├── models.py       # Conversation, Message
│   ├── services.py     # MessageService, EncryptionService
│   └── utils/          # Encryption utilities
├── notifications/      # Notification system
│   ├── models.py       # Notification, NotificationType
│   ├── services.py     # NotificationService
│   └── tasks.py        # Celery email tasks
├── badges/             # Achievement system
│   ├── models.py       # Badge, UserBadge
│   ├── services.py     # BadgeService, AchievementService
│   └── management/     # Badge seeding commands
├── core/               # Shared utilities
│   ├── events.py       # EventBus, domain events
│   ├── cache.py        # Ultra cache implementation
│   ├── encryption.py   # Security utilities
│   ├── audit.py        # Audit logging
│   └── middleware.py   # Custom middleware
└── api/                # REST API endpoints
    ├── viewsets.py     # DRF ViewSets
    ├── serializers.py  # API serializers
    └── permissions.py  # API permissions
```

### 3.2 Database Design

#### 3.2.1 Schema Overview
```sql
-- User Management
users_user (id, email, username, created_at, is_active)
users_privacysettings (user_id, profile_visibility, email_visibility)

-- Community Groups
groups_group (id, name, description, location_city, location_country, is_private)
groups_groupmembership (id, group_id, user_id, role, joined_at)

-- Item Catalog
items_item (id, owner_id, name, description, category_id, condition)
items_itemcategory (id, name, parent_id)
items_itemimage (id, item_id, image, is_primary)

-- Loan System
loans_loan (id, item_id, borrower_id, lender_id, status, start_date, end_date)
loans_userreputation (user_id, score, reliability_rating, timeliness_rating)

-- Messaging
messaging_conversation (id, salt, created_at)
messaging_message (id, conversation_id, sender_id, encrypted_content, timestamp)

-- Notifications
notifications_notification (id, user_id, notification_type, content, is_read)

-- Badges
badges_badge (id, name, description, category, condition)
badges_userbadge (id, user_id, badge_id, awarded_at)

-- Audit Logging
core_auditlog (id, user_id, action, resource_type, resource_id, timestamp, ip_address)
```

#### 3.2.2 Key Relationships
- **Users ↔ Groups**: Many-to-many through GroupMembership
- **Users ↔ Items**: One-to-many (ownership)
- **Items ↔ Groups**: Many-to-many (sharing across groups)
- **Users ↔ Loans**: One-to-many (as borrower and lender)
- **Loans ↔ Reviews**: One-to-many (two-way reviews)

#### 3.2.3 Indexing Strategy
```sql
-- Performance-critical indexes
CREATE INDEX idx_items_owner_category ON items_item(owner_id, category_id);
CREATE INDEX idx_loans_borrower_status ON loans_loan(borrower_id, status);
CREATE INDEX idx_loans_lender_status ON loans_loan(lender_id, status);
CREATE INDEX idx_groupmembership_group_role ON groups_groupmembership(group_id, role);
CREATE INDEX idx_notifications_user_unread ON notifications_notification(user_id, is_read);
CREATE INDEX idx_auditlog_user_timestamp ON core_auditlog(user_id, timestamp);

-- Composite indexes for common queries
CREATE INDEX idx_items_category_available ON items_item(category_id, status) WHERE status = 'available';
CREATE INDEX idx_loans_active_dates ON loans_loan(status, start_date, end_date) WHERE status IN ('active', 'pending');
```

### 3.3 API Design

#### 3.3.1 REST API Structure
```
/api/v1/
├── auth/
│   ├── token/              # JWT login
│   ├── token/refresh/     # Token refresh
│   └── logout/            # Token blacklist
├── users/
│   ├── me/                # Current user profile
│   ├── {id}/              # Public user profiles
│   └── me/privacy/        # Privacy settings
├── groups/
│   ├── /                  # List user's groups
│   ├── {id}/              # Group details
│   ├── {id}/members/      # Group membership
│   └── {id}/join/         # Join group
├── items/
│   ├── /                  # Item listing with filters
│   ├── {id}/              # Item details
│   ├── {id}/borrow/       # Borrow request
│   └── categories/        # Item categories
├── loans/
│   ├── /                  # User's loans
│   ├── {id}/              # Loan details
│   ├── {id}/approve/      # Approve loan
│   └── {id}/return/       # Return item
├── conversations/
│   ├── /                  # User's conversations
│   ├── {id}/              # Conversation details
│   └── {id}/messages/     # Messages in conversation
└── notifications/
    ├── /                  # User's notifications
    └── {id}/mark-read/    # Mark notification read
```

#### 3.3.2 Authentication & Authorization
```python
# JWT Authentication with refresh tokens
class JWTAuthentication:
    - Access token: 15 minutes
    - Refresh token: 7 days
    - Automatic token refresh
    - Token blacklist on logout

# Permission System
class IsOwnerOrMember(BasePermission):
    - Object-level permissions
    - Group membership checks
    - Privacy settings enforcement
```

### 3.4 Security Design

#### 3.4.1 Privacy Protection
```python
# Email/Phone Hashing
class PrivacyHasher:
    - SHA-256 with salt
    - Verification without exposure
    - GDPR-compliant data handling

# E2EE Messaging
class EncryptionService:
    - PBKDF2 key derivation
    - AES-256 encryption
    - Per-conversation salts
    - Forward secrecy
```

#### 3.4.2 Rate Limiting
```python
# Sliding Window Rate Limiting
class RateLimitMiddleware:
    - Authentication: 5/minute
    - API endpoints: 10/second
    - Messages: 20/minute
    - Redis-backed distributed limiting
    - CloudFlare IP detection
```

#### 3.4.3 Audit Logging
```python
# Comprehensive Audit Trail
class AuditLogger:
    - User actions tracking
    - Authentication events
    - Data access logging
    - IP address and user agent
    - Tamper-evident logs
```

## 4. Data Flow Design

### 4.1 User Registration Flow
```
1. User submits email
   ↓
2. Email verification sent
   ↓
3. User clicks verification link
   ↓
4. Auto-generated username created
   ↓
5. Privacy settings initialized
   ↓
6. Welcome notification sent
```

### 4.2 Item Borrowing Flow
```
1. User browses items
   ↓
2. User clicks "Borrow" on item
   ↓
3. LoanRequest created (status: pending)
   ↓
4. Lender receives notification
   ↓
5. Lender approves/rejects request
   ↓
6. If approved: Loan created (status: approved)
   ↓
7. Both users receive notifications
   ↓
8. Item marked as unavailable
```

### 4.3 Event-Driven Processing
```
1. Domain Event Published
   ↓
2. EventBus Receives Event
   ↓
3. Event Handlers Registered
   ↓
4. Async Task Created (Celery)
   ↓
5. Background Processing
   ↓
6. Side Effects Executed
   ↓
7. Audit Log Updated
```

## 5. Service Layer Design

### 5.1 Domain Services

#### 5.1.1 LoanService
```python
class LoanService:
    def create_loan_request(self, item, borrower, message):
        # Business logic for loan request creation
        # Validation: item availability, user permissions
        # Event publishing: LoanRequestCreated
        
    def approve_loan(self, loan, lender):
        # Business logic for loan approval
        # Status updates, notifications
        # Event publishing: LoanApproved
        
    def return_item(self, loan, condition_notes):
        # Business logic for item return
        # Condition tracking, reputation updates
        # Event publishing: LoanReturned
```

#### 5.1.2 BadgeService
```python
class BadgeService:
    def check_achievement_conditions(self, user, event):
        # Evaluate badge conditions based on events
        # Award badges automatically
        # Event publishing: BadgeAwarded
        
    def calculate_reputation_impact(self, badge):
        # Update user reputation based on badges
        # Multi-dimensional reputation scoring
```

#### 5.1.3 NotificationService
```python
class NotificationService:
    def send_notification(self, user, notification_type, content):
        # Create notification record
        # Send email notification (async)
        # Update in-app notification center
        
    def batch_notifications(self, notifications):
        # Efficient batch processing
        # Rate limiting compliance
```

### 5.2 Event System Design

#### 5.2.1 Domain Events
```python
@dataclass
class ItemCreated:
    item_id: int
    owner_id: int
    timestamp: datetime

@dataclass
class LoanRequestCreated:
    loan_id: int
    item_id: int
    borrower_id: int
    lender_id: int

@dataclass
class BadgeAwarded:
    user_id: int
    badge_id: int
    awarded_at: datetime
```

#### 5.2.2 Event Handlers
```python
class BadgeEventHandler:
    def handle_item_created(self, event: ItemCreated):
        # Check for "First Item" badge
        # Award badge if conditions met
        
    def handle_loan_completed(self, event: LoanCompleted):
        # Update reputation scores
        # Check for milestone badges
```

## 6. Caching Strategy

### 6.1 Multi-Layer Caching
```python
# Layer 1: Ultra Cache (Application-level)
class UltraCache:
    - Item details cache
    - User profile cache
    - Group membership cache
    - 5-minute TTL

# Layer 2: Redis Cache (Database-level)
class RedisCache:
    - Query result caching
    - Session storage
    - Rate limiting data
    - 1-hour TTL

# Layer 3: Browser Cache (Client-level)
class BrowserCache:
    - Static assets
    - API responses (GET)
    - 24-hour TTL
```

### 6.2 Cache Invalidation
```python
# Event-Driven Cache Invalidation
class CacheInvalidator:
    def on_item_updated(self, event):
        # Invalidate item cache
        # Invalidate related list caches
        
    def on_user_updated(self, event):
        # Invalidate user profile cache
        # Invalidate group membership caches
```

## 7. Performance Optimization

### 7.1 Database Optimization
- **Query Optimization**: Select_related and prefetch_related usage
- **Index Strategy**: Optimized indexes for common query patterns
- **Connection Pooling**: pgbouncer for connection management
- **Read Replicas**: Planned for scaling (Phase 3+)

### 7.2 Application Optimization
- **Lazy Loading**: Images and content loaded on demand
- **Pagination**: Efficient pagination for large datasets
- **Background Tasks**: Async processing for non-critical operations
- **Compression**: Gzip compression for API responses

### 7.3 Frontend Optimization
- **Server-Side Rendering**: Django templates for instant loads
- **Minimal JavaScript**: HTMX + Alpine.js (20KB vs 150KB React)
- **Image Optimization**: Easy-thumbnails for responsive images
- **CSS Optimization**: Tailwind CSS with purging

## 8. Security Architecture

### 8.1 Defense in Depth
```
1. Network Security
   - HTTPS/TLS encryption
   - CloudFlare DDoS protection
   - Firewall rules

2. Application Security
   - Input validation and sanitization
   - SQL injection prevention (Django ORM)
   - XSS protection (template escaping)

3. Data Security
   - E2EE for sensitive communications
   - Encrypted data at rest
   - Secure key management

4. Access Control
   - JWT-based authentication
   - Role-based permissions
   - Privacy settings enforcement
```

### 8.2 Privacy by Design
```python
# Privacy Controls Implementation
class PrivacyController:
    def get_user_profile(self, requester, target_user):
        # Check privacy settings
        # Filter sensitive information
        # Apply visibility rules
        
    def audit_data_access(self, user, resource):
        # Log all data access
        # Track permission checks
        # Monitor for privacy violations
```

## 9. Deployment Architecture

### 9.1 Container-Based Deployment
```yaml
# Docker Compose Services
services:
  web:           # Django + Gunicorn
  db:            # PostgreSQL
  redis:         # Cache + Celery broker
  celery:        # Background tasks
  nginx:         # Reverse proxy + static files
  mailcatcher:   # Email testing (dev)
```

### 9.2 Environment Configuration
```python
# Multi-Environment Support
environments/
├── development/   # Local development settings
├── staging/       # Pre-production testing
└── production/    # Production deployment
```

### 9.3 Monitoring and Logging
```python
# Comprehensive Monitoring
class MonitoringService:
    - Application performance metrics
    - Error tracking and alerting
    - Database query analysis
    - User activity analytics
    - Security event monitoring
```

## 10. Extensibility Design

### 10.1 Plugin Architecture
```python
# Plugin System for Future Extensions
class PluginManager:
    - Dynamic plugin loading
    - Hook system for extensions
    - Plugin configuration management
    - Version compatibility checking
```

### 10.2 API Versioning
```python
# Backward-Compatible API Evolution
/api/v1/    # Current stable version
/api/v2/    # Future features (planned)
/api/legacy/ # Deprecated endpoints
```

### 10.3 Mobile App Integration
```python
# Flutter App Backend Support
class MobileAPI:
    - Optimized endpoints for mobile
    - Push notification support
    - Offline sync capabilities
    - Image compression for mobile
```

## 11. Testing Strategy

### 11.1 Test Pyramid
```
E2E Tests (5%)
├── User journey testing
├── Cross-browser testing
└── Mobile responsiveness

Integration Tests (25%)
├── API endpoint testing
├── Database integration
└── Service integration

Unit Tests (70%)
├── Model testing
├── Service logic testing
├── Utility function testing
└── Security testing
```

### 11.2 Test Coverage Requirements
- **Minimum Coverage**: 85%
- **Critical Path Coverage**: 100%
- **Security Test Coverage**: 100%

## 12. Future Evolution

### 12.1 Phase 2: Mobile + Enhanced Web
- Flutter mobile app development
- HTMX + Alpine.js frontend upgrade
- Enhanced search functionality
- Offline capabilities

### 12.2 Phase 3: Real-time + Governance
- WebSocket integration (Django Channels)
- Proposal and voting systems
- Group treasury management
- Real-time notifications

### 12.3 Phase 4: Federation + AI
- Federated group architecture
- AI-powered resource matching
- Advanced analytics
- Cross-federation trading

## 13. Design Decisions Rationale

### 13.1 Technology Choices
| Decision | Rationale |
|----------|-----------|
| Django Templates vs React | 7x less energy, volunteer-friendly, 10-year sustainability |
| Flutter vs React Native | Better performance on low-end devices, smaller app size |
| PostgreSQL vs NoSQL | ACID compliance, complex queries, reliability |
| Redis vs Memcached | Data persistence, advanced features |

### 13.2 Architectural Decisions
| Decision | Rationale |
|----------|-----------|
| Event-Driven Architecture | Loose coupling, scalability, async processing |
| Clean Architecture | Maintainability, testability, clear boundaries |
| Privacy-First Design | User trust, regulatory compliance, platform values |

## 14. Conclusion

The Comuniza software design prioritizes sustainability, privacy, and maintainability while providing a robust foundation for community-based resource sharing. The architecture supports the current feature set and planned evolution toward mobile, real-time, and federated capabilities.

The design follows permacomputing principles with minimal resource usage, volunteer-friendly technology choices, and a 10+ year maintenance horizon. The event-driven architecture and clean separation of concerns ensure the system can evolve with changing requirements while maintaining stability and security.
