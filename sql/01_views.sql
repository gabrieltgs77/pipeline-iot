-- Views do pipeline IoT (tabela base: temperature_readings)
-- Colunas: log_id, room_id, noted_at, temperature, location ('In' / 'Out')

-- 1) Temperatura média por dispositivo (sensor interno e externo da sala)
CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT
    room_id || ' - ' || location                 AS device_id,
    ROUND(AVG(temperature)::numeric, 2)::float   AS avg_temp,
    COUNT(*)                                     AS total_leituras
FROM temperature_readings
GROUP BY room_id, location;

-- 2) Quantidade de leituras por hora do dia (0 a 23)
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT
    EXTRACT(HOUR FROM noted_at)::int AS hora,
    COUNT(*)                         AS contagem
FROM temperature_readings
GROUP BY EXTRACT(HOUR FROM noted_at)
ORDER BY hora;

-- 3) Temperaturas máxima, mínima e média por dia
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT
    noted_at::date                               AS data,
    MAX(temperature)                             AS temp_max,
    MIN(temperature)                             AS temp_min,
    ROUND(AVG(temperature)::numeric, 2)::float   AS temp_media
FROM temperature_readings
GROUP BY noted_at::date
ORDER BY data;
