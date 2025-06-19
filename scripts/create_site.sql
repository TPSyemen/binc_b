-- Check if the django_site table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='django_site';

-- Insert or replace the default site
INSERT OR REPLACE INTO django_site (id, domain, name) VALUES (1, 'binc-b-1.onrender.com', 'Best In Click');
