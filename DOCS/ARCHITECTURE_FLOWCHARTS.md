# COMUNIZA ARCHITECTURE FLOWCHARTS

## Visual Evolution from Phase 0 → Phase 4

---

## FLOWCHART 1: PHASE 0-A CRITICAL REFACTORING

### (Weeks 1-4: Architecture Decoupling & Security)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 0: CURRENT STATE (BROKEN)            │
└─────────────────────────────────────────────────────────────────┘

                       USER ACTION
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │    Django View / REST API Endpoint   │
        └────────────────┬─────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────────┐
        │    Form Validation / Serialization   │
        └────────────────┬─────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────────┐
        │       Model.save() [ITEM/LOAN]       │ ◄─── REQUEST THREAD BLOCKS HERE
        └────────┬─────────────────────────────┘
                 │
        ┌────────┴──────────────────────────────────┐
        │                                           │
        ▼                                           ▼
    ❌ BadgeService.import()             ✅ Database.save()
    (Circular Dependency)                (Actually works)
        │                                           │
        ▼                                           │
    RuntimeError: Circular Import                   │
    (Blocks execution)                              │
                                                    │
        ┌───────────────────────────────────────────┘
        │
        ▼
    ❌ FAILURE: Request hangs or errors
    ❌ No cache invalidation
    ❌ No async processing
    ❌ No event audit trail
    ❌ Blocks scaling

═════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│          PHASE 0-A: REFACTORED STATE (FIXED) ✅               │
└─────────────────────────────────────────────────────────────────┘

                       USER ACTION
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │    Django View / REST API Endpoint   │
        └────────────────┬─────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────────┐
        │    Form Validation / Serialization   │
        └────────────────┬─────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────────┐
        │       Model.save() [ITEM/LOAN]       │ ◄─── NO BLOCKING
        │       (Pure business logic only)     │
        └────────┬─────────────────────────────┘
                 │
        ┌────────┴────────────┬──────────────────┐
        │                     │                  │
        ▼                     ▼                  ▼
    Save to DB          Emit Event          Update Cache
        │                (IF NEW)              │
        │                   │                  │
        ▼                   ▼                  ▼
    ✅ Transaction   DomainEventBus      Cache.invalidate()
       boundary         .publish()            │
                           │                  │
                           ▼                  │
                    ┌──────────────────┐      │
                    │ EventStore.save()│      │
                    │ (Audit trail)    │      │
                    └──────────────────┘      │
                           │                  │
        ┌──────────────────┘                  │
        │                                     │
        ▼                                     │
    Message Queue                             │
    (Celery/Redis)                            │
        │                                     │
        ▼                                     ▼
    async_task: process_event         ✅ RESPONSE (200ms)
        │                             │
        ▼                             │
    ┌──────────────────────────┐      │
    │ BadgeService.award()     │      │
    │ (No import, no block)    │      │
    └──────────────────────────┘      │
        │                             │
        ▼                             │
    UpdateReputation()                │
    SendNotifications()               │
    AnalyticsLog()                    │
        │                             │
        └─────────────────────────────┘
                       │
                       ▼
            USER RECEIVES RESPONSE
            (Request completes fast)

    ✅ No circular imports
    ✅ No blocking
    ✅ Async processing
    ✅ Event audit trail
    ✅ Scalable architecture
```

---

## FLOWCHART 2: DATA FLOW - ITEM CREATION THROUGH FEDERATION

```
┌────────────────────────────────────────────────────────────────────┐
│                   ITEM/RESOURCE CREATION FLOW                     │
│                   (Phase 0-A through Phase 4)                     │
└────────────────────────────────────────────────────────────────────┘

    USER CREATES ITEM/RESOURCE
            │
            ▼
    ┌─────────────────────────────┐
    │  POST /api/v1/items/        │
    │  POST /api/v1/resources/    │
    └──────────┬──────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────┐
    │  Serializer Validation                  │
    │  ├─ Title, description required         │
    │  ├─ Category in allowed list            │
    │  └─ User authenticated & authorized     │
    └──────────┬──────────────────────────────┘
               │
        ┌──────┴──────────────────────────────┐
        │                                     │
    ✅ PASS                                ❌ FAIL
        │                                     │
        ▼                                     ▼
    Create Item                     Return 400/403
    in Database                     with error details
        │
        ▼
    ┌─────────────────────────────────────────┐
    │  EMIT: ItemCreatedEvent                 │
    │  ├─ item_id                             │
    │  ├─ owner_id                            │
    │  ├─ resource_type                       │
    │  └─ timestamp                           │
    └──────────┬──────────────────────────────┘
               │
               ▼
    ┌────────────────────────────────────────────┐
    │  EventBus.publish(ItemCreatedEvent)        │
    │  Store in DomainEventStore (audit trail)   │
    └──────────┬─────────────────────────────────┘
               │
        ┌──────┴────────────────────────────────────┐
        │                                           │
        ▼                                           ▼
    Async Task Scheduling                  Cache Invalidation
    (Add to message queue)                 ├─ user:item:list
                                           ├─ group:resources
    ┌─────────────────────────────┐       └─ feed:recent
    │ Badge Service Handler       │
    │ (async task)                │
    └──────────┬──────────────────┘
               │
               ▼
    Check if user qualifies for:
    ├─ First Item Badge
    ├─ Contributor Badge
    └─ Milestone Badge (10, 50, 100 items)
               │
               ▼
    Award badges (if earned)
    Update UserReputation
    Send notification
               │
    ┌──────────┴────────────────────────┐
    │                                   │
    ▼ (Phase 2+)                        ▼
 Reputation                        Matching Service
 Updates:                          (Phase 2+ only)
 ├─ +5 points for contributing          │
 ├─ +2 points per month active    Search for matching
 └─ Skill endorsements            help requests or jobs
                                     │
                                     ▼
                              Notify potential
                              borrowers/exchanges
                              via notifications
                                   │
    ┌──────────────────────────────┘
    │
    ▼ (Phase 3+)
 Group Impact
 (If group-owned)
 ├─ Add to ResourcePool
 ├─ Update group metrics
 └─ Trigger distribution
    algorithm if needed
    │
    ▼ (Phase 4+)
