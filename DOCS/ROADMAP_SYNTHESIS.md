# Comuniza Roadmap Synthesis & Architecture Strategy
## Cyberpunk Communism Platform Evolution (2026)

---

## Executive Summary

**Current State**: Phase 0 alpha with functional library lending system, privacy controls, and basic reputation scoring.

**Vision**: Hierarchical federated platform enabling anarchistic resource distribution via automated AI-matching, collective governance, and recursive organizational structures.

**Critical Finding**: The three previous analyses (Big-Pickle, GLM-4.7, Grok-Code) unanimously identify **architecture decoupling and security hardening as blockers** for Phase 2+ evolution. Foundation must be perfected before complexity is added.

**Recommendation**: 
- **Immediate (Next 4 weeks)**: Architecture refactoring + security hardening
- **Short-term (Months 2-3)**: Resource model generalization
- **Medium-term (Months 4-6)**: Governance systems + federation foundation
- **Long-term (Months 7-12)**: AI automation layer + recursive federations

---

## Comparison of Three Previous Analyses

### Analysis 1: Big-Pickle (Original/First)
**Strengths**:
- Most detailed code-level audit
- Identified circular dependencies in Item.save() → BadgeService
- Caught E2EE deterministic key generation vulnerability
- Comprehensive OWASP Top 10 mapping

**Weaknesses**:
- Very code-focused, less strategic
- Minimal federation architecture details
- Limited discussion of AI/matching systems

**Unique Contributions**:
- Emphasis on test coverage (>85% target)
- Security review checklist orientation

---

### Analysis 2: GLM-4.7 (Comprehensive Roadmap)
**Strengths**:
- Most complete phase descriptions
- Detailed model designs for each phase (Resource, Proposal, Vote, Federation)
- Implementation priority matrix with business value assessment
- Clear "Week 1, Week 2" breakdown for Month 1

**Weaknesses**:
- Some redundancy with Big-Pickle
- Less emphasis on anarchistic governance principles
- Moderate discussion of AI aspects

**Unique Contributions**:
- Reputation 2.0 multi-dimensional system
- Resource distribution optimizer with priority scoring
- Crowdfunding mechanism design
- Concrete serializer specifications

---

### Analysis 3: Grok-Code (Pragmatic Architecture)
**Strengths**:
- Most visionary cyberpunk framing
- Clear risk mitigation strategies
- Excellent "zero downtime migration" approach
- Success metrics (KPIs) defined

**Weaknesses**:
- Less detailed model specifications
- Less emphasis on security
- Less comprehensive governance design

**Unique Contributions**:
- Model generalization strategy (Item → Resource)
- Transaction type expansion (Loan → Gift/Exchange/Payment/Time)
- Migration strategy preventing breaking changes
- Anarchistic design principles emphasis

---

### Key Consensus Points Across All Three
1. ✅ **Model decoupling is critical** - Move BadgeService out of Item.save()
2. ✅ **Security hardening is a blocker** - Fix E2EE, add rate limiting, implement CSP
3. ✅ **Resource model must generalize** - Support services, jobs, help, gifts beyond items
4. ✅ **API architecture needs unification** - Not just views, need REST API
5. ✅ **Governance systems prerequisite to groups** - Voting, proposals, quorum
6. ✅ **Federation requires clear data model** - Hierarchical group relationships

---

## Detailed Roadmap with Flowcharts

### Phase 0 → Phase 4 Evolution Map

