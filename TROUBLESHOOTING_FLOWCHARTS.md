# Administrator Troubleshooting Flowcharts
## Visual Decision Trees for Common Platform Issues

**Version:** 1.0  
**Format:** ASCII Art (print-friendly)  
**Status:** Production Ready

---

## 🔧 FLOWCHART 1: User Can't Login

```
                          ┌─────────────────┐
                          │ User Can't Login│
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              Getting Error?              No Error shown
                    │                             │
      ┌─────────────┼─────────────┐             │
      │             │             │             │
   401 Error    429 Error   Other Error   Page loads, won't
   Unauthorized  Rate Limit  (500, etc.)    login accepted
      │             │             │             │
      ▼             ▼             ▼             ▼
   Check    Too many login  Check system   User typed
   Email &   attempts in    status page    wrong email
   Password  short time     
      │          │             │             │
   Wrong?   Locked out?   System down?  Ask correct
      │          │             │        email again
   ┌──┴──┐    ┌──┴──┐       ┌──┴──┐        │
 Yes│   │No  Yes│   │No    Yes│   │No  ┌───┴────┐
   ▼    ▼     ▼    ▼         ▼    ▼    │Has MFA?│
 Send  Check  Reset  Wait  Wait &  Weird └───┬────┘
Reset  MFA  Unlock  60s  Escalate Code!    │
Link   Enabled?        to Eng      │    ┌───┴────┐
         │                          │   Yes│   │No
      ┌──┴──┐                       ▼    ▼     ▼
    Yes│   │No                    Check  Ask for Ask for
      ▼    ▼                   MFA Code  new code password
    Bypass  Send  Resend            │        │     reset
    needed MFA     MFA              ├────────┘     │
      │       code   code           │              │
      ▼       │      │              ├──────────────┘
    CALL    WORKS?  WORKS?          │
    USER      │      │              │
             ┌┴──────┴┐             │
             ▼        ▼             │
           LOGIN   LOG IN        LOG IN
           SUCCESS SUCCESS       SUCCESS


DECISION POINTS:
☐ Ask: What error do they see?
☐ Check: Admin > Users > Find user > Status
☐ Check: Admin > Settings > Security > MFA enabled?
☐ Check: Monitor > System Health > Status
☐ Action: Password reset (auto-emails link)
☐ Action: MFA bypass (call user, verify identity)
☐ Action: Unlock account (if locked out)

TIME TO RESOLVE: 2-5 minutes
ESCALATE IF: Still failing after all steps
```

---

## 🔧 FLOWCHART 2: Task Execution Failed

```
                    ┌──────────────────┐
                    │Task Exec Failed  │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    Status Code          Message               No
    Shows?               Shows?              Message
        │                    │                 │
   ┌────┴────┐          ┌────┴────┐          │
   │          │          │         │          │
 401/403    429  400/422  500  Timeout   Hangs/
 Auth      Rate   Request Server          Stalls
 Error     Limit  Invalid  Error
   │        │       │       │       │
   ▼        ▼       ▼       ▼       ▼
Check   Upgrade  Check   Check  Check
API Key Quota or JSON  System  Query
  │      Wait    Format  Health  Size
  │      │       │       │       │
  ├─┐  ┌─┴──┐   ├─────┐ ├─────┐ ├─────────┐
  │ │  │    │   │     │ │     │ │         │
  ▼ ▼  ▼    ▼   ▼     ▼ ▼     ▼ ▼         ▼
Valid?Wait &  Simplify Try  Is  Split
     Retry  Query   Again Soon  Into
   │          │       │      │   Multiple
   No─→Send   Success!Success!  Tasks
   Reset Link           │       │
             ┌──────────┴───────┘
             ▼
           WORKS!


DECISION TREE:
Step 1: Error Code?
├─ 401/403: Check API key validity
├─ 429: Check rate limit headers, wait 60s
├─ 400/422: JSON validation error
├─ 500: System error, try again in 5 min
└─ Timeout: Query too complex, simplify

Step 2: Framework Used?
├─ LangGraph (speed): Should be <2 seconds
├─ CrewAI (quality): Should be <60 seconds  
└─ AutoGen (reliability): Should be <120 seconds

Step 3: Query Complexity?
├─ Simple question: Use LangGraph
├─ Complex analysis: Use CrewAI
└─ Code generation: Use AutoGen

TIME TO RESOLVE: 5-15 minutes
ESCALATE IF: System error (500) persists
```

