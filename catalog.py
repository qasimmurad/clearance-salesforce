"""Seeded org + request catalogue for the Clearance demo.

Everything here is a stand-in for a real Salesforce org. The numbers are
modelled on published admin-to-user ratios and typical mid-market org bloat;
they are illustrative, not measured. Nothing in this app touches a live org.
"""

ORG = {
    "name": "Vantage Logistics",
    "edition": "Enterprise Edition",
    "users": 340,
    "admins": 3,
    "open_requests": 87,
    "median_age_days": 19,
    "opp_custom_fields": 214,
    "active_flows": 62,
    "opp_validation_rules": 18,
    "open_opps": 1847,
    "accounts": 12400,
}

PERSONA = {
    "name": "Dana Whitfield",
    "title": "Sales Operations Manager",
    "access": "Standard user. No admin rights, no Setup access, no Flow Builder.",
}

# ---------------------------------------------------------------------------
# Requests. Each one is a full round trip: what a business user typed, what
# Clearance reads it as, the ambiguity it refuses to guess at, the artifact it
# drafts, and what deploying it would actually do to the org.
# ---------------------------------------------------------------------------

REQUESTS = [
    # ===================================================================== 1
    {
        "id": "REQ-1041",
        "bubble": "Stop reps over-discounting enterprise deals",
        "bubble_sub": "Guardrail · Opportunity",
        "raw": (
            "When a rep puts more than a 20% discount on an Enterprise deal they "
            "should get a warning. Right now we only find out at the end of the "
            "quarter when the margin is already gone."
        ),
        "artifact": "Validation Rule",
        "obj": "Opportunity",
        "confidence": 0.94,
        "restatement": (
            "On any open Opportunity whose Account is in the Enterprise segment, "
            "intervene when Discount % goes above 20."
        ),
        "clarify_q": "You said <em>warning</em>. Should this block the save, or let it through and tell someone?",
        "clarify_why": (
            "A validation rule blocks the save. It is the cheapest thing to build, "
            "but it stops the rep cold. Nine of your last twelve tickets that said "
            "\"warn\" were built as blocks, and four of those were rolled back "
            "within a month. This is the question a ticket queue never asks, and "
            "it is the one that decides whether the change survives."
        ),
        "options": [
            {
                "key": "block",
                "label": "Block the save",
                "meta": "Validation Rule · ~2 admin hours · reversible in one click",
                "risk": "Medium",
                "code": """Rule Name       Enterprise_Discount_Ceiling
Object          Opportunity
Active          true
Error Location  Discount_Percent__c        <- bound to the field, not the page

Formula
    AND(
      ISPICKVAL( Account.Customer_Segment__c , "Enterprise" ),
      Discount_Percent__c > 20,
      NOT( ISPICKVAL( StageName , "Closed Won" ) ),
      NOT( ISPICKVAL( StageName , "Closed Lost" ) ),
      NOT( $Permission.Bypass_Discount_Guardrail )
    )

Companion       Custom Permission "Bypass_Discount_Guardrail"
                assigned to: Deal Desk, Sales VP
                -> gives you an exception path that does not need a code change""",
                "msg_draft": (
                    "Error: Discount percentage entered exceeds the maximum allowable "
                    "threshold of 20% as defined by the Enterprise segment discount "
                    "policy; please revise your entry or obtain the requisite "
                    "approval prior to proceeding."
                ),
                "msg_revised": (
                    "Enterprise deals cap at a 20% discount. Lower the discount, or "
                    "ask your VP to approve an exception."
                ),
            },
            {
                "key": "notify",
                "label": "Let it save, tell the manager",
                "meta": "Record-Triggered Flow · ~6 admin hours · reversible in one click",
                "risk": "Low",
                "code": """Flow API Name   Opportunity_Discount_Alert
Type            Record-Triggered Flow (after save)
Object          Opportunity
Trigger         A record is created or updated
Entry Criteria  Account.Customer_Segment__c = "Enterprise"
                AND Discount_Percent__c > 20
                AND ISCHANGED( Discount_Percent__c )
                AND IsClosed = false

 1  Decision       "Already flagged?"  ->  Discount_Flagged__c = false
 2  Update Record  Opportunity.Discount_Flagged__c = true
 3  Action         Send Custom Notification
                     Recipient  {!$Record.Owner.ManagerId}
                     Title      "Discount above policy on {!$Record.Name}"

New field       Discount_Flagged__c · Checkbox · default false
                -> the checkpoint that stops the same deal alerting twice""",
                "msg_draft": (
                    "Notification: A discount value in excess of segment policy has "
                    "been recorded against the referenced opportunity record and is "
                    "hereby flagged for managerial review."
                ),
                "msg_revised": (
                    "A rep set a discount above 20% on an Enterprise deal. Open the "
                    "deal to see the numbers, or leave it if you are happy with it."
                ),
            },
        ],
        "impact": {
            "objects": "Opportunity (write) · Account (read)",
            "in_scope": "1,847 open opportunities · 312 Enterprise · 41 already above 20%",
            "limits": "No governor limit exposure. Validation rules run inline on save.",
            "conflicts": (
                "Opportunity already carries 18 validation rules. This makes 19. "
                "Salesforce guidance is to consolidate before 20 — you are one "
                "request away from that conversation."
            ),
            "rollback": "Untick Active. No data changes. Under a minute.",
        },
        "blast": {
            "headline": "41 open deals already break this rule.",
            "body": (
                "If you ship the blocking version, those 41 reps cannot save "
                "<em>any</em> edit to their deal — not a next step, not a close date — "
                "until the discount comes down. That is the failure mode that gets a "
                "change rolled back in week one. Clearance suggests scoping the rule "
                "to records created after go-live, or clearing the 41 first."
            ),
            "tone": "warn",
        },
    },

    # ===================================================================== 2
    {
        "id": "REQ-1042",
        "bubble": "Flag renewals with no CSM assigned",
        "bubble_sub": "Automation · Opportunity",
        "raw": (
            "Renewals keep landing on us with no customer success owner. I want "
            "somebody told when a renewal is two months out and nobody from CS is "
            "on it."
        ),
        "artifact": "Schedule-Triggered Flow",
        "obj": "Opportunity",
        "confidence": 0.88,
        "restatement": (
            "Every day, find open renewal Opportunities closing in 60 days with an "
            "empty CSM field, and tell the account's CS manager once."
        ),
        "clarify_q": "One alert per deal, or a weekly digest?",
        "clarify_why": (
            "A daily sweep with no checkpoint re-notifies the same person about the "
            "same deal every morning for sixty days. That is how a helpful alert "
            "becomes a filter rule. Whichever you pick, Clearance adds the "
            "checkpoint field — but the choice changes who gets interrupted and "
            "how often."
        ),
        "options": [
            {
                "key": "single",
                "label": "One alert per deal, the day it qualifies",
                "meta": "Schedule-Triggered Flow · ~4 admin hours · low blast radius",
                "risk": "Low",
                "code": """Flow API Name   Renewal_CSM_Coverage_Sweep
Type            Schedule-Triggered Flow
Frequency       Daily at 06:00, org time zone
Object          Opportunity
Filter          Type                   = "Renewal"
                CloseDate              = TODAY + 60
                CSM__c                 = null
                IsClosed               = false
                Coverage_Alert_Sent__c = false

 1  Get Records    User WHERE Id = {!$Record.Account.CS_Manager__c}
 2  Action         Send Email Alert -> Renewal_Uncovered_Alert
                     To  CS Manager     CC  Opportunity Owner
 3  Update Record  Opportunity.Coverage_Alert_Sent__c = true
 4  Create Record  Task
                     Subject   "Assign a CSM - renewal closes {!$Record.CloseDate}"
                     Assigned  {!$Record.Account.CS_Manager__c}
                     Due       TODAY + 3

New field       Coverage_Alert_Sent__c · Checkbox · default false""",
                "msg_draft": (
                    "Notification: The subject renewal opportunity has been identified "
                    "as lacking an assigned Customer Success Manager resource within "
                    "the 60-day pre-close window and requires remediation."
                ),
                "msg_revised": (
                    "This renewal closes in 60 days and has no CSM. Assign one, or "
                    "reply to this email if the account does not need one."
                ),
            },
            {
                "key": "digest",
                "label": "Weekly digest, all uncovered renewals at once",
                "meta": "Schedule-Triggered Flow + report subscription · ~3 admin hours",
                "risk": "Low",
                "code": """Flow API Name   Renewal_Coverage_Digest
Type            Schedule-Triggered Flow
Frequency       Weekly, Monday 07:00
Object          Opportunity  (runs once, not per record)

 1  Get Records    Opportunity
                     Type      = "Renewal"
                     CloseDate <= TODAY + 60
                     CSM__c    = null
                     IsClosed  = false
 2  Decision       "Anything to send?"  ->  count > 0
                     (no matches = no email; a zero-row digest trains people
                      to ignore the real one)
 3  Loop           Build a plain-text list, one line per deal
 4  Action         Send Email Alert -> Renewal_Coverage_Weekly
                     To  CS Manager group

No new fields   Nothing to un-ship if you drop this later.""",
                "msg_draft": (
                    "Weekly Renewal Coverage Exception Report: the following "
                    "opportunity records have been determined to be deficient in "
                    "Customer Success Manager assignment as of the reporting date."
                ),
                "msg_revised": (
                    "These renewals close in the next 60 days and have no CSM. "
                    "Assign someone to each, or reply to tell us which ones do not "
                    "need one."
                ),
            },
        ],
        "impact": {
            "objects": "Opportunity (write) · Account (read) · User (read) · Task (create)",
            "in_scope": "1,847 open opportunities · 284 renewals · 61 with no CSM · 9 inside the 60-day window today",
            "limits": "Scheduled flows process up to 250,000 records a day org-wide. This touches about 9. No exposure.",
            "conflicts": (
                "62 active flows in the org, 7 of them on Opportunity. Two are "
                "after-save record-triggered; a scheduled flow runs in its own "
                "transaction, so order of execution will not collide."
            ),
            "rollback": "Deactivate the flow. One checkbox field is left behind on 1,847 records.",
        },
        "blast": {
            "headline": "The first run fires 9 alerts at once.",
            "body": (
                "Nine renewals already sit inside the 60-day window with no CSM. "
                "Day one, all nine land in the same inbox in the same minute, which "
                "reads as a broken system rather than a working one. Clearance can "
                "mark the existing nine as already-alerted so the flow starts quiet "
                "and only speaks up about deals that cross the line from here on."
            ),
            "tone": "warn",
        },
    },

    # ===================================================================== 3
    {
        "id": "REQ-1043",
        "bubble": "Track why customers churn",
        "bubble_sub": "New field + report · Account",
        "raw": (
            "I can't answer \"why are we losing customers\" without reading Slack "
            "threads one by one. I need it in Salesforce so I can actually report "
            "on it."
        ),
        "artifact": "Custom Field + Report",
        "obj": "Account",
        "confidence": 0.91,
        "restatement": (
            "Add a structured reason customers leave, and a report that groups "
            "churned accounts by it."
        ),
        "clarify_q": "On the Account, or on the Opportunity that was lost?",
        "clarify_why": (
            "Account gives you one reason per customer, which is what an exec "
            "dashboard wants. Opportunity gives you a reason per lost deal, which "
            "is what a pipeline review wants. This is the one decision in your "
            "queue that is genuinely expensive to reverse: once reps start typing "
            "into the field, moving it means a migration."
        ),
        "options": [
            {
                "key": "account",
                "label": "Account — one reason per customer",
                "meta": "Picklist + detail field + report · ~5 admin hours",
                "risk": "Medium",
                "code": """Field           Churn_Reason__c
Object          Account
Type            Picklist (restricted)
Label           Churn reason
Help Text       Pick the main reason this customer left. If more than one
                applies, pick the one that would have kept them if we had
                fixed it.

Values          Price
                Missing capability
                Switched to a competitor
                Support experience
                Low adoption
                Business closed or acquired
                Other

Companion       Churn_Reason_Detail__c · Text Area (255)
                Label      Churn reason - details
                Help Text  Required when the reason is Other. One or two
                           sentences.

Validation      Churn_Reason_Detail_Required
                AND( ISPICKVAL( Churn_Reason__c , "Other" ),
                     ISBLANK( Churn_Reason_Detail__c ) )
                Error Location  Churn_Reason_Detail__c

Security        Read/Write  Sales Ops, CS Manager, System Admin
                Read only   Sales Rep, Executive
Layout          Account -> Customer Health, after "Account Status"

Report          "Churn reasons - trailing 4 quarters"
                Type      Accounts
                Group by  Churn reason -> record count + sum of ARR
                Filter    Status = Churned AND Churn Date = LAST 4 QUARTERS""",
                "msg_draft": "Value required. The detail field must be populated when Other is selected.",
                "msg_revised": (
                    "Add a sentence about why this customer left. \"Other\" only "
                    "helps later if we know what it meant."
                ),
            },
            {
                "key": "opportunity",
                "label": "Opportunity — one reason per lost deal",
                "meta": "Picklist on a standard object · ~4 admin hours",
                "risk": "Medium",
                "code": """Field           Loss_Reason__c
Object          Opportunity
Type            Picklist (restricted)
Label           Loss reason
Help Text       Pick why this deal was lost. Fill it in before you move the
                deal to Closed Lost.

Values          Price
                Missing capability
                Lost to a competitor
                No decision / no budget
                Timing
                Other

Validation      Loss_Reason_Required_On_Close
                AND( ISPICKVAL( StageName , "Closed Lost" ),
                     ISBLANK( TEXT( Loss_Reason__c ) ) )
                Error Location  Loss_Reason__c

Report          "Loss reasons by segment - trailing 4 quarters"
                Type      Opportunities
                Group by  Loss reason x Customer segment

Caveat          A churned customer is not the same thing as a lost deal.
                A customer who renews for two years and then leaves has no
                Closed Lost opportunity at all - this design will not see them.""",
                "msg_draft": "Invalid: Loss Reason is a required field for records in the Closed Lost stage.",
                "msg_revised": (
                    "Pick a loss reason before you close this deal. It takes a "
                    "second now and saves the quarterly review."
                ),
            },
        ],
        "impact": {
            "objects": "Account (write) · Opportunity (read, for the backfill option)",
            "in_scope": "12,400 accounts · 1,912 already marked Churned · all 12,400 start blank",
            "limits": "Well inside the 800 custom fields per object ceiling on Enterprise Edition.",
            "conflicts": (
                "Account already has three picklists with overlapping intent: "
                "Status__c, Health_Score__c, and Lost_Reason__c — the last created "
                "in 2022, populated on 4 records, on no page layout. Clearance "
                "recommends retiring Lost_Reason__c rather than shipping a fourth."
            ),
            "rollback": (
                "Weakest rollback in the queue. A field with data in it can be "
                "hidden, but not cleanly removed."
            ),
        },
        "blast": {
            "headline": "Your report is empty on day one.",
            "body": (
                "1,912 accounts are already churned and none of them will have a "
                "reason on file. You are roughly two quarters from a chart worth "
                "showing an exec. Two ways to shorten that: accept the wait, or run "
                "a one-time backfill from the Closed Lost reasons already sitting "
                "on Opportunity — which covers about 640 of the 1,912 and leaves "
                "the rest blank."
            ),
            "tone": "warn",
        },
    },

    # ===================================================================== 4
    {
        "id": "REQ-1044",
        "bubble": "Require VP sign-off on deals over $250K",
        "bubble_sub": "Approval process · Opportunity",
        "raw": (
            "Anything over 250k should need a VP to say yes before it goes to "
            "Negotiation. Right now it's a Slack message and nobody can find it "
            "six months later when finance asks."
        ),
        "artifact": "Approval Process",
        "obj": "Opportunity",
        "confidence": 0.96,
        "restatement": (
            "Gate the move into Negotiation on Opportunities above $250,000 behind "
            "a VP approval, with an auditable record of who approved what."
        ),
        "clarify_q": "Who counts as \"a VP\" — the rep's manager's manager, or a named group?",
        "clarify_why": (
            "Role hierarchy routes itself and survives reorgs, but fails silently "
            "when someone's Manager field is blank — the record locks and nobody is "
            "asked to approve it. You have 14 users with a blank Manager field "
            "today. A named queue never breaks that way but needs upkeep every "
            "time someone changes job."
        ),
        "options": [
            {
                "key": "hierarchy",
                "label": "Manager's manager, with a queue fallback",
                "meta": "Approval Process · ~8 admin hours · highest blast radius in the queue",
                "risk": "High",
                "code": """Approval Process  Large_Deal_VP_Approval
Object            Opportunity

Entry Criteria    Amount > 250000
                  AND ISCHANGED( StageName )
                  AND ISPICKVAL( StageName , "Negotiation" )

Record Lock       Lock on submission. Admins can still edit.

Initial Submission
  · Field Update  Approval_Status__c -> "Pending VP"
  · Email Alert   Large_Deal_Submitted -> approver

Step 1  "VP sign-off"
  Approver        Related user field  ->  Owner.Manager.Manager
  If blank        Route to queue "Deal Desk"     <- covers your 14 orphans
  On reject       Final rejection

Final Approval
  · Field Update  Approval_Status__c -> "Approved"
  · Field Update  Approved_By__c, Approved_Date__c
  · Unlock record

Final Rejection
  · Field Update  Approval_Status__c -> "Rejected"
  · Email Alert   to Opportunity Owner, includes the rejection comment
  · Unlock record""",
                "msg_draft": (
                    "Your approval request has been rejected. Please consult the "
                    "approval history related list for further information "
                    "regarding the disposition of this record."
                ),
                "msg_revised": (
                    "Your VP did not approve this deal. Their reason is below. "
                    "Update the deal and send it for approval again."
                ),
            },
            {
                "key": "queue",
                "label": "A named Deal Desk queue",
                "meta": "Approval Process · ~6 admin hours · needs upkeep after reorgs",
                "risk": "Medium",
                "code": """Approval Process  Large_Deal_Desk_Approval
Object            Opportunity

Entry Criteria    Amount > 250000
                  AND ISCHANGED( StageName )
                  AND ISPICKVAL( StageName , "Negotiation" )

Record Lock       Lock on submission. Admins can still edit.

Step 1  "Deal Desk review"
  Approver        Queue "Deal_Desk_VP"  (4 named members today)
  Assignment      First responder approves for the queue
  On reject       Final rejection

Ongoing cost      Someone owns queue membership. When a VP changes role and
                  nobody updates the queue, deals sit locked with no owner.
                  Clearance suggests a quarterly membership review task.""",
                "msg_draft": (
                    "Rejected. Refer to approval history for the rationale documented "
                    "by the approving party."
                ),
                "msg_revised": (
                    "The Deal Desk did not approve this deal. Their reason is below. "
                    "Fix what they flagged and send it again."
                ),
            },
        ],
        "impact": {
            "objects": "Opportunity (write, lock) · User (read) · Queue (read)",
            "in_scope": "1,847 open opportunities · 96 above $250K · 23 already sitting in Negotiation",
            "limits": "Within the 300 active approval processes per org ceiling. Currently 11 active.",
            "conflicts": (
                "Overlaps REQ-1041. If both ship, a $300K Enterprise deal at a 25% "
                "discount hits a hard save block AND an approval gate for one "
                "action, down two different error paths. Clearance recommends "
                "sequencing: approval first, then re-scope the discount rule to "
                "skip records already in approval."
            ),
            "rollback": (
                "Deactivating strands any in-flight approvals. They have to be "
                "recalled first, one at a time."
            ),
        },
        "blast": {
            "headline": "23 deals in Negotiation right now slip through.",
            "body": (
                "An approval process fires on submission, never retroactively. The "
                "23 large deals already in Negotiation will close with no VP "
                "sign-off and no audit record — which is exactly the gap finance "
                "asked about. Someone has to walk those 23 back a stage and "
                "resubmit them, or accept a hole in the audit trail for this "
                "quarter. Clearance can generate the list."
            ),
            "tone": "critical",
        },
    },
]

