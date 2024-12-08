from sqlalchemy import DDL, event


def trigger_total_cost(Base):
    drop_total_cost_fn = DDL("""
        DROP FUNCTION IF EXISTS calculate_total_cost CASCADE;
    """)
    calculate_total_cost = DDL("""
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
    """)

    update_total_cost = DDL("""
        CREATE TRIGGER update_total_cost
        BEFORE UPDATE OF endtime ON transactions
        FOR EACH ROW
        WHEN (NEW.endtime IS DISTINCT FROM OLD.endtime)
        EXECUTE FUNCTION calculate_total_cost();
    """)

    event.listen(Base.metadata, "after_create", drop_total_cost_fn)
    event.listen(Base.metadata, "after_create", calculate_total_cost)
    event.listen(Base.metadata, "after_create", update_total_cost)
