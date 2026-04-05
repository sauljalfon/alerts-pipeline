with alarms as (
    select * from {{ ref('stg_alarms__alarms') }}
),

cities as (
    select * from {{ ref('stg_cities__cities') }}
),

final as (
    select
        -- keys
        alarms.alarm_id,

        -- alarm attributes
        alarms.city,
        alarms.category,
        alarms.category_desc,
        alarms.matrix_id,
        alarms.alerted_at,
        alarms.ingested_at,

        -- time dimensions
        DATE(alarms.alerted_at, 'Asia/Jerusalem') as alert_date,
        TIME(alarms.alerted_at, 'Asia/Jerusalem') as alert_time,
        EXTRACT(hour from alarms.alerted_at at time zone 'Asia/Jerusalem') as alert_hour,
        EXTRACT(dayofweek from alarms.alerted_at at time zone 'Asia/Jerusalem') as alert_day_of_week,

        -- city enrichment
        cities.city_id,
        cities.population,
        cities.latitude,
        cities.longitude

    from alarms
    left join cities
        on alarms.city = cities.name
)

select * from final