# What the rest of the admin queue looks like behind Dana's request.
QUEUE = [
    ("REQ-1039", "Add a 'Reason for extension' field to Contract", "Config · low risk", 14, "Ready to draft"),
    ("REQ-1040", "Nightly sync of territory assignments", "Needs code · Apex", 22, "With admin"),
    ("REQ-1036", "Report: win rate by lead source, last 6 quarters", "Already possible today", 31, "Answered"),
    ("REQ-1044", "Require VP sign-off on deals over $250K", "Config · high risk", 9, "Ready to draft"),
    ("REQ-1031", "Stop the duplicate contact alert firing on imports", "Duplicate of REQ-0998", 38, "Closed as duplicate"),
]

# Where the 87 open requests actually land once Clearance triages them.
TRIAGE = [
    ("Already possible today", 24, "Answered on the spot with a how-to. No admin touched it."),
    ("Config, low risk, auto-drafted", 28, "Clearance drafts it, an admin approves in minutes."),
    ("Config, needs admin design", 16, "Real design work. Clearance still does the impact analysis."),
    ("Duplicate of an open request", 11, "Merged into the original."),
    ("Needs code (Apex or LWC)", 8, "Out of scope. Routed to the dev queue with the spec attached."),
]

# 12-week open-backlog curve. Baseline is the org's own trailing average;
# the Clearance curve is a model, not a measurement.
BACKLOG_WEEKS = list(range(0, 12))
BACKLOG_BASE = [87, 89, 92, 90, 94, 97, 95, 99, 102, 100, 104, 107]
BACKLOG_CLEARANCE = [87, 78, 66, 57, 49, 42, 38, 33, 30, 28, 26, 25]

# The hero figure on the dashboard already carries median time-to-live, so the
# tiles below it must not repeat it - one hero per view, no restated numbers.
METRICS = [
    ("Resolved without an admin touching it", "40%", "35 of 87 · was 0%"),
    ("Requests fulfilled per month", "71", "was 34"),
    ("Admin hours a week spent on intake", "3.5", "was 11.0"),
    ("Requests abandoned before fulfilment", "6%", "was 22%"),
]
