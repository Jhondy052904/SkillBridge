from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'List all table names in the public schema of the current database.'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"
                )
                rows = cursor.fetchall()
            except Exception as e:
                raise CommandError(f'Error querying information_schema: {e}')

        if not rows:
            self.stdout.write(self.style.WARNING('No tables found in public schema.'))
            return

        self.stdout.write(self.style.SUCCESS('Tables in public schema:'))
        for (table_name,) in rows:
            self.stdout.write(f' - {table_name}')
