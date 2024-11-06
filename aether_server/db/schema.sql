CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    stored_credentials VARCHAR(255) NOT NULL,
    is_landlord BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS computers (
    id SERIAL PRIMARY KEY,
    rate INT CHECK (rate >= 0),
    landlord_id INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    starttime TIMESTAMP NOT NULL,
    endtime TIMESTAMP,
    customer_id INT REFERENCES users(id) ON DELETE SET NULL,
    landlord_id INT REFERENCES users(id) ON DELETE SET NULL,
    computer_id INT REFERENCES computers(id) ON DELETE SET NULL,
    total_cost INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


DROP FUNCTION IF EXISTS calculate_total_cost CASCADE;

CREATE OR REPLACE FUNCTION calculate_total_cost() 
RETURNS TRIGGER AS $$
DECLARE
    computer_rate INT;
BEGIN
    SELECT rate INTO computer_rate FROM computers WHERE id = NEW.computer_id;
    IF NEW.endtime IS NOT NULL AND NEW.starttime IS NOT NULL THEN
        NEW.total_cost := EXTRACT(EPOCH FROM (NEW.endtime - NEW.starttime)) / 3600 * computer_rate;
    ELSE
        NEW.total_cost := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_total_cost
BEFORE UPDATE OF endtime ON transactions
FOR EACH ROW
WHEN (NEW.endtime IS DISTINCT FROM OLD.endtime)
EXECUTE FUNCTION calculate_total_cost();
