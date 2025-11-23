from django.core.management.base import BaseCommand
from supabase import create_client
import os
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Create resident_certificates table in Supabase"

    def handle(self, *args, **options):
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            self.stdout.write(self.style.ERROR("Missing SUPABASE_URL or SUPABASE_KEY in environment"))
            return

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # SQL to create the table:
        # CREATE TABLE resident_certificates (
        #     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        #     resident_email VARCHAR(255) NOT NULL,
        #     certificate_name VARCHAR(255) NOT NULL,
        #     file_url TEXT NOT NULL,
        #     upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        # );

        self.stdout.write("Please create the resident_certificates table manually in Supabase with the following SQL:")
        self.stdout.write("""
CREATE TABLE resident_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resident_email VARCHAR(255) NOT NULL,
    certificate_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""")

        # Also create the storage bucket
        try:
            buckets = supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if 'resident_certificates' not in bucket_names:
                supabase.storage.create_bucket('resident_certificates', {'public': True})
                self.stdout.write(self.style.SUCCESS("Created 'resident_certificates' bucket"))
            else:
                self.stdout.write("Bucket 'resident_certificates' already exists")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating bucket: {e}"))