Federation-Level
├─ Federate availability
│  (share across groups)
├─ AI Matching Engine
│  analyzes cross-federation
│  demand patterns
└─ Auto-suggest optimal
   distribution if surplus


    ┌──────────────────────────────────────────────┐
    │        RESPONSE TO USER (200ms later)        │
    │  {                                           │
    │    "id": 12345,                             │
    │    "title": "Django Book",                  │
    │    "resource_type": "physical",             │
    │    "status": "available",                   │
    │    "badges_awarded": ["contributor"]       │
    │  }                                          │
    └──────────────────────────────────────────────┘
```

---

## FLOWCHART 3: SECURITY ARCHITECTURE EVOLUTION

```
┌────────────────────────────────────────────────────────────────┐
│              E2EE & SECURITY LAYER EVOLUTION                  │
└────────────────────────────────────────────────────────────────┘

PHASE 0: BROKEN E2EE (CRITICAL VULNERABILITY)
═══════════════════════════════════════════════

User A ──────────────► [Message] ◄────────── User B
                           │
                           ▼
                    ❌ generate_salt()
                    returns str(uuid.uuid4())
                           │
                    ❌ DETERMINISTIC!
                    Same salt on restart
                           │
                           ▼
                    ❌ Weak key derivation
                    Simple SHA256 hash
                           │
                           ▼
                    Store in DB
                           │
                    ❌ VULNERABLE TO:
                    ├─ Rainbow table attacks
                    ├─ Container restart = same key
                    ├─ GPU brute force
                    └─ Replay attacks


PHASE 0-A: FIXED E2EE (SECURE) ✅
═════════════════════════════════

User A ──────────────► [Message] ◄────────── User B
                           │
                           ▼
                    Conversation Created
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    User A                User B         EventStore
    SecureKey             SecureKey       (Audit)
        │                  │               │
        ▼                  ▼               ▼
    ✅ PBKDF2             ✅ PBKDF2      Log Event
    Iterations:           Iterations:
    480,000               480,000
        │                  │
        ▼                  ▼
    ✅ Random Salt        ✅ Random Salt
    (crypto.urandom)      (crypto.urandom)
        │                  │
        ▼                  ▼
    ✅ Key Derivation     ✅ Key Derivation
    256-bit keys          256-bit keys
        │                  │
        ▼                  ▼
    Fernet Encryption     Fernet Encryption
    with 128-bit IV       with 128-bit IV
        │                  │
        ▼                  ▼
    Encrypted Message ←──────┘
    Stored in DB
        │
        ▼
    ✅ SAFE AGAINST:
    ├─ Rainbow tables (random salt)
    ├─ GPU brute force (PBKDF2 iterations)
    ├─ Container restart (secure RNG)
    ├─ Replay attacks (IV per message)
    └─ Forward secrecy (key rotation every 90 days)


RATE LIMITING MIDDLEWARE
═════════════════════════

Request ──────────────────────────► DjangoRateLimit
                                          │
                              ┌───────────┼───────────┐
                              │           │           │
                         Auth        Search      Upload
                         Endpoints   Endpoints   Endpoints
                              │           │           │
                              ▼           ▼           ▼
                         5/min       30/min       10/min
                         per IP      per user     per IP
                              │           │           │
                              └─────┬─────┴─────┬─────┘
                                    │           │
                            ✅ PASS            ❌ EXCEEDED
                                    │           │
                                    ▼           ▼
                            Continue      429 Too Many
                            Processing    Requests
                                              │
                                              ▼
                                        (Wait & retry)


SECURITY HEADERS MIDDLEWARE
════════════════════════════

Response Headers Added:
├─ Strict-Transport-Security: max-age=31536000 (HSTS)
│  └─ Forces HTTPS only
├─ X-Content-Type-Options: nosniff
│  └─ Prevents MIME type sniffing
├─ X-Frame-Options: DENY
│  └─ Prevents clickjacking
├─ Content-Security-Policy: default-src 'self'
│  └─ Restricts external script loading
└─ Referrer-Policy: strict-origin-when-cross-origin
   └─ Limits referrer leaking

Result: A+ Security Grade (OWASP ZAP)
```

---

## FLOWCHART 4: PHASE 1 RESOURCE GENERALIZATION

```
┌────────────────────────────────────────────────────────────────┐
│           PHASE 1: RESOURCE MODEL HIERARCHY                    │
│        (Item → Resource + Subtypes, Zero Downtime)            │
└────────────────────────────────────────────────────────────────┘