---

## 🔧 FLOWCHART 3: API Rate Limited (429)

```
                    ┌──────────────────┐
                    │429 Rate Limited  │
                    └────────┬─────────┘
                             │
              Check Headers:
              X-RateLimit-Limit
              X-RateLimit-Remaining
              X-RateLimit-Reset
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  Per-Minute Limit   Per-Hour Limit    Per-Day Limit
  Reached            Reached           Reached
  (100/min)          (6,000/hr)        (Daily Quota)
        │                    │                    │
        ▼                    ▼                    ▼
   Wait 60              Wait until            Upgrade
   Seconds              hour resets            Quota
   & Retry              (check clock)          (Admin)
        │                    │                    │
        ├────────────────────┼────────────────────┤
        │
        ▼
   Implement Exponential
   Backoff in Code:
   
   Attempt 1: Wait 1 second
   Attempt 2: Wait 2 seconds
   Attempt 3: Wait 4 seconds
   Attempt 4: Wait 8 seconds
   Max: 60 seconds
        │
        ├─ Add Jitter (+/- random)
        ├─ Max retry: 3-5 attempts
        ├─ Log all attempts
        └─ Alert on repeated 429s
        │
        ▼
   SUCCESS or
   ESCALATE FOR
   QUOTA UPGRADE


SOLUTIONS:
Option 1: WAIT (Immediate)
- Wait until rate limit resets
- Check X-RateLimit-Reset header
- Time: 60 seconds to 24 hours

Option 2: OPTIMIZE (15 minutes)
- Batch requests efficiently
- Cache results (use DragonflyDB)
- Reduce request frequency
- Example savings: 50%+

Option 3: UPGRADE (1 hour)
- Admin: Go to Users > [User] > Quota
- Increase requests/minute
- Increase requests/month
- Billing: Additional cost

Option 4: USE CACHE (Immediate)
- Check DragonflyDB cache
- Store and reuse results
- Reduce API calls 40-70%


PREVENTION:
✓ Batch 10 requests into 1
✓ Cache for 1 hour
✓ Use webhooks vs polling
✓ Implement backoff
✓ Monitor usage
✓ Alert at 80% quota

TIME TO RESOLVE: 1 minute (wait) or 15 min (optimize)
```

---

## 🔧 FLOWCHART 4: High Latency (Slow Response)

```
                   ┌─────────────────┐
                   │ Slow Response   │
                   │ (>2 seconds)    │
                   └────────┬────────┘
                            │
              Check Status Page:
              https://status.superagent.com
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   System OK          Degraded           Outage
   (All Green)        (Yellow)           (Red)
        │                   │                   │
        ▼                   ▼                   ▼
   Check User's         Wait for      ESCALATE
   Load                 Recovery      IMMEDIATELY
        │                   │
   ┌────┴────┐              │
   │          │              │
Local  Network  └──────┐
Issue  Issue           │
   │      │            │
   ▼      ▼            ▼
Check Ping  Check   Wait &
Browser  to API    Retry
Cache    Server
   │      │
   ├──────┤
   ▼
Is Request:
  ├─ LangGraph: <2s expected
  ├─ CrewAI: 15-60s expected
  ├─ AutoGen: 30-120s expected
   │
   ├─ Too slow? ──→ Check framework
   │
   ▼
Check Query:
   ├─ Very complex? ──→ Simplify
   ├─ Large documents? ──→ Split files
   ├─ Many API calls? ──→ Use batch
        │
        ▼
   Try Again
        │
   ┌────┴───────┐
   ▼            ▼
 FASTER?     STILL SLOW?
   │            │
  OK!       Possible
            System Issue
             │
             ▼
          ESCALATE


OPTIMIZATION STEPS:
1. Simplify Query
   - Break complex questions into parts
   - Ask for specific output format
   - Use specific frameworks

2. Reduce Context
   - Fewer documents uploaded
   - Smaller file sizes
   - More specific content

3. Optimize Code (if using API)
   - Batch requests
   - Use caching
   - Async/await properly
   - Connection pooling

4. Check System Load
   - Admin > Monitoring > Load
   - Try at off-peak hours
   - Scale if needed

TIME TO RESOLVE: 2-10 minutes
ESCALATE IF: Slow everywhere, not just for you
```

