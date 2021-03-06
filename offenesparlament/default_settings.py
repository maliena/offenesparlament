DEBUG = True
SECRET_KEY = 'no'
CACHE = True
CACHE_AGE = 84600/2

SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/parlament2'
SOLR_URL = 'http://127.0.0.1:8983/solr/parlament'
ETL_URL = 'postgresql://localhost/parlament_etl'
FLATPAGES_ROOT = 'pages'

NOMENKLATURA_PERSONS_DATASET = 'offenesparlament'
NOMENKLATURA_TYPES_DATASET = 'offenesparlament-typen'
NOMENKLATURA_VOTES_DATASET = 'offenesparlament-votes'
NOMENKLATURA_STAGE_DATASET = 'offenesparlament-stand'
NOMENKLATURA_PRELOAD = True