BEFORE (Phase 0):
═════════════════
        Item Model
            │
    ┌───────┼───────┐
    │       │       │
   Book   Tool    Toy
  (hardcoded)

LIMITATION: Only physical goods
           No jobs, services, help, skills


AFTER (Phase 1):
════════════════
              Resource (Abstract Base)
              ├─ id, owner, title, description
              ├─ created_at, updated_at
              ├─ status, visibility, archived_at
              └─ resource_type (polymorphic)
                       │
        ┌──────────┬───┼────┬──────────┬─────────┐
        │          │   │    │          │         │
        ▼          ▼   ▼    ▼          ▼         ▼
    Physical    Service  Job     HelpRequest  Skill  Time
     Item                        (Request)    Share  Credit
        │          │      │          │         │      │
    ┌───┴┐      ┌──┴───┐ ┌─┴──┐    ┌─┴──┐   ┌──┴──┐ ┌─┴───┐
    │    │      │      │ │    │    │    │   │     │ │     │
  Book Tool  Tutor Hours  Task Comp. Moving Help   Skill Time
  Toy  etc   Repair      Deadline    Help  Endorsements Balance


DATABASE MIGRATION (Zero Downtime):
═════════════════════════════════════

Phase 0 Database State:
┌──────────────────┐
│  items_item      │
├──────────────────┤
│ id (PK)          │
│ owner_id (FK)    │
│ title            │
│ description      │
│ category         │
│ created_at       │
│ is_borrowed      │
│ borrowed_by_id   │
└──────────────────┘


PARALLEL OPERATION (90 days):
        Phase 0 Code               Phase 1 Code
        (Old reads/writes)         (New reads/writes)
              │                          │
              ▼                          ▼
        ┌──────────────┐         ┌──────────────┐
        │ items_item   │◄───────►│ resources_   │
        │ (active)     │  Dual   │ resource     │
        │              │ Write   │ (active)     │
        └──────────────┘ Layer   │              │
                                 │ + resource_  │
                                 │ physical_    │
                                 │ item         │
                                 │ (new)        │
                                 └──────────────┘

During Migration:
├─ Write new items to BOTH tables
├─ Read from primary (items_item)
├─ Keep old Item model intact
├─ Test thoroughly in staging
└─ Run data consistency checks


CUTOVER (Day 91):
═════════════════
Step 1: Final sync of any stragglers
        items_item → resources_resource

Step 2: Switch code to use Resource model
        from apps.items.models import Item
        ↓
        from apps.resources.models import Resource, PhysicalItem

Step 3: Update views, serializers, queries
        Item.objects.all()
        ↓
        Resource.objects.filter(resource_type='physical')

Step 4: Archive old items_item table
        (keep for 180 days as backup)

Step 5: Deploy new code
        Zero downtime!


API EVOLUTION:
═════════════

OLD API (v0):
GET /api/items/
GET /api/items/{id}/
POST /api/items/
PUT /api/items/{id}/

NEW API (v1):
GET /api/v1/resources/
GET /api/v1/resources/{id}/
POST /api/v1/resources/  (auto-detects type)
PUT /api/v1/resources/{id}/
GET /api/v1/resources?type=physical
GET /api/v1/resources?type=service
GET /api/v1/resources?type=job

BACKWARD COMPAT:
GET /api/items/  (still works, redirects to /api/v1/resources?type=physical)
```

---

## FLOWCHART 5: PHASE 2 TRANSACTION TYPES

```
┌────────────────────────────────────────────────────────────────┐
│        PHASE 2: TRANSACTION TYPE EXPANSION                     │
│    Loan → Gift/Exchange/Payment/TimeCredit (Unified)          │
└────────────────────────────────────────────────────────────────┘

BEFORE (Phase 0): Single Transaction Type
═════════════════════════════════════════════

User A ─────────────────► Book ◄────────── User B
       Loan Agreement
       (ONLY option)
            │
    ┌───────┼────────┐
    │       │        │
    ▼       ▼        ▼
 Borrowed  Due Date  Condition
 Status    (fixed)   (return required)

LIMITATION: Can't model:
├─ Gifts (permanent transfers)
├─ Exchanges (mutual swaps)
├─ Service payments
├─ Time banking


AFTER (Phase 2): Multiple Transaction Types
═════════════════════════════════════════════

                    Transaction
                         │
        ┌────────────┬────┼────┬──────────┬────────┐
        │            │    │    │          │        │
        ▼            ▼    ▼    ▼          ▼        ▼
      LOAN        GIFT  EXCHANGE PAYMENT  TIME   PURCHASE
      (temp)   (permanent) (mutual) (work)  CREDIT   (store)
        │         │         │        │       │         │
        ├─────────┼─────────┼────────┼───────┼─────────┤
        │         │         │        │       │         │
    Borrower  Owner    Both users  Payer  Worker   Shopper
    Returns   Keeps    Swap         Pays   Credits   Pays
    Later     Forever  Equally      Money  Hours     Credits
        │         │         │        │       │         │
        ├─────────┼─────────┼────────┼───────┼─────────┤
        │         │         │        │       │         │
   Reputation Reputation Reputation Reputation Reputation
   ├─ Timely   ├─ Generous├─ Fair   ├─ Payment├─ Work
   │  Return   │ Spirit   │ Exchange│  Made   │  Quality
   ├─ Condition├─ Trust   │ Values  │ On-time │         
   └─ Care     └─         └─ Both   └─ Trust  └─

   Badge:     Badge:     Badge:     Badge:    Badge:
   Reliable   Helpful    Fair       Trustworthy Skilled
   Borrower   Community  Trader     Employer    Worker