```
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 0: FOUNDATION (CURRENT)               │
│                  USUARIOS ← (ARTÍCULOS) → USUARIOS              │
│                                                                │
│  ✅ Users + Authentication                                    │
│  ✅ Items (physical goods lending)                            │
│  ✅ Loans (temporary transfers)                               │
│  ✅ Groups (basic ownership)                                  │
│  ✅ Messaging (E2EE conversations)                            │
│  ✅ Reputation + Badges                                       │
│  ✅ Privacy controls                                          │
│                                                                │
│  ❌ NO: Governance, jobs, services, federations              │
│  ❌ NO: AI matching, autocracy detection                     │
│  ❌ NO: Resource distribution algorithms                      │
│  ❌ NO: Multi-group hierarchies                              │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│          PHASE 1: ARCHITECTURE FOUNDATION (IMMEDIATE)          │
│              CRITICAL BLOCKERS REMOVAL (4-6 weeks)            │
│                                                                │
│  DECOUPLING:                        SECURITY:                 │
│  ✅ Remove BadgeService from save() ✅ Fix E2EE keys         │
│  ✅ Implement DomainEventBus        ✅ Rate limiting          │
│  ✅ Async task queue (Celery)       ✅ Security headers      │
│  ✅ Transaction boundaries           ✅ OWASP compliance     │
│  ✅ REST API unification             ✅ Audit logging         │
│                                                                │
│  TESTING:                           DATA MIGRATION:           │
│  ✅ >85% code coverage              ✅ Item → Resource prep  │
│  ✅ API endpoint tests              ✅ Loan → Transaction    │
│  ✅ Security scanning               ✅ Schema versioning     │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│     PHASE 2: RESOURCE EXPANSION & REPUTATION 2.0 (BETA)      │
│           USUARIOS ← (RECURSOS) → USUARIOS → GRUPOS          │
│                        (8-10 weeks)                           │
│                                                                │
│  RESOURCE GENERALIZATION:     NEW TRANSACTION TYPES:         │
│  ✅ Resource base class       ✅ Gift (permanent)             │
│  ✅ PhysicalItem subclass     ✅ Exchange (mutual)            │
│  ✅ Service subclass          ✅ Payment (compensation)       │
│  ✅ Job/Task subclass         ✅ TimeCredit (time banking)   │
│  ✅ HelpRequest subclass      ✅ Skill verification         │
│  ✅ SkillShare subclass                                       │
│                                                                │
│  REPUTATION 2.0 SYSTEM:      SOCIAL GRAPH:                   │
│  ✅ Multi-dimensional scores ✅ Trust connections            │
│  ✅ Skill endorsements       ✅ Affinity networks            │
│  ✅ Reliability metrics      ✅ Community mapping            │
│  ✅ Contribution tracking    ✅ Friend-of-friend networks   │
│  ✅ Trust decay over time                                    │
│                                                                │
│  PHASE 2 FEATURES:                                            │
│  ✅ Job marketplace                                           │
│  ✅ Help request boards                                       │
│  ✅ Gift distribution system                                  │
│  ✅ Skill endorsement & learning                             │
│  ✅ Time banking system                                       │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│   PHASE 3: COOPERATIVE GOVERNANCE & GROUP COORDINATION        │
│          (USUARIOS + RECURSOS + COORDINACION)                │
│                    (10-12 weeks)                              │
│                                                                │
│  DEMOCRATIC GOVERNANCE:     RESOURCE DISTRIBUTION:            │
│  ✅ Proposal system         ✅ ResourcePool model            │
│  ✅ Voting mechanisms       ✅ Allocation algorithms         │
│  ✅ Multiple voting rules   ✅ Need-based distribution       │
│  ✅ Quorum requirements     ✅ Time-window optimization      │
│  ✅ Decision tracking       ✅ Fair rotation (lottery)       │
│  ✅ Veto & consensus        ✅ Contribution weighing         │
│                                                                │
│  GROUP FEATURES:            COORDINATION TOOLS:               │
│  ✅ Group treasuries        ✅ Group chats                   │
│  ✅ Crowdfunding            ✅ Event calendars               │
│  ✅ Shared budgets          ✅ Task assignments              │
│  ✅ Time-based access       ✅ Announcement boards           │
│  ✅ Role management         ✅ Document sharing              │
│  ✅ Permission matrices     ✅ Decision archives             │
│                                                                │
│  GOVERNANCE ALGORITHMS:                                       │
│  ✅ Quadratic voting option                                   │
│  ✅ Approval voting option                                    │
│  ✅ Ranked choice voting                                      │
│  ✅ Sortition (random selection) for transparency            │
│  ✅ Threshold-dependent rules                                 │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│    PHASE 4: FEDERATED SUPERGROUPS & AI AUTOMATION             │
│          (GRUPOS + COORDINACION + ADAPTABILIDAD)             │
│                    (12-16 weeks)                              │
│                                                                │
│  RECURSIVE FEDERATION:      AI MATCHING & AUTOMATION:         │
│  ✅ Federation model        ✅ Resource-person matching       │
│  ✅ Parent-child groups     ✅ Need prediction               │
│  ✅ Hierarchical voting     ✅ Optimal distribution           │
│  ✅ Delegate systems        ✅ Fraud detection               │
│  ✅ Cross-federation trade  ✅ Anomaly alerts                │
│  ✅ Recursive policies      ✅ Reputation predictions        │
│                                                                │
│  INTER-FEDERATION:          ADAPTIVE GOVERNANCE:              │
│  ✅ Federation agreements   ✅ Meta-voting systems            │
│  ✅ Resource exchange       ✅ Policy learning                │
│  ✅ Message routing         ✅ Effectiveness analytics        │
│  ✅ Dispute resolution      ✅ Organic rule evolution         │
│  ✅ Reputation federation   ✅ Community health metrics       │
│                                                                │
│  SCALABILITY:                                                 │
│  ✅ Event sourcing                                            │
│  ✅ CQRS pattern (if needed)                                  │
│  ✅ Distributed consensus                                     │
│  ✅ Horizontal scaling                                        │
│  ✅ Multi-region federation                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Critical Path: Immediate Actions (Next 4 Weeks)

### Week 1: Architecture Foundation
**Primary Goal**: Remove blocking circular dependencies

**Actionable Tasks**:
```
1. Create DomainEventBus system
   - apps/core/events.py with publish/subscribe
   - Define ItemCreated, ItemTransferred, BadgeAwarded events
   - Decouple Badge processing from Item.save()

2. Refactor Item.save()
   - Remove BadgeService import
   - Emit ItemCreated event instead
   - Handler processes async via Celery

3. Refactor Loan.save()
   - Remove BadgeService import
   - Emit appropriate transaction event
   - Handler processes async

