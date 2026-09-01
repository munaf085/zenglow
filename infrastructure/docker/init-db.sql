-- Create test database alongside the main one
SELECT 'CREATE DATABASE zenglow_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'zenglow_test')\gexec

GRANT ALL PRIVILEGES ON DATABASE zenglow_test TO zenglow;