USER JOURNEY: Service Exchange (Phase 2)
═════════════════════════════════════════

Alice (needs help moving) ────────────────────────────► 
                          Creates HelpRequest Resource
                          ├─ Title: "Help moving apartment"
                          ├─ Description: "Need 2-3 people to help"
                          ├─ Urgency: urgent
                          └─ Date needed: 2024-02-15
                                 │
                                 ▼
                    Posted to group/federation
                                 │
                      ┌──────────┼──────────┐
                      │          │          │
    Bob (available)   │      Carl (busy)   │
    "I can help"      │                    │
         │            │                    ▼
         ▼            │          Sophia (interested)
    Claim HelpRequest │          "2 hours only"
         │            │                │
         ▼            │                ▼
    ┌──────────────┐  │         ┌──────────────────┐
    │Transaction:  │  │         │Transaction:      │
    │FROM: Alice   │  │         │FROM: Alice       │
    │TO: Bob       │  │         │TO: Sophia        │
    │RESOURCE:Help │  │         │RESOURCE: Help    │
    │TYPE: service │  │         │TYPE: service     │
    │STATUS: active│  │         │STATUS: active    │
    │HOURS: 3      │  │         │HOURS: 2          │
    │COMPS: TIME   │  │         │COMPS: TIME       │
    └──────────────┘  │         └──────────────────┘
         │            │                │
         ▼            │                ▼
    Moving Day        │         Sophia helps for 2h
    Bob helps 3h      │              │
         │            │              ▼
         ├────────────┼──────────────┤
         │ All finish │              │
         ├────────────┼──────────────┤
         │            │              │
         ▼            │              ▼
    ┌──────────────┐  │         ┌──────────────────┐
    │Mark Complete │  │         │Mark Complete     │
    │TIME CREDITED:│  │         │TIME CREDITED:    │
    │Alice → +3h   │  │         │Alice → +2h       │
    │Bob → +3h     │  │         │Sophia → +2h      │
    │Rating: ⭐⭐⭐⭐⭐│  │         │Rating: ⭐⭐⭐⭐⭐   │
    └──────────────┘  │         └──────────────────┘
         │            │                │
         ▼            │                ▼
    Reputation Updates:
    ├─ Alice: +5 (community helper)
    ├─ Bob: +5 (reliable worker)
    ├─ Sophia: +5 (punctual worker)
    └─ All receive "Service Worker" badge
```

---

## FLOWCHART 6: PHASE 3 GOVERNANCE & VOTING

```
┌────────────────────────────────────────────────────────────────┐
│           PHASE 3: DEMOCRATIC DECISION MAKING                 │
│     Proposals → Voting → Implementation → Evaluation          │
└────────────────────────────────────────────────────────────────┘

PROPOSAL LIFECYCLE:
════════════════════

                        NEW PROPOSAL
                             │
                             ▼
                    ┌──────────────────┐
                    │ Draft Stage      │
                    │ - Author writes  │
                    │ - Define voting  │
                    │   method         │
                    │ - Set deadline   │
                    └────────┬─────────┘
                             │
                    Author submits
                             │
                             ▼
                    ┌──────────────────┐
                    │ Review Stage     │
                    │ - Moderators     │
                    │   check format   │
                    │ - May request    │
                    │   changes        │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                ✅ APPROVE        ❌ REJECT
                    │                 │
                    ▼                 ▼
            ┌─────────────────┐   Proposal Archived
            │ Open for Voting │   (with feedback)
            └────────┬────────┘
                     │
                  VOTING PERIOD
                  (1-14 days)
                     │
                ┌────┴────┬────┬─────────┐
                │         │    │         │
             FOR      AGAINST ABSTAIN  DELEGATE
             (Yes)    (No)   (No opinion)(to someone)
                │         │    │         │
                └────┬────┴────┴─────────┘
                     │
              VOTING CLOSES
                     │
                     ▼
         ┌──────────────────────────┐
         │ Count Votes              │
         │ Verify Quorum            │
         │ Apply Decision Method    │
         └────────┬─────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
    ✅ PASSED           ❌ FAILED
        │                    │
        ▼                    ▼
    ┌──────────────┐   ┌──────────────┐
    │ Accepted     │   │ Rejected     │
    │ - Scheduled  │   │ - Archived   │
    │   for impl.  │   │ - Feedback   │
    │ - Announce   │   │   sent to    │
    │ - Create     │   │   author     │
    │   tasks      │   │ - Can rerun  │
    └──────┬───────┘   │   next month │
           │           └──────────────┘
    IMPLEMENTATION PHASE
           │
           ▼
    ┌──────────────────┐
    │ Execute tasks    │
    │ - Update rules   │
    │ - Allocate funds │
    │ - Assign roles   │
    │ - Send notices   │
    └────────┬─────────┘
             │
    Update implemented_at
             │
             ▼
    Post-Implementation Review
    (check effectiveness)