4. Create unified REST API skeleton
   - api/v1/items/
   - api/v1/loans/
   - api/v1/users/
   - api/v1/groups/
   - DRF viewsets with proper permissions
```

**Success Criteria**:
- ✅ No circular imports on project load
- ✅ Item/Loan creation emits events properly
- ✅ Badge processing completes without blocking
- ✅ API endpoints respond within 200ms

---

### Week 2: Security Hardening
**Primary Goal**: OWASP compliance + cryptographic fixes

**Actionable Tasks**:
```
1. E2EE Key Management Fix
   - Replace UUID-based salts with crypto.PBKDF2
   - Use django-cryptography for key derivation
   - Implement SecureKeyManager class
   - Add key rotation mechanism
   - Update Conversation model

2. Implement Rate Limiting
   - Add django-ratelimit or DRF throttling
   - Configure per-endpoint limits
   - Implement sliding window algorithm
   - Add custom IP detection (CloudFlare/proxy aware)

3. Security Headers Middleware
   - Content-Security-Policy
   - X-Frame-Options: DENY
   - X-Content-Type-Options: nosniff
   - Strict-Transport-Security
   - Referrer-Policy

4. Audit Logging System
   - Create AuditLog model
   - Log all sensitive operations
   - User authentication events
   - Permission changes
   - Data access patterns

5. Input Validation Hardening
   - Add django-validators
   - Implement field-level sanitization
   - SQL injection prevention (already using ORM, but verify)
   - XSS prevention in templates
```

**Security Checklist (OWASP Top 10)**:
- ✅ A01:2021 - Broken Access Control (add @permission_required)
- ✅ A02:2021 - Cryptographic Failures (fix E2EE keys)
- ✅ A03:2021 - Injection (verify parameterized queries)
- ✅ A04:2021 - Insecure Design (add security by design)
- ✅ A05:2021 - Security Misconfiguration (env secrets)
- ✅ A07:2021 - Authentication Failures (MFA optional phase 2)
- ✅ A09:2021 - Logging & Monitoring (audit logs)

---

### Week 3-4: Testing & Phase 2 Preparation
**Primary Goal**: Test coverage + data model planning

**Actionable Tasks**:
```
1. Expand Test Suite
   - Unit tests for all models (>85% coverage)
   - API endpoint integration tests
   - Security scanning (OWASP ZAP)
   - Load testing (100 concurrent users)
   - E2E tests for critical flows

2. Phase 2 Data Model Design
   - Create abstract Resource class
   - Plan PhysicalItem, Service, Job, HelpRequest
   - Design Transaction type expansion
   - Plan SocialConnection model
   - Design ReputationProfile improvements

3. Migration Planning
   - Design zero-downtime migration scripts
   - Item → Resource data migration
   - Loan → Transaction schema evolution
   - Backward compatibility layer
   - Rollback procedures

4. API Documentation
   - OpenAPI/Swagger specs
   - Authentication flow docs
   - Error response standards
   - Rate limit documentation
```

**Success Criteria**:
- ✅ >85% test coverage
- ✅ A+ security score (OWASP ZAP)
- ✅ <200ms API response times
- ✅ Zero breaking changes to existing APIs

---

## Phase 1 Architecture Details

### DomainEventBus Implementation Pattern

```python
# apps/core/events.py - Event system foundation

from typing import Callable, List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DomainEvent:
    """Base class for all domain events"""
    aggregate_id: int
    timestamp: datetime
    event_type: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

@dataclass
class ItemCreatedEvent(DomainEvent):
    item_id: int
    owner_id: int
    item_name: str
    category: str
    
@dataclass
class ItemTransferredEvent(DomainEvent):
    item_id: int
    from_user_id: int
    to_user_id: int
    transfer_type: str  # 'loan', 'gift', 'exchange'

@dataclass
class LoanCompletedEvent(DomainEvent):
    loan_id: int
    user_id: int
    item_id: int
    days_outstanding: int
    condition_rating: int

