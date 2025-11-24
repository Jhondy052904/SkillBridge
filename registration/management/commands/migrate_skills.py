from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import os
from dotenv import load_dotenv

from registration.models import Skill, Resident, ResidentSkill
from django.db import connection
import uuid

try:
    from supabase import create_client
except Exception:
    create_client = None


class Command(BaseCommand):
    help = 'Migrate legacy skills (CSV) from Supabase residents into Skill and ResidentSkill tables.'

    def add_arguments(self, parser):
        parser.add_argument('--source', choices=['supabase'], default='supabase', help='Source to read legacy skills from (default: supabase)')
        parser.add_argument('--commit', action='store_true', help='Actually write changes to DB. Without --commit the command runs as dry-run.')
        parser.add_argument('--create-residents', action='store_true', help='Create missing Django Resident rows when found in Supabase.')

    def handle(self, *args, **options):
        source = options['source']
        do_commit = options['commit']
        create_residents = options['create_residents']

        load_dotenv()
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

        if source != 'supabase':
            raise CommandError('Currently only supabase source is supported.')

        if create_client is None:
            raise CommandError('supabase package is not installed in this environment.')

        if not SUPABASE_URL or not SUPABASE_KEY:
            raise CommandError('SUPABASE_URL and SUPABASE_KEY must be set in environment.')

        sb = create_client(SUPABASE_URL, SUPABASE_KEY)

        self.stdout.write('Fetching residents from Supabase...')
        try:
            resp = sb.table('resident').select('id,email,first_name,last_name,skills').execute()
            rows = resp.data or []
        except Exception as e:
            raise CommandError(f'Error fetching residents from Supabase: {e}')

        total = len(rows)
        self.stdout.write(f'Found {total} resident records to examine.')

        created_skills = 0
        created_links = 0
        skipped = 0

        for i, r in enumerate(rows, start=1):
            email = (r.get('email') or '').strip()
            legacy_skills = r.get('skills') or ''
            if not email:
                self.stdout.write(f'[{i}/{total}] skipping resident without email')
                skipped += 1
                continue

            # Try to find a Django Resident with this email
            resident = Resident.objects.filter(email=email).first()
            if not resident:
                if create_residents and do_commit:
                    # Create a minimal Resident using available fields
                    first = r.get('first_name') or email.split('@')[0]
                    last = r.get('last_name') or 'Resident'
                    resident = Resident.objects.create(email=email, first_name=first, last_name=last, date_registered=timezone.now())
                    self.stdout.write(f'[{i}/{total}] created Resident for {email}')
                else:
                    self.stdout.write(f'[{i}/{total}] no Django resident for {email} (skipping)')
                    skipped += 1
                    continue

            # Parse legacy CSV (comma-separated names)
            skill_names = [s.strip() for s in legacy_skills.split(',') if s.strip()]
            if not skill_names:
                self.stdout.write(f'[{i}/{total}] no skills for {email}')
                continue

            for name in skill_names:
                # Find or create skill by name (case-insensitive)
                skill = Skill.objects.filter(skill_name__iexact=name).first()
                if not skill:
                    if do_commit:
                        skill = Skill.objects.create(skill_name=name, description='Migrated from legacy skills')
                        created_skills += 1
                        self.stdout.write(f'  created skill: {name}')
                    else:
                        self.stdout.write(f'  would create skill: {name}')
                        continue
                # Create ResidentSkill link if not exists
                # The resident_skills table references the Supabase `resident` table (resident.id)
                # We will use the Supabase resident id from the fetched row (r['id']) when inserting
                supa_resident_id = r.get('id')

                # Check existing link directly in resident_skills table
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM resident_skills WHERE resident_id = %s AND skill_id = %s LIMIT 1;",
                        [supa_resident_id, str(skill.id)]
                    )
                    exists_row = cursor.fetchone()

                if exists_row:
                    self.stdout.write(f'  link exists: supa_resident {supa_resident_id} -> {skill.skill_name}')
                else:
                    if do_commit:
                        # Insert directly into resident_skills using the supabase resident id
                        new_id = str(uuid.uuid4())
                        created_at_val = timezone.now()
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO resident_skills (id, resident_id, skill_id, created_at) VALUES (%s, %s, %s, %s);",
                                [new_id, supa_resident_id, str(skill.id), created_at_val]
                            )
                        created_links += 1
                        self.stdout.write(f'  linked: supa_resident {supa_resident_id} -> {skill.skill_name}')
                    else:
                        self.stdout.write(f'  would link: supa_resident {supa_resident_id} -> {skill.skill_name}')

        self.stdout.write('---')
        self.stdout.write(f'Created skills: {created_skills}')
        self.stdout.write(f'Created resident-skill links: {created_links}')
        self.stdout.write(f'Skipped residents: {skipped}')
        if not do_commit:
            self.stdout.write('Dry-run complete. Rerun with --commit to apply changes.')