VOTING METHODS COMPARISON:
═══════════════════════════

METHOD 1: Simple Majority (50% + 1)
───────────────────────────────────
Total Votes: 100
For: 51
Against: 49
RESULT: ✅ PASSES
Use Case: Routine decisions


METHOD 2: Supermajority (66%)
──────────────────────────────
Total Votes: 100
For: 66
Against: 34
RESULT: ✅ PASSES
Use Case: Important policy changes


METHOD 3: Consensus (85%+)
───────────────────────────
Total Votes: 100
For: 85
Against: 15
RESULT: ✅ PASSES
Use Case: Constitutional changes


METHOD 4: Quadratic Voting
──────────────────────────
User A votes FOR with power 1.0 = 1 point
User B votes FOR with power 2.0 = 4 points (2²)
User C votes AGAINST with power 3.0 = 9 points (3²)

Total FOR: 5 points
Total AGAINST: 9 points
RESULT: ❌ FAILS

Use Case: Prevents vocal minorities from dominating


RESOURCE ALLOCATION PROPOSAL:
═════════════════════════════

GROUP: Barcelona Community Kitchen

PROPOSAL:
"Allocate 50 working hours to new soup kitchen"

VOTING SUMMARY:
    For:      35 members
    Against:  5 members
    Abstain:  10 members
    ──────────────────
    Quorum:   83% ✅
    Result:   Simple Majority ✅ PASSES

IMPLEMENTATION:
    ┌─────────────────────────────────┐
    │ 50 hours allocated              │
    │ ├─ Distribution Algorithm:      │
    │ │  Need-Based (priority scoring)│
    │ └─ Schedule: 2024-02-01         │
    │                                 │
    │ Eligible Members (score):       │
    │ ├─ Maria (85) - No resources    │
    │ ├─ Jean (72) - Working full-time│
    │ ├─ Fatima (68) - Single parent  │
    │ ├─ Ahmed (45) - Already has help│
    │ └─ ...                          │
    │                                 │
    │ ALLOCATION:                     │
    │ ├─ Maria: 15 hours (setup)      │
    │ ├─ Jean: 12 hours (cooking)    │
    │ ├─ Fatima: 10 hours (serving)   │
    │ ├─ Others: 8-5 hours each       │
    │ └─ Reserve: 5 hours (backup)    │
    │                                 │
    │ NOTIFICATIONS SENT ✅           │
    │ CALENDAR UPDATED ✅             │
    │ REPUTATIONS UPDATED ✅          │
    └─────────────────────────────────┘


VOTING TRANSPARENCY:
════════════════════

PROPOSAL: "Increase annual budget 10%"

├─ Created By: Finance Committee
├─ Created At: 2024-01-15
├─ Voting Opens: 2024-01-16
├─ Voting Closes: 2024-01-23
├─ Status: VOTING OPEN
│
├─ VOTE BREAKDOWN (Live):
│  ├─ FOR: 42 (67%) ▓▓▓▓▓▓▓░░░
│  ├─ AGAINST: 15 (24%) ▓▓░░░░░░░░
│  ├─ ABSTAIN: 5 (8%) ▓░░░░░░░░░
│  └─ Quorum: 62/100 (62%) THRESHOLD MET ✅
│
├─ RECENT VOTES:
│  ├─ Alice (09:23 UTC): FOR ✓
│  ├─ Bob (09:15 UTC): AGAINST ✗
│  ├─ Carol (09:08 UTC): FOR ✓
│  └─ Dave (09:01 UTC): ABSTAIN ~
│
├─ ARGUMENTS:
│  FOR:
│  ├─ Alice: "We have growing membership"
│  ├─ Carol: "Need more resources for projects"
│  └─ ...
│
│  AGAINST:
│  ├─ Bob: "We should audit current spending first"
│  └─ ...
│
└─ VOTING HISTORY (Archive):
   All votes publicly viewable
   (But not who voted what, except by voter themselves)
```

---

## FLOWCHART 7: PHASE 4 FEDERATION HIERARCHY

```
┌────────────────────────────────────────────────────────────────┐
│        PHASE 4: RECURSIVE FEDERATION STRUCTURE                │
│     Groups → Federations → Federations of Federations         │
└────────────────────────────────────────────────────────────────┘

SINGLE GROUP (Phase 0-1):
═════════════════════════

           Group A
            │
        ┌───┼───┐
        │   │   │
       U1  U2  U3  (Users)
        │   │   │
        └───┼───┘
            │
      Resources
      ├─ Book A
      ├─ Tool B
      └─ Time Credit


FEDERATION OF GROUPS (Phase 3):
═════════════════════════════════

        Barcelona Federation
                 │
        ┌────────┼────────┐
        │        │        │
      Group1   Group2   Group3
      Gracia  Eixample Sagrada
        │        │        │
     ┌──┴──┐  ┌──┴──┐  ┌──┴──┐
     U1 U2 U3 U4 U5 U6 U7 U8 U9
        │        │        │
      Resources & Transactions
      (Cross-group visibility)


FEDERATED SUPER-GROUPS (Phase 4):
══════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    IBERIAN COMMONS                             │
│              (Federation of Federations)                        │
└─────────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    BARCELONA          MADRID            LISBON
    FEDERATION         FEDERATION        FEDERATION
        │                  │                  │
    ┌───┼───┐         ┌───┼───┐         ┌───┼───┐
    │   │   │         │   │   │         │   │   │
   G1  G2  G3        G4  G5  G6        G7  G8  G9
    │   │   │         │   │   │         │   │   │
   U... U... U...    U... U... U...    U... U... U...