class EventBus:
    """Pub/Sub event system for decoupled architecture"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        """Publish event to all subscribers"""
        event_type = event.__class__.__name__
        
        # Store event for audit/replay
        AuditLog.objects.create(
            event_type=event_type,
            aggregate_id=event.aggregate_id,
            event_data=event.__dict__,
            timestamp=event.timestamp
        )
        
        # Call all handlers asynchronously
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                process_event_handler.delay(handler.__name__, event)

# Global event bus instance
event_bus = EventBus()

# Handler functions (executed async via Celery)
@celery_app.task
def process_event_handler(handler_name: str, event: DomainEvent):
    """Execute event handler asynchronously"""
    handlers = {
        'award_badge_on_item_creation': handle_badge_award,
        'update_reputation_on_transfer': handle_reputation_update,
        'notify_on_loan_completion': handle_notification,
    }
    handler = handlers.get(handler_name)
    if handler:
        handler(event)

def handle_badge_award(event: ItemCreatedEvent):
    """Async handler for badge awards"""
    from apps.badges.services import BadgeService
    BadgeService.award_badges_for_item(event.item_id)

def handle_reputation_update(event: ItemTransferredEvent):
    """Async handler for reputation updates"""
    from apps.users.services import ReputationService
    ReputationService.update_on_transfer(
        event.from_user_id, 
        event.to_user_id,
        event.transfer_type
    )

def handle_notification(event: LoanCompletedEvent):
    """Async handler for notifications"""
    from apps.notifications.services import NotificationService
    NotificationService.notify_loan_completion(event.loan_id)

# Register handlers on app startup
def ready(self):
    event_bus.subscribe('ItemCreatedEvent', handle_badge_award)
    event_bus.subscribe('ItemTransferredEvent', handle_reputation_update)
    event_bus.subscribe('LoanCompletedEvent', handle_notification)
```

### Refactored Item Model

```python
# apps/items/models.py - AFTER refactoring

from django.db import models
from apps.core.events import ItemCreatedEvent, event_bus

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('book', 'Book'),
        ('tool', 'Tool'),
        ('toy', 'Toy'),
        ('electronics', 'Electronics'),
        ('furniture', 'Furniture'),
        ('other', 'Other'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    condition = models.IntegerField(default=5)  # 1-10 scale
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_available = models.BooleanField(default=True)
    
    # NO LONGER CALLS BadgeService HERE! ✅
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only emit event if this is a new item
        if is_new:
            event = ItemCreatedEvent(
                aggregate_id=self.pk,
                item_id=self.pk,
                owner_id=self.owner_id,
                item_name=self.title,
                category=self.category
            )
            event_bus.publish(event)  # ✅ Emit event instead
    
    class Meta:
        db_table = 'items_item'
        indexes = [
            models.Index(fields=['owner', 'is_available']),
            models.Index(fields=['category', 'created_at']),
        ]
```

---

## Phase 2 Resource Model Architecture

### Abstract Resource Hierarchy

```python
# apps/resources/models.py - Phase 2 implementation

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Resource(models.Model):
    """Abstract base class for all transferable resources"""
    
    RESOURCE_TYPES = [
        ('physical', 'Physical Item'),
        ('service', 'Service'),
        ('job', 'Job/Task'),
        ('help', 'Help Request'),
        ('skill', 'Skill Share'),
        ('time', 'Time Credit'),
    ]
    
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPES
    )
    
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='owned_resources'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete support
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = False
        db_table = 'resources_resource'
        indexes = [
            models.Index(fields=['owner', 'resource_type']),
            models.Index(fields=['created_at', 'resource_type']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

class PhysicalItem(Resource):
    """Tangible goods: books, tools, furniture, etc."""
    
    CONDITION_CHOICES = [
        (1, 'Broken/Non-functional'),
        (2, 'Poor'),
        (3, 'Fair'),
        (4, 'Good'),
        (5, 'Like New'),
    ]
    
    condition = models.IntegerField(
        choices=CONDITION_CHOICES,
        default=4
    )
    
    estimated_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    category = models.CharField(
        max_length=50,
        choices=[
            ('book', 'Book'),
            ('tool', 'Tool'),
            ('toy', 'Toy'),
            ('electronics', 'Electronics'),
            ('furniture', 'Furniture'),
            ('clothing', 'Clothing'),
            ('other', 'Other'),
        ]
    )
    
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., '30x20x10 cm'"
    )
    
    weight_kg = models.FloatField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'resources_physical_item'

class Service(Resource):
    """Time-based services: plumbing, tutoring, gardening, etc."""
    
    DURATION_UNIT = [
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('week', 'Week'),
        ('project', 'Project'),
    ]
    
    duration_unit = models.CharField(
        max_length=20,
        choices=DURATION_UNIT,
        default='hour'
    )
    
    estimated_hours = models.FloatField(
        default=1.0
    )
    
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional: if not free service"
    )
    
    skills_required = models.ManyToManyField(
        'users.Skill',
        blank=True,
        related_name='services_needing'
    )
    
    availability_start = models.DateTimeField()
    availability_end = models.DateTimeField()
    
    max_concurrent_users = models.IntegerField(
        default=1,
        help_text="How many people can use simultaneously"
    )
    
    class Meta:
        db_table = 'resources_service'

class Job(Resource):
    """Tasks or jobs to be completed"""
    
    COMPLEXITY = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    complexity = models.CharField(
        max_length=20,
        choices=COMPLEXITY
    )
    
    estimated_hours = models.FloatField()
    
    compensation_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free/Voluntary'),
            ('credit', 'Time Credit'),
            ('money', 'Money'),
            ('goods', 'Goods Exchange'),
        ]
    )
    
    compensation_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    deadline = models.DateTimeField()
    
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Where work happens"
    )
    
    skills_needed = models.ManyToManyField(
        'users.Skill',
        blank=True,
        related_name='jobs_needing'
    )
    
    class Meta:
        db_table = 'resources_job'

class HelpRequest(Resource):
    """Requests for assistance from community"""
    
    URGENCY = [
        ('low', 'Can wait'),
        ('normal', 'Needed soon'),
        ('urgent', 'Needed ASAP'),
        ('emergency', 'Emergency'),
    ]
    
    urgency = models.CharField(
        max_length=20,
        choices=URGENCY,
        default='normal'
    )
    
    category = models.CharField(
        max_length=100,
        help_text="e.g., Moving, Childcare, Medical support"
    )
    
    needed_by = models.DateTimeField()
    
    estimated_effort_hours = models.FloatField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'resources_help_request'

class Skill(models.Model):
    """User skills/expertise for matching"""
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'resources_skill'
    
    def __str__(self):
        return self.name

class SkillEndorsement(models.Model):
    """User endorsement of another user's skill"""
    
    endorser = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='skill_endorsements_given'
    )
    
    endorsee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='skill_endorsements_received'
    )
    
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'resources_skill_endorsement'
        unique_together = ('endorser', 'endorsee', 'skill')