---

## 🔧 FLOWCHART 5: Knowledge Base Search Returns Poor Results

```
              ┌──────────────────────┐
              │ Search Results Bad   │
              │ or No Results        │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    No Results        Wrong Results   Confusing
    Returned         Returned         Results
         │               │               │
         ▼               ▼               ▼
    Is Document:   Is Query:       Is Relevance:
    ├─ Uploaded?   ├─ Too vague?   ├─ Low ranking?
    ├─ Indexed?    ├─ Ambiguous?   ├─ Multiple
    ├─ Public?     ├─ Too long?    │  meanings?
         │             │               │
         ▼             ▼               ▼
    Check:       Reframe          Check:
    ├─ Collection ├─ Be specific  ├─ Collection
    │ name       ├─ Use keywords │ settings
    ├─ Status    └─ Use examples ├─ Embedding
    │ "indexed"                  │ model
    ├─ File type                 └─ Threshold
    └─ Size
         │
    All good?
         │
    ┌────┴────┐
    ▼         ▼
   YES      NO
    │        │
    │    Upload
    │    or Fix
    │        │
    │        └──→ Try Again
    │
    ▼
 Reindex
 Collection
    │
    └──→ Try Again
         │
    ┌────┴───────┐
    ▼            ▼
 WORKS!    Still Poor
           Results
           │
           ▼
        ESCALATE


TROUBLESHOOTING STEPS:

Issue: No results
Step 1: Check document uploaded
 - Go to Knowledge Base > [Collection]
 - See document listed?
 - If no → Upload it

Step 2: Check indexing status
 - Admin > Knowledge Base > Status
 - Show "Indexed: X chunks"?
 - If pending → Wait 5-10 min

Step 3: Verify collection visible
 - Try searching from different account
 - Check permissions

Step 4: Re-upload if stuck
 - Delete document
 - Upload again
 - Index typically takes 2-5 min


Issue: Wrong results
Step 1: Improve query
 - Bad: "machine learning"
 - Good: "How do I implement ML in Python?"

Step 2: Add context
 - Upload more related documents
 - Clarify domain/context

Step 3: Check collection contains relevant docs
 - Browse collection documents
 - Add missing resources


Issue: Poor ranking
Step 1: Check embedding model
 - Admin > Knowledge Base > Settings
 - See embedding model listed?
 - Consider more advanced model

Step 2: Lower similarity threshold
 - Default: 0.7
 - Try: 0.5-0.6
 - More results, may be less relevant

Step 3: Reindex with better settings
 - Delete collection
 - Re-create with better params
 - Re-upload documents


OPTIMIZATION:
✓ Use specific search terms
✓ Upload multiple formats (PDF, markdown, etc.)
✓ Keep documents focused (1 topic per doc)
✓ Use consistent terminology
✓ Add table of contents for large docs
✓ Index often (set to auto-index)

TIME TO RESOLVE: 5-15 minutes
```

---

## 🔧 FLOWCHART 6: Cost Too High