MULTI-SECTOR FEDERATION (Phase 4):
════════════════════════════════════

           COMMONS NETWORK
                 │
    ┌────────────┼────────────┐
    │            │            │
FOOD SYSTEMS  HOUSING      SKILLS
FEDERATION    FEDERATION   FEDERATION
    │            │            │
 ┌──┴──┐      ┌──┴──┐      ┌──┴──┐
 │  │  │      │  │  │      │  │  │
Gr1...      Gr4...       Gr7...


HIERARCHICAL VOTING (Phase 4):
═══════════════════════════════

Proposal: "Establish inter-federation trade agreement"

LEVEL 1 - Individual Groups:
┌─────────────────────────────────────────┐
│ Group 1 (Gracia):                       │
│ ├─ Members vote: 23 FOR, 2 AGAINST     │
│ └─ Group delegates: YES (weighted 1.0) │
│                                         │
│ Group 2 (Eixample):                     │
│ ├─ Members vote: 18 FOR, 5 AGAINST     │
│ └─ Group delegates: YES (weighted 0.9) │
│                                         │
│ Group 3 (Sagrada):                      │
│ ├─ Members vote: 15 FOR, 8 AGAINST     │
│ └─ Group delegates: YES (weighted 0.8) │
└─────────────────────────────────────────┘

LEVEL 2 - Federation Council:
┌─────────────────────────────────────────┐
│ Barcelona Federation Council:            │
│ ├─ G1 vote: YES (weighted 1.0)          │
│ ├─ G2 vote: YES (weighted 0.9)          │
│ ├─ G3 vote: YES (weighted 0.8)          │
│ │                                       │
│ └─ Federation position: YES (weighted 1) │
│                                         │
│ Madrid Federation Council:              │
│ ├─ Mixed votes, position: YES (weighted 0.9)
│                                         │
│ Lisbon Federation Council:              │
│ ├─ Mixed votes, position: NO (weighted 0.7)
└─────────────────────────────────────────┘

LEVEL 3 - Iberian Commons Assembly:
┌─────────────────────────────────────────┐
│ ├─ Barcelona: YES (weighted 1.0)        │
│ ├─ Madrid: YES (weighted 0.9)           │
│ ├─ Lisbon: NO (weighted 0.7)            │
│ │                                       │
│ └─ RESULT: Supermajority YES ✅ PASSES │
│                                         │
│ IMPLEMENTATION:                         │
│ ├─ All 9 groups bound by decision      │
│ ├─ Cross-federation trading enabled    │
│ ├─ Resource prices harmonized          │
│ ├─ Dispute resolution protocol active  │
│ └─ AI matching across federations ON   │
└─────────────────────────────────────────┘


RESOURCE FLOW IN FEDERATED SYSTEM (Phase 4):
═════════════════════════════════════════════

Alice (Barcelona, need tools)
        │
        ▼
    [Searching for tools...]
        │
    ┌───┴───────────────────────────┐
    │                               │
GROUP 1             GROUP 2    [NO LOCAL MATCH]
Resources:          Resources:
├─ Book ✓           ├─ Book
├─ Hammer ✓         ├─ Saw
└─ Screwdriver      └─ Nails

    ↓ (expand to federation level)

BARCELONA FEDERATION
├─ GROUP 1: Hammer ✓ (3km away)
├─ GROUP 2: Saw (5km away)
├─ GROUP 3: Tool kit (8km away)

    ↓ (expand to cross-federation)

IBERIAN COMMONS
├─ MADRID: Industrial tools (250km)
├─ LISBON: Specialized equipment (500km)

OPTIMAL MATCH (AI):
    Hammer from Group 1 (3km)
    + Saw from Group 2 (5km)
    = TRANSACTION CREATED

Alice ────────────────► [Hammer] ◄────────── Joan (Group 1)
         Transfer                  Loan
         │                         │
         ▼                         ▼
    Time Credit:           Reputation Update:
    +2 hours to Joan       Joan +5 (helpful community)
         │                 Alice +3 (grateful borrower)
         └────────┬────────┘
                  │
            [Notification sent
             to Joan: Tool needed
             in Barcelona!]

             (Maybe Joan also
              needs something
              Alice can provide?
              AI suggests reciprocal
              exchange...)


FEDERATION CONSENSUS FLOW (Phase 4):
═════════════════════════════════════

PROPOSAL: "Emergency resource redistribution"
(Drought in region → food shortage)

Step 1: Individual Groups
┌─────────────────────────────────────────┐
│ EACH GROUP surveys members:             │
│ "Should we share food reserves?"        │
│ ├─ Anonymous vote                       │
│ ├─ Open discussion forum                │
│ ├─ Final group position recorded        │
│ └─ Can veto if severe local need        │
└─────────────────────────────────────────┘

Step 2: Federation Council
┌─────────────────────────────────────────┐
│ Representatives from each group meet    │
│ ├─ Discuss distribution fairness        │
│ ├─ Identify urgent needs                │
│ ├─ Allocate reserves proportionally     │
│ └─ Write redistribution plan            │
└─────────────────────────────────────────┘