```

### Transaction Type Expansion

```python
# apps/transactions/models.py - Unified transaction handling

class Transaction(models.Model):
    """Unified transaction model replacing Loan"""
    
    TRANSACTION_TYPES = [
        ('loan', 'Temporary Loan'),
        ('gift', 'Permanent Gift'),
        ('exchange', 'Mutual Exchange'),
        ('payment', 'Service Payment'),
        ('time_credit', 'Time Credit'),
        ('purchase', 'Community Store Purchase'),
    ]
    
    STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('returned', 'Returned'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    
    from_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='transactions_sent'
    )
    
    to_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='transactions_received'
    )
    
    resource = models.ForeignKey(
        'resources.Resource',
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='pending'
    )
    
    # Loan-specific fields
    due_date = models.DateTimeField(null=True, blank=True)
    return_condition = models.IntegerField(
        null=True,
        blank=True,
        help_text="Condition rating on return (1-5)"
    )
    
    # Exchange-specific
    exchange_resource = models.ForeignKey(
        'resources.Resource',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exchanges_for'
    )
    
    # Payment-specific
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    currency = models.CharField(
        max_length=3,
        default='USD'
    )
    
    # Time credit-specific
    time_credits = models.FloatField(
        null=True,
        blank=True,
        help_text="Hours of time credits"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions_transaction'
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
```

---

## Phase 3: Governance Models

### Proposal & Voting System

```python
# apps/governance/models.py - Democratic decision-making

class Proposal(models.Model):
    """Proposals for group decision-making"""
    
    PROPOSAL_TYPES = [
        ('policy', 'Policy Change'),
        ('resource', 'Resource Allocation'),
        ('budget', 'Budget Decision'),
        ('governance', 'Governance Change'),
        ('membership', 'Membership Decision'),
        ('removal', 'Member Removal'),
    ]
    
    VOTING_METHODS = [
        ('simple_majority', 'Simple Majority (50%+1)'),
        ('supermajority', 'Supermajority (66%+)'),
        ('consensus', 'Consensus (85%+)'),
        ('quadratic', 'Quadratic Voting'),
        ('approval', 'Approval Voting'),
        ('ranked_choice', 'Ranked Choice'),
        ('sortition', 'Random Selection'),
    ]
    
    STATUS = [
        ('draft', 'Draft'),
        ('open', 'Open for Voting'),
        ('closed', 'Closed'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('implemented', 'Implemented'),
    ]
    
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    
    proposer = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='proposals_created'
    )
    
    proposal_type = models.CharField(
        max_length=20,
        choices=PROPOSAL_TYPES
    )
    
    voting_method = models.CharField(
        max_length=20,
        choices=VOTING_METHODS,
        default='simple_majority'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    rationale = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='draft'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    voting_starts = models.DateTimeField()
    voting_ends = models.DateTimeField()
    implementation_deadline = models.DateTimeField(null=True, blank=True)
    
    # Quorum requirements
    minimum_voters = models.IntegerField(
        help_text="Minimum number of votes required"
    )
    
    quorum_percentage = models.IntegerField(
        default=50,
        help_text="Percentage of members that must vote"
    )
    
    # Veto powers
    allows_veto = models.BooleanField(default=False)
    veto_count = models.IntegerField(default=0)
    max_vetoes = models.IntegerField(default=3)
    
    passed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'governance_proposal'
        ordering = ['-created_at']
    
    def is_passed(self) -> bool:
        """Determine if proposal passed based on votes"""
        total_votes = self.votes.count()
        
        if total_votes < self.minimum_voters:
            return False
        
        total_eligible = self.group.members.count()
        if total_votes < (total_eligible * self.quorum_percentage / 100):
            return False
        
        votes_for = self.votes.filter(choice='for').count()
        votes_against = self.votes.filter(choice='against').count()
        
        if self.voting_method == 'simple_majority':
            return votes_for > votes_against
        elif self.voting_method == 'supermajority':
            return votes_for >= (total_votes * 0.66)
        elif self.voting_method == 'consensus':
            return votes_for >= (total_votes * 0.85)
        
        return False

class Vote(models.Model):
    """Individual votes on proposals"""
    
    VOTE_CHOICES = [
        ('for', 'For'),
        ('against', 'Against'),
        ('abstain', 'Abstain'),
    ]
    
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    
    voter = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='votes_cast'
    )
    
    choice = models.CharField(
        max_length=10,
        choices=VOTE_CHOICES
    )
    
    # For quadratic voting
    power = models.FloatField(
        default=1.0,
        help_text="Voting power (for quadratic voting)"
    )
    
    rationale = models.TextField(
        blank=True,
        help_text="Why they voted this way"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'governance_vote'
        unique_together = ('proposal', 'voter')
```

### Resource Distribution System

```python
# apps/governance/distribution.py - Fair allocation algorithms

class DistributionOptimizer:
    """Calculates fair resource distribution across group members"""
    
    def calculate_distribution(self, resource, group, algorithm='need_based'):
        """
        Distribute resource to group members fairly
        
        Algorithms:
        - need_based: Priority to those with greatest need
        - contribution: Based on contribution history
        - random_lottery: Fair random selection
        - time_rotation: Round-robin fair rotation
        - hybrid: Weighted combination
        """
        
        if algorithm == 'need_based':
            return self._distribute_by_need(resource, group)
        elif algorithm == 'contribution':
            return self._distribute_by_contribution(resource, group)
        elif algorithm == 'lottery':
            return self._distribute_by_lottery(resource, group)
        elif algorithm == 'rotation':
            return self._distribute_by_rotation(resource, group)
        else:
            return self._hybrid_distribution(resource, group)
    
    def _distribute_by_need(self, resource, group):
        """Distribute to those with greatest documented need"""
        members = group.members.all()
        
        scores = {}
        for member in members:
            # Calculate need score (0-100)
            score = 0
            
            # Factor 1: Active help requests (40 points)
            help_requests = HelpRequest.objects.filter(
                owner=member,
                is_archived=False
            ).count()
            score += min(40, help_requests * 10)
            
            # Factor 2: Resource scarcity (30 points)
            resources_owned = Resource.objects.filter(
                owner=member,
                is_archived=False
            ).count()
            score += max(0, 30 - (resources_owned * 5))
            
            # Factor 3: Recent contributions (20 points)
            # Users who contribute more get slightly better access
            contributions = Transaction.objects.filter(
                from_user=member,
                created_at__gte=datetime.now() - timedelta(days=30)
            ).count()
            score += min(20, contributions * 2)
            
            # Factor 4: Accessibility priority (10 points)
            # Medical conditions, disabilities, special needs
            if hasattr(member, 'accessibility_needs'):
                score += 10
            
            scores[member.id] = score
        
        # Sort by need score
        sorted_members = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {mid: rank for rank, (mid, _) in enumerate(sorted_members)}
    
    def _distribute_by_lottery(self, resource, group):
        """Fair random lottery selection"""
        members = list(group.members.all())
        random.shuffle(members)
        return {m.id: i for i, m in enumerate(members)}
    
    def _distribute_by_rotation(self, resource, group):
        """Round-robin based on last access time"""
        members = group.members.all().order_by(
            'last_resource_access'
        )
        return {m.id: i for i, m in enumerate(members)}

class ResourcePool(models.Model):
    """Shared resource pool for group allocation"""
    
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='resource_pools'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Distribution method
    allocation_algorithm = models.CharField(
        max_length=20,
        choices=[
            ('need_based', 'Need-Based'),
            ('contribution', 'Contribution'),
            ('lottery', 'Random Lottery'),
            ('rotation', 'Fair Rotation'),
            ('hybrid', 'Hybrid'),
        ],
        default='need_based'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'governance_resource_pool'
    
    def get_next_recipient(self, resource_type=None):
        """Get next eligible member for resource"""
        optimizer = DistributionOptimizer()
        distribution = optimizer.calculate_distribution(
            resource_type,
            self.group,
            self.allocation_algorithm
        )
        return distribution
```

---

## Phase 4: Federation Architecture

### Recursive Group Hierarchy

```python
# apps/federations/models.py - Hierarchical organization

class Federation(models.Model):
    """
    Federated group: collection of groups organized hierarchically
    Enables recursive structure for scaling
    
    Examples:
    - City-level federation (contains neighborhood groups)
    - Sector federation (contains worker coops)
    - Skill federation (contains skill-sharing groups)
    """
    
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    
    # Hierarchy
    parent_federation = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_federations'
    )
    
    # Governance at federation level
    governance_type = models.CharField(
        max_length=20,
        choices=[
            ('consensus', 'Consensus'),
            ('voting', 'Democratic Voting'),
            ('council', 'Council Delegation'),
            ('hybrid', 'Hybrid'),
        ]
    )
    
    # Federation properties
    scope = models.CharField(
        max_length=20,
        choices=[
            ('geographic', 'Geographic Region'),
            ('sectoral', 'Sector/Industry'),
            ('skill', 'Skill-based'),
            ('ideological', 'Values-based'),
            ('custom', 'Custom'),
        ]
    )
    
    scope_description = models.CharField(
        max_length=255,
        help_text="e.g., 'Barcelona Metropolitan', 'Food Systems', 'Data Privacy'"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'federations_federation'
    
    def get_all_groups(self):
        """Get all groups in this federation recursively"""
        groups = self.member_groups.all()
        for sub_fed in self.sub_federations.all():
            groups = groups | sub_fed.get_all_groups()
        return groups
    
    def get_all_members(self):
        """Get all users across all member groups"""
        from django.contrib.auth.models import User
        users = set()
        for group in self.get_all_groups():
            users.update(group.members.all())
        return users

class FederationMembership(models.Model):
    """Group membership in federation"""
    
    federation = models.ForeignKey(
        Federation,
        on_delete=models.CASCADE,
        related_name='member_groups'
    )
    
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='federations'
    )
    
    # Governance role
    role = models.CharField(
        max_length=20,
        choices=[
            ('member', 'Member Group'),
            ('council', 'Council Delegate'),
            ('admin', 'Federation Admin'),
        ],
        default='member'
    )
    
    # Contribution level
    contribution_weight = models.FloatField(
        default=1.0,
        help_text="Voting weight in federation decisions"
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'federations_membership'
        unique_together = ('federation', 'group')

class FederationProposal(models.Model):
    """Proposals at federation level affecting multiple groups"""
    
    federation = models.ForeignKey(
        Federation,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Which groups does this affect?
    affected_groups = models.ManyToManyField(
        'groups.Group',
        related_name='federation_proposals_affecting'
    )
    
    proposer_group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        related_name='federation_proposals_created'
    )
    
    # Voting
    votes_required = models.IntegerField()
    votes_received = models.IntegerField(default=0)
    votes_for = models.IntegerField(default=0)
    votes_against = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    voting_ends = models.DateTimeField()
    
    class Meta:
        db_table = 'federations_proposal'
```

---

## Security Architecture Changes

### E2EE Key Management Fix

```python
# apps/messaging/security.py - Cryptographic key management

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import secrets

class SecureKeyManager:
    """Manages E2EE conversation keys securely"""
    
    ITERATIONS = 480000  # OWASP recommended for PBKDF2
    KEY_LENGTH = 32  # 256-bit keys
    
    @staticmethod
    def generate_salt():
        """
        Generate cryptographically secure random salt
        ✅ FIXED: No longer deterministic
        """
        return secrets.token_bytes(16)
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password + salt
        Using PBKDF2 with OWASP-recommended parameters
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=SecureKeyManager.KEY_LENGTH,
            salt=salt,
            iterations=SecureKeyManager.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    @staticmethod
    def create_conversation_key(
        conversation_id: int,
        user_password: str
    ) -> tuple[bytes, bytes]:
        """
        Create unique conversation key for each user
        
        Returns: (key, salt)
        Both stored securely, never hardcoded
        """
        salt = SecureKeyManager.generate_salt()
        key = SecureKeyManager.derive_key(user_password, salt)
        return key, salt
    
    @staticmethod
    def rotate_conversation_keys(conversation_id: int):
        """
        Periodic key rotation (recommended every 90 days)
        Implements forward secrecy
        """
        from apps.messaging.models import Conversation, ConversationKey
        
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Archive old keys
        ConversationKey.objects.filter(
            conversation=conversation,
            is_active=True
        ).update(
            is_active=False,
            rotated_at=datetime.utcnow()
        )
        
        # Create new keys for all participants
        for participant in conversation.participants.all():
            key, salt = SecureKeyManager.create_conversation_key(
                conversation_id,
                participant.password_hash
            )
            
            ConversationKey.objects.create(
                conversation=conversation,
                user=participant,
                key_hash=hash(key),
                salt=salt,
                is_active=True,
                created_at=datetime.utcnow()
            )

class Conversation(models.Model):
    """E2EE conversation model"""
    
    participants = models.ManyToManyField('users.User')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Create keys for each participant on first save
        if not self.conversationkey_set.exists():
            for user in self.participants.all():
                key, salt = SecureKeyManager.create_conversation_key(
                    self.id,
                    user.password_hash
                )
                ConversationKey.objects.create(
                    conversation=self,
                    user=user,
                    key_hash=hash(key),
                    salt=salt,
                    is_active=True
                )
```

---

## Success Metrics & KPIs

### Technical Metrics
| Metric | Phase 1 Target | Phase 2 Target | Phase 4 Target |
|--------|---------------|---------------|---------------|
| API Response Time | <200ms p99 | <250ms p99 | <500ms p99 |
| Test Coverage | >85% | >90% | >95% |
| Security Score | A (OWASP) | A+ | A++ |
| Uptime | 99.5% | 99.9% | 99.99% |
| Database Query Time | <50ms avg | <75ms avg | <100ms avg |
| Cache Hit Rate | 70% | 80% | 85% |

### Business Metrics
| Metric | Current | Phase 2 | Phase 4 |
|--------|---------|---------|---------|
| Monthly Active Users | ~100 | 500+ | 5,000+ |
| Total Resources | 1,000+ | 10,000+ | 100,000+ |
| Transactions/Month | 200 | 2,000 | 20,000 |
| Groups Created | 10 | 100 | 500+ |
| Federation Count | 0 | 0 | 10+ |
| AI Match Success Rate | — | 60% | 85% |

---

## Risk Assessment & Mitigation

### High-Risk Areas

**Risk 1: Breaking Existing APIs During Refactor**
- **Probability**: Medium | **Impact**: High
- **Mitigation**:
  - Maintain backward-compatible endpoints during Phase 1
  - Version all APIs (v1/ vs v2/)
  - Use feature flags for new functionality
  - 100% regression test coverage

**Risk 2: Data Migration Losses (Item→Resource)**
- **Probability**: Low | **Impact**: Critical
- **Mitigation**:
  - Develop and test migrations in staging
  - Implement dual-write period
  - Keep old tables for 90 days
  - Full backup before execution

**Risk 3: Security Vulnerability in E2EE Fix**
- **Probability**: Low | **Impact**: Critical
- **Mitigation**:
  - External security audit before production
  - Cryptographic peer review
  - Gradual rollout (1% of users)
  - Immediate rollback plan

**Risk 4: Federation Complexity Explosion**
- **Probability**: Medium | **Impact**: Medium
- **Mitigation**:
  - Start with 2-level hierarchy only
  - Extensive simulations before rollout
  - Gradual feature enablement
  - Clear governance boundaries

---

## Recommended Tech Stack Additions

### Current Stack (Phase 0)
```
Backend: Django 4.2 + DRF
Database: MariaDB/MySQL
Cache: Redis
Task Queue: Celery
Frontend: Django Templates
Security: django-cors, HTTPS
Monitoring: Basic logging
```

### Phase 1 Additions
```
✅ django-cryptography (E2EE keys)
✅ django-ratelimit (rate limiting)
✅ django-extensions (management commands)
✅ pytest + pytest-cov (testing)
✅ OWASP ZAP (security scanning)
✅ Sentry (error tracking)
```

### Phase 2-3 Additions
```
✅ channels + daphne (WebSockets for notifications)
✅ django-celery-beat (scheduled tasks)
✅ elasticsearch (full-text search for resources)
✅ graphene-django (GraphQL API option)
✅ psycopg2 (PostgreSQL driver if scaling)
```

### Phase 4 Additions
```
✅ machine-learning: scikit-learn + TensorFlow (AI matching)
✅ plotly/dash (analytics dashboards)
✅ networkx (graph analysis for federations)
✅ timescaledb (time-series data for voting patterns)
✅ kafka (distributed event streaming)
```

---

## Implementation Checklist: Next 30 Days

### Week 1: Kickoff & Foundation
- [ ] Create `/apps/core/events.py` with DomainEventBus
- [ ] Define ItemCreatedEvent, ItemTransferredEvent, etc.
- [ ] Refactor `Item.save()` to emit events instead of calling BadgeService
- [ ] Setup Celery task for async badge processing
- [ ] Create first integration test for event flow

### Week 2: Security Hardening
- [ ] Implement SecureKeyManager with PBKDF2
- [ ] Add RateLimitMiddleware to Django settings
- [ ] Add SecurityHeadersMiddleware with CSP/HSTS/XFO
- [ ] Create AuditLog model and middleware
- [ ] Run OWASP ZAP scan against staging
- [ ] Document all security fixes

### Week 3: API & Testing
- [ ] Create DRF viewsets for all models
- [ ] Setup OpenAPI/Swagger documentation
- [ ] Write unit tests (target >85% coverage)
- [ ] Write API integration tests
- [ ] Performance load testing (100 concurrent users)

### Week 4: Documentation & Planning
- [ ] Document architecture changes in README
- [ ] Create API migration guide for clients
- [ ] Plan Phase 2 data models in detail
- [ ] Create migration scripts (Item→Resource)
- [ ] Setup staging deployment
- [ ] Create rollback procedures

---

## Anarchistic Principles in Implementation

Your vision is explicitly anti-authoritarian. Ensure architectural decisions reflect this:

1. **No Central Authority**: Implement at-federation level, not platform level
2. **Consensus by Default**: Governance should default to consensus/supermajority, not majority
3. **Transparent Decision-Making**: All proposals and votes public in group/federation
4. **Right to Exit**: Groups can leave federations easily (with 2-week notice)
5. **Contribution-Weighted Access**: Access to resources weighted by contribution, not wealth
6. **Skill-Based Matching**: Match based on actual skills, not credentials
7. **Privacy as Default**: All data encrypted by default, no surveillance
8. **Forking-Friendly**: Easy for groups to fork if consensus breaks down

---

## Conclusion

Your platform has solid alpha foundations. The critical path forward involves:

1. **Month 1**: Decouple architecture, harden security (Foundation)
2. **Month 2-3**: Generalize Resource model, expand transaction types (Resource Exchange)
3. **Month 4-6**: Implement governance systems, group treasuries (Cooperatives)
4. **Month 7-12**: Build federations, AI matching, recursive structures (Cyberpunk Communism)

The three analyses unanimously agree: **fix the foundation before adding complexity**. Architecture debt now compounds exponentially in later phases.

Your vision of "cyberpunk communism for the 21st century" is technically achievable, but only with disciplined, security-first engineering.

The revolution begins with clean code.

---

**Next Action**: Schedule Phase 1 implementation kickoff. Assign: 1 backend dev (full-time), 1 security engineer (2 days/week), 1 QA engineer (part-time).

Estimated Phase 1 cost: 4-6 weeks of focused development.
Estimated Phase 4 completion: 9-12 months from Phase 1 start.