```
                    ┌──────────────────┐
                    │ Cost Too High    │
                    │ for This Month   │
                    └────────┬─────────┘
                             │
        First: Accept Reality
        Each API call costs $
        Optimization takes time
                             │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    Immediate      Medium-term    Long-term
    (Today)        (This Week)     (Ongoing)
         │                    │                    │
         ▼                    ▼                    ▼
    PAUSE        OPTIMIZE      ARCHITECTURE
    Services    Workflows      CHANGES
         │           │              │
    Which are    Which cost    Consider:
    not critical? the most?    ├─ Caching
    Disable them └─ Switch to  ├─ Local models
         │        cheaper      ├─ Rate limiting
    ├─ Webhooks  framework    └─ Batch jobs
    ├─ Advanced  ├─ Use Lang
    │ Analytics  │ Graph for
    ├─ Premium   │ simple tasks
    │ Features  ├─ Cache more
    └─ Custom   │ results
      Agents    └─ Batch
         │       requests
    Monthly     │
    Savings:    Monthly
    $__         Savings:
         │       $__
         │
         ├────────────────────┬─────────────────────┐
         │                    │                     │
         └────────────────────┼─────────────────────┘
                              │
                              ▼
                    BUDGET SET & MONITORED
                    Spend alerts: 50%, 75%, 90%


COST BREAKDOWN:
Check your spending:
Admin > Analytics > Cost

By Framework:
├─ LangGraph: Cheapest ($0.01-0.05/call)
├─ CrewAI: Medium ($0.20-1.00/call)
└─ AutoGen: Expensive ($0.50-5.00/call)

By User:
├─ Heavy users: Expensive
├─ Light users: Cheap
└─ Identify outliers

By Day:
├─ Peak days: More calls
├─ Off-peak: Fewer calls
└─ Plan accordingly


COST REDUCTION STRATEGIES:

Strategy 1: Use Right Framework
Current: CrewAI for everything (EXPENSIVE)
Better: Use LangGraph 70%, CrewAI 20%, AutoGen 10%
Savings: 60-70%

Strategy 2: Implement Caching
Current: Same query run multiple times
Better: Cache 1 hour
Savings: 40-50%

Strategy 3: Batch Processing
Current: Individual API calls
Better: Batch 10 together
Savings: 30-40%

Strategy 4: Use Local Models
Current: 100% cloud LLMs
Better: 20% local + 80% cloud
Savings: 20-30%

Strategy 5: Reduce Complexity
Current: Large documents uploaded each time
Better: Keep knowledge base updated
Savings: 30-50%

TOTAL POTENTIAL SAVINGS: 50-70%


DAILY MONITORING:
☐ Check cost dashboard (Admin > Analytics)
☐ Compare to previous days
☐ Identify expensive tasks
☐ Alert at 80% quota
☐ Review spike causes


TIME TO REDUCE COSTS: 1-7 days
PERMANENT SAVINGS: 50-70% typically achieved
```

---

## 📋 Flowchart Summary

| Flowchart | Issue | Time | Escalate If |
|-----------|-------|------|-------------|
| 1. Login | User can't log in | 2-5 min | Still failing |
| 2. Task Failed | Task won't execute | 5-15 min | System error |
| 3. Rate Limited | 429 errors | 1-15 min | Quota issue |
| 4. Slow | >2s response | 2-10 min | System-wide |
| 5. Search Poor | Bad KB results | 5-15 min | Persistent |
| 6. Cost | Too expensive | Variable | Architecture |

---

## 🖨️ How to Use These Flowcharts

**Print Format:**
- Print on 11x17" (ledger) for wall chart
- Or 8.5x11" and tape together
- Laminate for durability
- Post in support area

**Digital Format:**
- Store on internal wiki
- Link from support KB
- Include in support onboarding
- Email to support team

**How Support Uses:**
1. Customer calls with issue
2. Find flowchart
3. Follow decision tree
4. Note each decision point
5. Reach resolution or escalation

**Benefits:**
✓ Consistent responses
✓ Faster resolution
✓ Less escalations
✓ Better support QA
✓ New staff training

---

**Status**: ✅ Production Ready  
**Last Updated**: November 2025  
**Print Quality**: 300 DPI recommended  
**Laminate**: Highly recommended for durability
