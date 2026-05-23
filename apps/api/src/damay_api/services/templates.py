"""Outbound WhatsApp message templates.

Filipino voice with light Taglish where natural. DAMAY = "to share in feeling,
to extend help"; copy is warm, communal, never crypto-bro. No placeholders left
unfilled at send time — callers must pass every named field.

Keep these as module-level constants so reviewers can grep + diff copy without
hunting through code.
"""

from __future__ import annotations

# --- Inbound acknowledgements ---------------------------------------------------

WELCOME_JOIN = (
    "Welcome sa {round_name}! Position #{position} ka. "
    "Mag-aabang lang tayo ng signal para sa cycle 1. 💛"
)

AWAITING_CONTRIBUTION = (
    "Cycle {cycle} na! Reply PAY para mag-contribute ng ₱{amount}. "
    "Hanggang {deadline_pretty} lang."
)

PAY_RECEIVED = (
    "Salamat, {name}! Process pa namin ang ₱{amount} on-chain. "
    "We'll text once confirmed."
)

PAY_CONFIRMED = (
    "Done na! ✅ Cycle {cycle} contribution confirmed. "
    "View on chain: {stellar_expert_url}"
)

PAYOUT_NOTIFY = (
    "Recipient ka this cycle! ₱{amount} sent to your registered Stellar account. "
    "Tx: {stellar_expert_url}"
)

# --- Help / status / fallback ---------------------------------------------------

GARBAGE_FALLBACK = "Hindi ko gets. Try: JOIN <code> · PAY · STATUS · HELP"

HELP_MENU = (
    "DAMAY commands:\n"
    "• JOIN <code> — sumali sa round\n"
    "• PAY — mag-contribute\n"
    "• STATUS — check current round\n"
    "• HELP — this menu"
)

STATUS_LINE = (
    "Round: {round_name}\n"
    "Cycle: {cycle}/{total}\n"
    "Status: {member_status}\n"
    "Next payout: {next_recipient}"
)

# --- Error / edge-case copy -----------------------------------------------------

UNKNOWN_MEMBER = (
    "Hi! You're not in any DAMAY round yet. "
    "Ask the organizer to invite you."
)

INVALID_JOIN_CODE = "Invalid code. Double-check with your organizer."

NO_ACTIVE_CYCLE = (
    "Walang active cycle ngayon. We'll text you once it's time to contribute."
)

ALREADY_CONTRIBUTED = (
    "Naka-contribute ka na for this cycle. Salamat! Antayin mo na lang ang next signal."
)

NOT_IN_ACTIVE_ROUND = (
    "Wala kang active round sa DAMAY. Type HELP para sa commands."
)
