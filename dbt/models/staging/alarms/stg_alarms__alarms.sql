select
    rid as alarm_id,
    data as city,
    TIMESTAMP(alertDate, 'Asia/Jerusalem') as alerted_at,
    category,
    category_desc,
    matrix_id,
    ingested_at

from {{ source('alarms', 'raw_alerts') }}
WHERE category NOT IN (13, 14)
