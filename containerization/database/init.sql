-- Best runs of XArcanoid. One row is one finished game, not a user account.
CREATE TABLE scores (
    id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player     text NOT NULL CHECK (player ~ '^[A-Za-z0-9_]{3,20}$'),
    score      integer NOT NULL CHECK (score BETWEEN 0 AND 999999),
    level      integer NOT NULL CHECK (level BETWEEN 1 AND 9999),
    max_combo  integer NOT NULL CHECK (max_combo BETWEEN 0 AND 9999),
    difficulty text NOT NULL CHECK (difficulty IN ('standard', 'overdrive')),
    mode       text NOT NULL CHECK (mode IN ('campaign', 'survival')),
    played_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_scores_board ON scores (mode, player, score DESC);

INSERT INTO scores (player, score, level, max_combo, difficulty, mode) VALUES
    ('Corebreaker', 184320, 17, 42, 'overdrive', 'survival'),	
    ('FasterXaos',  147069, 11, 69, 'overdrive', 'survival'),
    ('NovaPaddle',  126540, 10, 28, 'standard',  'campaign'),
    ('Brickline',    98210,  8, 19, 'standard',  'survival'),
    ('NightArcade',  74330, 11, 15, 'overdrive', 'campaign'),
    ('AbyssMiss',    22150,  4,  7, 'standard',  'survival');
