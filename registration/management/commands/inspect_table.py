from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Inspect table columns in the current database. Usage: python manage.py inspect_table <table_name>'

    def add_arguments(self, parser):
        parser.add_argument('table_name', type=str, help='Table name to inspect')

    def handle(self, *args, **options):
        table = options['table_name']
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position;",
                    [table]
                )
                rows = cursor.fetchall()
            except Exception as e:
                raise CommandError(f'Error querying information_schema: {e}')

        if not rows:
            self.stdout.write(self.style.WARNING(f'No columns found for table "{table}".'))
            return

        self.stdout.write(self.style.SUCCESS(f'Columns for table "{table}":'))
        for col_name, data_type, is_nullable in rows:
            self.stdout.write(f' - {col_name} ({data_type}) nullable={is_nullable}')