Step 3: Final Group Approval
┌─────────────────────────────────────────┐
│ EACH GROUP approves final plan          │
│ ├─ Group discussions                    │
│ ├─ Final ratification vote              │
│ ├─ Groups can add local priorities      │
│ └─ Consensus-seeking discussions        │
└─────────────────────────────────────────┘

Step 4: Implementation
┌─────────────────────────────────────────┐
│ AUTOMATED DISTRIBUTION:                 │
│ ├─ Match surplus to shortage            │
│ ├─ Coordinate logistics                 │
│ ├─ Track deliveries                     │
│ └─ Auto-update reputations              │
│                                         │
│ GOVERNANCE LOG:                         │
│ ├─ All decisions documented             │
│ ├─ Fully transparent & auditable        │
│ ├─ Accessible to all members            │
│ └─ Can be referenced for appeals        │
└─────────────────────────────────────────┘
```

---

## FLOWCHART 8: COMPLETE SYSTEM ARCHITECTURE (Phase 4)

```
┌────────────────────────────────────────────────────────────────────┐
│              COMPLETE SYSTEM ARCHITECTURE (Phase 4)               │
│         Federated AI-Automated Resource Commons                    │
└────────────────────────────────────────────────────────────────────┘

PRESENTATION LAYER
═════════════════════════════════════════════════════════════════

Web UI                Mobile App              API Clients
├─ React/Vue.js       ├─ React Native         ├─ Integrations
├─ Real-time updates  ├─ Offline support      ├─ Bots
└─ Accessible         └─ Push notifications   └─ Analytics


API GATEWAY LAYER
═════════════════════════════════════════════════════════════════

    Request ──────────────────────────► API Gateway
                                              │
                                    ┌─────────┼─────────┐
                                    │         │         │
                    ┌──────────────┼─────────┼─────────┐
                    │              │         │         │
            Rate Limiting      Auth Check  Route    Logging
            (RateLimit)        (JWT/OAuth)  Validation


APPLICATION LAYER (Django)
═════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────┐
│                         VIEWS/VIEWSETS                       │
│  (REST API endpoints for resources, transactions, proposals) │
└───────────────────────────┬──────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
        ┌─────────────┐ ┌────────┐ ┌──────────┐
        │  Services   │ │ Helpers│ │ Managers │
        │ (Business   │ │(Utils) │ │(Complex  │
        │  Logic)     │ │        │ │  flows)  │
        └────────┬────┘ └────────┘ └──────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
MODELS       EVENTS         SIGNALS
├─ User      ├─ Pub/Sub      ├─ Auto
├─ Resource  ├─ Event Store  │  triggers
├─ Transac.  └─ Async Tasks  └─
├─ Proposal  │
└─ Federation│
             └─ CELERY
                TASKS


DATABASE LAYER
═════════════════════════════════════════════════════════════════

Primary DB (PostgreSQL):
├─ Users & Profiles
├─ Resources
├─ Transactions
├─ Proposals & Votes
├─ Groups & Federations
├─ Reputation Scores
├─ Audit Logs
├─ Messages (encrypted)
└─ Event Store


CACHE LAYER
═════════════════════════════════════════════════════════════════

Redis Multi-Use:
├─ Session Storage (Django sessions)
├─ Cache Broker (Celery)
├─ Rate Limiting Counters
├─ Feed Caching (recent transactions)
├─ User Lists (membership queries)
├─ Reputation Scores (frequently accessed)
└─ Real-time Notifications (pub/sub)


ASYNC PROCESSING LAYER
═════════════════════════════════════════════════════════════════

Celery + RabbitMQ:
│
├─ Badge Processing
│  └─ Award badges async on transactions
│
├─ Reputation Scoring
│  └─ Calculate multi-dimensional scores
│
├─ Notifications
│  ├─ Email digests
│  ├─ Push notifications
│  └─ In-app notifications
│
├─ Resource Matching
│  ├─ Find optimal exchanges
│  ├─ Suggest complementary resources
│  └─ AI-powered recommendations
│
├─ Distribution Optimization
│  ├─ Calculate allocation priorities
│  ├─ Suggest fair distributions
│  └─ Auto-allocate if authorized
│
├─ Governance Processing
│  ├─ Tally votes
│  ├─ Check quorum/thresholds
│  └─ Implement decisions
│
├─ Analytics & Reporting
│  ├─ Activity summaries
│  ├─ Health metrics
│  └─ Pattern detection
│
└─ Maintenance Tasks
   ├─ Key rotation
   ├─ Data cleanup
   ├─ Backups
   └─ Index optimization


SECURITY LAYER
═════════════════════════════════════════════════════════════════

Request ──► SSL/TLS ──► Authentication ──► Authorization
(HTTPS)        │           (JWT/OAuth)      (Permissions)
               │                │               │
               ▼                ▼               ▼
        Rate Limiting      Session Mgmt    Object-Level
        (DjangoRateLimit)   (Encrypted)     Permissions
               │                │           (django-guardian)
               └────────┬───────┴───────────┘
                        │
                        ▼
            Audit Logging & Monitoring
            (All sensitive ops logged)


FEDERATION LAYER
═════════════════════════════════════════════════════════════════

