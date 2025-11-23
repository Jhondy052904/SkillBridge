from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os
from supabase import create_client

class Command(BaseCommand):
    help = "Create training_certificates table in Supabase"

    def handle(self, *args, **options):
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            self.stderr.write("Supabase environment variables missing.")
            return

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Note: Supabase Python client does not support DDL operations like CREATE TABLE.
        # This command is a placeholder. You need to create the table manually in Supabase dashboard or via SQL.
        # SQL to create the table:
        # CREATE TABLE training_certificates (
        #     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        #     resident_id UUID NOT NULL,
        #     training_id BIGINT NOT NULL,
        #     certificate_url TEXT NOT NULL,
        #     file_type VARCHAR(10) NOT NULL,
        #     file_name TEXT NOT NULL,
        #     uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        # );

        self.stdout.write("Please create the training_certificates table manually in Supabase with the following SQL:")
        self.stdout.write("""
CREATE TABLE training_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resident_id UUID NOT NULL,
    training_id BIGINT NOT NULL,
    certificate_url TEXT NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_name TEXT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
        """)