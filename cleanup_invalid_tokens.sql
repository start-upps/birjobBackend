-- Remove invalid device tokens and users from the database

-- QUICK CLEANUP COMMANDS (run these individually if needed):

-- 1. Remove users with no email AND no keywords:
-- DELETE FROM iosapp.users WHERE (email IS NULL OR email = '') AND (keywords = '[]' OR keywords IS NULL);

-- 2. Remove specific problematic device tokens:
-- DELETE FROM iosapp.device_tokens WHERE device_id IN ('1C1108D7-BBAD-4B0F-89F7-F55624300CE1', 'B71F57C9-A1B4-41AC-9AD9-3E1F284AFDEA');

-- 3. Remove all placeholder tokens:
-- DELETE FROM iosapp.device_tokens WHERE device_token LIKE '%placeholder%' OR device_token LIKE '%chars_min%';

-- FULL CLEANUP SCRIPT:

-- First, let's see what we're going to delete
SELECT 
    id, 
    device_id, 
    device_token, 
    is_active,
    user_id
FROM iosapp.device_tokens 
WHERE 
    device_token LIKE '%placeholder%' 
    OR device_token LIKE '%1C1108D7%'
    OR device_token LIKE '%B71F57C9%'
    OR device_token LIKE '%B6BDBB52%'
    OR device_token LIKE '%0B43E135%'
    OR device_token LIKE '%chars_min%'
    OR device_token LIKE '%xxxx%'
    OR LENGTH(device_token) != 64
    OR device_token ~ '[^0-9a-fA-F]'; -- Contains non-hex characters

-- Now delete the invalid tokens
DELETE FROM iosapp.device_tokens 
WHERE 
    device_token LIKE '%placeholder%' 
    OR device_token LIKE '%1C1108D7%'
    OR device_token LIKE '%B71F57C9%'
    OR device_token LIKE '%B6BDBB52%'
    OR device_token LIKE '%0B43E135%'
    OR device_token LIKE '%chars_min%'
    OR device_token LIKE '%xxxx%'
    OR LENGTH(device_token) != 64
    OR device_token ~ '[^0-9a-fA-F]'; -- Contains non-hex characters

-- Show remaining tokens after cleanup
SELECT 
    id, 
    device_id, 
    device_token, 
    is_active,
    user_id,
    registered_at
FROM iosapp.device_tokens 
ORDER BY registered_at DESC;

-- Clean up invalid users
-- First, let's see what invalid users we have
SELECT 
    id, 
    email, 
    keywords, 
    notifications_enabled,
    created_at
FROM iosapp.users 
WHERE 
    email IS NULL 
    OR email = ''
    OR keywords = '[]'
    OR keywords IS NULL;

-- Delete users with no email AND no keywords (completely useless entries)
DELETE FROM iosapp.users 
WHERE 
    (email IS NULL OR email = '') 
    AND (keywords = '[]' OR keywords IS NULL);

-- Delete users who have no active device tokens
DELETE FROM iosapp.users 
WHERE id NOT IN (
    SELECT DISTINCT user_id 
    FROM iosapp.device_tokens 
    WHERE user_id IS NOT NULL AND is_active = true
);

-- Show remaining valid users after cleanup
SELECT 
    id, 
    email, 
    keywords, 
    notifications_enabled,
    created_at
FROM iosapp.users 
ORDER BY created_at DESC;