My Instance ──────────┐
                      │
            ┌──────────┼──────────┐
            │          │          │
        Fed 1      Fed 2      Fed 3
        (Barca)    (Madrid)   (Lisbon)
            │          │          │
        ┌───┼──┐   ┌───┼──┐   ┌───┼──┐
        G1 G2  G3  G4 G5  G6  G7 G8  G9
        │  │   │   │  │   │   │  │   │
       U... U... U...   ...


AI/MATCHING LAYER
═════════════════════════════════════════════════════════════════

Resource Matcher:
├─ Input: User needs + Available resources
├─ Algorithm: Similarity + Reputation + Accessibility
├─ Output: Ranked match suggestions
└─ Confidence scores

Distribution Optimizer:
├─ Input: Resource pool + User scores
├─ Algorithm: Multi-factor priority scoring
├─ Output: Fair allocation recommendations
└─ Can be manual-approved or auto-execute

Prediction Engine:
├─ Predict resource needs (ML time series)
├─ Identify supply gaps
├─ Suggest preventive sharing
└─ Anomaly detection (fraud, abuse)


OBSERVABILITY LAYER
═════════════════════════════════════════════════════════════════

Logging (ELK Stack):
├─ Application logs
├─ Request/response logs
├─ Error tracking (Sentry)
└─ Audit trails

Metrics (Prometheus):
├─ API response times
├─ Database query times
├─ Cache hit rates
├─ Task queue depths
└─ User activity

Monitoring (Grafana):
├─ Real-time dashboards
├─ Alerts (email, Slack)
├─ System health checks
└─ Capacity planning


WORKFLOW EXAMPLE: End-to-End Transaction
══════════════════════════════════════════

1. User clicks "Borrow Book"
   └─► API POST /api/v1/transactions/
           │
           ▼
2. Django processes request
   ├─ Deserialize JSON
   ├─ Validate data
   ├─ Check user auth
   ├─ Check resource exists
   ├─ Check permissions
   └─ Create Transaction object
           │
           ▼
3. Transaction.save() triggers
   ├─ Database INSERT
   ├─ Emit TransactionCreatedEvent
   ├─ Update cache (user's transactions)
   └─ Return 201 Created
           │
           ▼ (Async, <200ms user perceives)

4. Event propagates via EventBus
   ├─ Store in EventStore (audit)
   ├─ Queue async tasks
   └─ Notify subscribers
           │
   ┌───────┼───────┬─────────┐
   │       │       │         │
   ▼       ▼       ▼         ▼

5a. BadgeService      5b. ReputationService   5c. NotificationService
    └─ Check if           └─ Calculate           └─ Email recipient
      milestone              transaction          └─ In-app notification
                             impact               └─ Update feed

6. All tasks queued in Celery
   └─ Picked up by worker processes
      └─ Executed async
         └─ Results stored

7. Client receives immediate response:
   {
     "id": 54321,
     "status": "pending",
     "from_user": {...},
     "to_user": {...},
     "resource": {...},
     "type": "loan",
     "message": "Transaction created. Recipient notified."
   }

8. Within 30 seconds (async tasks complete):
   ├─ Badges awarded (if applicable)
   ├─ Reputation scores recalculated
   ├─ Notifications sent
   └─ Analytics logged

9. User sees in real-time (WebSocket):
   ├─ Badge notification (if earned)
   ├─ Reputation change
   └─ Activity feed update
```

---

## CRITICAL PATH TIMELINE

```
WEEK 1                  WEEK 2-3                WEEK 4
═══════════════════════════════════════════════════════════════

Day 1-3:               Day 8-10:               Day 15-16:
✅ DomainEventBus      ✅ E2EE Keys            ✅ API Refactor
✅ Decouple Item       ✅ Rate Limiting        ✅ Test Suite
✅ Decouple Loan       ✅ Security Headers     ✅ Migrations
                        ✅ Audit Logging       ✅ Staging Deploy

Day 4-5:               Day 11-14:              Day 17-20:
✅ Refactor Handlers   ✅ OWASP Scanning       ✅ Documentation
✅ Celery Setup        ✅ Integration Tests    ✅ Performance Test
✅ Event Store         ✅ Load Testing         ✅ Production Ready


MONTH 1 (Weeks 1-4): FOUNDATION                           ✅ COMPLETE
├─ Decouple architecture
├─ Security hardening
├─ API unification
└─ Test coverage >85%

MONTH 2 (Weeks 5-8): RESOURCE MODEL                       ⏳ IN PROGRESS
├─ Resource generalization
├─ Transaction expansion
├─ Social features
└─ Migration to production

MONTH 3 (Weeks 9-12): GOVERNANCE                          ⏳ PLANNED
├─ Voting systems
├─ Proposal infrastructure
├─ Resource distribution
└─ Group treasuries

MONTH 4-6: COOPERATION                                    ⏳ PLANNED
├─ Multi-group features
├─ Event scheduling
├─ Crowdfunding
└─ Skill endorsements

MONTH 7-9: FEDERATIONS                                    ⏳ PLANNED
├─ Hierarchical groups
├─ Federation governance
├─ Cross-federation trading
└─ Dispute resolution

MONTH 10-12: AI AUTOMATION                                ⏳ PLANNED
├─ Resource matching
├─ Distribution optimization
├─ Predictive analytics
└─ Recursive federations
```

END OF FLOWCHARTS