-- =========================================================
-- SERVERS
-- Stores server-specific economy configuration.
-- =========================================================

CREATE TABLE servers (
    guild_id INTEGER PRIMARY KEY,

    starting_allowance INTEGER NOT NULL DEFAULT 1000
        CHECK (starting_allowance >= 0),

    interest_rate_bps INTEGER NOT NULL DEFAULT 500
        CHECK (interest_rate_bps >= 0),

    max_loan_balance INTEGER NOT NULL DEFAULT 5000
        CHECK (max_loan_balance >= 0),

    created_at TEXT NOT NULL
);


-- =========================================================
-- PLAYERS
-- Stores registered players and their bank balances.
-- A player can have a separate account in each server.
-- =========================================================

CREATE TABLE players (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    balance INTEGER NOT NULL DEFAULT 0
        CHECK (balance >= 0),

    registered_at TEXT NOT NULL,

    PRIMARY KEY (guild_id, user_id),

    FOREIGN KEY (guild_id)
        REFERENCES servers(guild_id)
        ON DELETE RESTRICT
);


-- =========================================================
-- LOANS
-- Stores individual loans belonging to players.
-- Multiple loans per player are supported.
-- =========================================================

CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    original_principal INTEGER NOT NULL
        CHECK (original_principal > 0),

    remaining_principal INTEGER NOT NULL
        CHECK (
            remaining_principal >= 0
            AND remaining_principal <= original_principal
        ),

    accrued_interest INTEGER NOT NULL DEFAULT 0
        CHECK (accrued_interest >= 0),

    interest_rate_bps INTEGER NOT NULL
        CHECK (interest_rate_bps >= 0),

    created_at TEXT NOT NULL,
    last_interest_at TEXT NOT NULL,

    paid_at TEXT,

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paid')),

    FOREIGN KEY (guild_id, user_id)
        REFERENCES players(guild_id, user_id)
        ON DELETE RESTRICT
);


-- =========================================================
-- TRANSACTIONS
-- Records financial activity for auditing.
-- Sender and recipient are optional depending on the
-- transaction type.
-- =========================================================

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id INTEGER NOT NULL,

    from_user_id INTEGER,
    to_user_id INTEGER,

    actor_user_id INTEGER,

    transaction_type TEXT NOT NULL,

    amount INTEGER NOT NULL
        CHECK (amount > 0),

    reason TEXT NOT NULL DEFAULT '',

    created_at TEXT NOT NULL,

    reference_id TEXT,

    CHECK (
        from_user_id IS NOT NULL
        OR to_user_id IS NOT NULL
    ),

    CHECK (
        from_user_id IS NULL
        OR to_user_id IS NULL
        OR from_user_id != to_user_id
    ),

    FOREIGN KEY (guild_id)
        REFERENCES servers(guild_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (guild_id, from_user_id)
        REFERENCES players(guild_id, user_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (guild_id, to_user_id)
        REFERENCES players(guild_id, user_id)
        ON DELETE RESTRICT
);


-- =========================================================
-- INDEXES
-- Improve lookup performance for common queries.
-- =========================================================

CREATE INDEX idx_loans_player
    ON loans(guild_id, user_id);

CREATE INDEX idx_transactions_player
    ON transactions(guild_id, from_user_id, to_user_id);

CREATE INDEX idx_transactions_created_at
    ON transactions(guild_id, created_at);
