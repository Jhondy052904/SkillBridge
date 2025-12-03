-- Add unique constraints to prevent future duplicates
-- Execute these commands in your Supabase SQL editor

-- Add unique constraint on resident table email column
ALTER TABLE resident ADD CONSTRAINT unique_resident_email UNIQUE (email);

-- Add unique constraint on registration_official table email column (if exists)
-- ALTER TABLE registration_official ADD CONSTRAINT unique_official_email UNIQUE (email);

-- Create unique index on email for better performance
CREATE UNIQUE INDEX IF NOT EXISTS idx_resident_email_unique ON resident(email);

