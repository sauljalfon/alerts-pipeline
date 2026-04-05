select
    cityId as city_id,
    name,
    population,
    CAST(
        REGEXP_EXTRACT(location, r'\(([^,]+),')
    AS FLOAT64) as latitude,

    CAST(
        REGEXP_EXTRACT(location, r',\s*([^\)]+)\)')
    AS FLOAT64) as longitude,

    createdAt as created_at,
    updatedAt as updated_at

from {{ ref('cities') }}
