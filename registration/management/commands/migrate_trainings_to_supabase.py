from django.core.management.base import BaseCommand
from registration.models import Training
from dotenv import load_dotenv
import os
from supabase import create_client


class Command(BaseCommand):
    help = "Migrate Django Training rows into Supabase and update training_attendees refs"

    def handle(self, *args, **options):
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            self.stderr.write("Supabase environment variables missing. Set SUPABASE_URL and SUPABASE_KEY in .env")
            return

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        trainings = Training.objects.all()
        if not trainings:
            self.stdout.write("No Django Training records found. Nothing to migrate.")
            return

        mapping = []

        for t in trainings:
            old_id = str(t.id)
            self.stdout.write(f"Processing training {old_id}: {t.training_name}")

            try:
                # Try to find an existing Supabase row by training_name + date
                query = supabase.table("training").select("*")
                # Use ilike on name to be tolerant, match date_scheduled exactly if available
                if t.date_scheduled:
                    resp = query.ilike("training_name", t.training_name).eq("date_scheduled", str(t.date_scheduled)).execute()
                else:
                    resp = query.ilike("training_name", t.training_name).execute()

                if resp.data:
                    new_id = resp.data[0].get("id")
                    self.stdout.write(f"  Found existing Supabase training -> {new_id}")
                else:
                    payload = {
                        "training_name": t.training_name,
                        "description": t.description,
                        "date_scheduled": t.date_scheduled.isoformat() if t.date_scheduled else None,
                        "location": getattr(t, "location", None),
                        "status": getattr(t, "status", None),
                        # created_by: best-effort: use organizer name or None
                        "created_by": getattr(t.organizer, "name", None) if getattr(t, "organizer", None) else None,
                    }
                    insert = supabase.table("training").insert(payload).execute()
                    if insert.data:
                        new_id = insert.data[0].get("id")
                        self.stdout.write(f"  Inserted Supabase training -> {new_id}")
                    else:
                        self.stderr.write(f"  Failed to insert training {old_id}: no data returned")
                        continue

                # Update any training_attendees that reference the old Django id (likely stored as string)
                try:
                    upd = supabase.table("training_attendees").update({"training_id": new_id}).eq("training_id", old_id).execute()
                    # Some Supabase clients return array of rows updated, others return None
                    count = len(upd.data) if getattr(upd, 'data', None) else 0
                    if count:
                        self.stdout.write(f"  Updated {count} attendee(s) from {old_id} -> {new_id}")
                    else:
                        self.stdout.write(f"  No attendees found referencing {old_id}")
                except Exception as e:
                    self.stderr.write(f"  Error updating attendees for {old_id}: {e}")

                mapping.append((old_id, new_id))

            except Exception as e:
                self.stderr.write(f"  Error migrating training {old_id}: {e}")

        self.stdout.write("\nMigration completed. Mappings:")
        for old, new in mapping:
            self.stdout.write(f"  {old} -> {new}")
