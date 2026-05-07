ALTER TABLE player ADD COLUMN IF NOT EXISTS login VARCHAR(100) UNIQUE;
ALTER TABLE player ADD COLUMN IF NOT EXISTS password VARCHAR(100);
ALTER TABLE player ADD COLUMN IF NOT EXISTS last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE player ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

UPDATE player SET login = nickname, password = 'password123' WHERE login IS NULL;

CREATE OR REPLACE PROCEDURE calculate_triangle_params(
    a NUMERIC, b NUMERIC, angle_deg NUMERIC,
    OUT side_c NUMERIC, OUT area NUMERIC
) AS $$
DECLARE
    angle_rad NUMERIC := radians(angle_deg);
BEGIN
    side_c := sqrt(a^2 + b^2 - 2 * a * b * cos(angle_rad));
    area := 0.5 * a * b * sin(angle_rad);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE get_triangle_type_full(
    a NUMERIC, b NUMERIC, c NUMERIC, 
    OUT result_text TEXT
) AS $$
DECLARE
    sides NUMERIC[];
    max_sq NUMERIC;
    sum_sq NUMERIC;
BEGIN
    SELECT array_agg(x ORDER BY x) INTO sides FROM unnest(ARRAY[a, b, c]) AS x;
    IF (sides[1] + sides[2]) <= sides[3] THEN 
        result_text := 'Не треугольник';
        RETURN;
    END IF;

    result_text := CASE 
        WHEN sides[1] = sides[2] AND sides[2] = sides[3] THEN 'Равносторонний'
        WHEN sides[1] = sides[2] OR sides[2] = sides[3] OR sides[1] = sides[3] THEN 'Равнобедренный'
        ELSE 'Разносторонний'
    END;

    max_sq := sides[3]^2;
    sum_sq := sides[1]^2 + sides[2]^2;

    IF abs(max_sq - sum_sq) < 0.001 THEN result_text := result_text || ', прямоугольный';
    ELSIF max_sq > sum_sq THEN result_text := result_text || ', тупоугольный';
    ELSE result_text := result_text || ', остроугольный';
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_max_sum_base(n INT) RETURNS INT AS $$
DECLARE
    max_sum INT := -1;
    best_base INT := 2;
    curr_sum INT;
    temp_n INT;
BEGIN
    FOR b IN 2..9 LOOP
        curr_sum := 0; temp_n := n;
        WHILE temp_n > 0 LOOP
            curr_sum := curr_sum + (temp_n % b);
            temp_n := temp_n / b;
        END LOOP;
        IF curr_sum > max_sum THEN
            max_sum := curr_sum; best_base := b;
        END IF;
    END LOOP;
    RETURN best_base;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE archive_inactive_players() AS $$
BEGIN
    UPDATE player 
    SET is_active = FALSE 
    WHERE last_login < (NOW() - INTERVAL '1 month') AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION auth_player(p_login TEXT, p_password TEXT) RETURNS INT AS $$
DECLARE
    pid INT;
BEGIN
    SELECT player_id INTO pid FROM player 
    WHERE login = p_login AND password = p_password AND is_active = TRUE;
    
    IF pid IS NOT NULL THEN
        UPDATE player SET last_login = NOW() WHERE player_id = pid;
    END IF;
    
    RETURN pid;
END;
$$ LANGUAGE plpgsql;
