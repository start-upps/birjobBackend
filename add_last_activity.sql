-- Add last_activity column to device_users table
ALTER TABLE iosapp.device_users 
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP WITH TIME ZONE;

-- Create index for performance on last_activity queries
CREATE INDEX IF NOT EXISTS idx_device_users_last_activity 
ON iosapp.device_users(last_activity);

-- Update existing users to have initial last_activity (using created_at)
UPDATE iosapp.device_users 
SET last_activity = created_at 
WHERE last_activity IS NULL;