from django.db import models
import uuid

# registration/models.py
from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    link_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"

# ----------------------------------------
# User Accounts
# ----------------------------------------
class UserAccount(models.Model):
    ROLE_CHOICES = [
        ('Resident', 'Resident'),
        ('Official', 'Official'),
        ('Admin', 'Admin'),
    ]
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"

# ----------------------------------------
# Residents
# ----------------------------------------
class Resident(models.Model):
    EMPLOYMENT_CHOICES = [
        ('Employed', 'Employed'),
        ('Unemployed', 'Unemployed'),
        ('Self-employed', 'Self-employed'),
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    VERIFICATION_STATUS = [
        ('Pending Verification', 'Pending Verification'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]
    CURRENT_STATUS_CHOICES = [
        ('Hired', 'Hired'),
        ('Not Hired', 'Not Hired'),
        ('Training', 'Training'),
    ]

    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default="Pending Verification")
    current_status = models.CharField(max_length=20, choices=CURRENT_STATUS_CHOICES, default='Not Hired')

    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default="Unemployed")
    # Many-to-many relationship is stored in the Supabase `resident_skills`
    # table which references the Supabase `resident` table. Rather than a
    # direct Django-managed ManyToManyField (which would expect the join
    # table to point at this local `registration_resident` table), expose a
    # property-based API that resolves via the SupabaseResident mapping.

    def get_supabase_resident(self):
        """Return the SupabaseResident that corresponds to this local Resident (by email)."""
        try:
            return SupabaseResident.objects.filter(email=self.email).first()
        except Exception:
            return None

    def get_skills(self):
        """Return a Django QuerySet of Skill objects associated with this resident via SupabaseResident."""
        supa = self.get_supabase_resident()
        if not supa:
            return Skill.objects.none()
        return Skill.objects.filter(residentskill__resident=supa)

    def set_skills(self, skill_qs):
        """Set skills for this resident by updating rows in `resident_skills`.

        `skill_qs` may be an iterable of Skill instances or their ids.
        """
        supa = self.get_supabase_resident()
        if not supa:
            raise ValueError('No SupabaseResident found for this Resident (by email)')

        # Normalize to Skill instances
        from django.db import connection
        skill_ids = []
        for s in skill_qs:
            if isinstance(s, Skill):
                skill_ids.append(str(s.id))
            else:
                skill_ids.append(str(s))

        # Delete existing links
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM resident_skills WHERE resident_id = %s;', [supa.id])

        # Insert new links
        import uuid
        from django.utils import timezone
        with connection.cursor() as cursor:
            for sid in skill_ids:
                nid = str(uuid.uuid4())
                cursor.execute(
                    'INSERT INTO resident_skills (id, resident_id, skill_id, created_at) VALUES (%s, %s, %s, %s);',
                    [nid, supa.id, sid, timezone.now()]
                )

    # Expose `skills` as a property for compatibility with existing code
    @property
    def skills(self):
        return self.get_skills()

    @skills.setter
    def skills(self, value):
        return self.set_skills(value)
    proof_residency = models.BinaryField(blank=True, null=True) 
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# ----------------------------------------
# Barangay Officials / Admins
# ----------------------------------------
class Official(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    position = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.name} ({self.position})"


# Represents the Supabase resident table (source-of-truth). This model is
# read/write-safe in Django only when mapping operations use Supabase ids.
class SupabaseResident(models.Model):
    id = models.IntegerField(primary_key=True, db_column='id')
    email = models.EmailField(db_column='email')
    first_name = models.CharField(max_length=100, blank=True, null=True, db_column='first_name')
    last_name = models.CharField(max_length=100, blank=True, null=True, db_column='last_name')

    class Meta:
        db_table = 'resident'
        managed = False

    def __str__(self):
        return f"{self.email}"


# ----------------------------------------
# Skills & Certifications
# ----------------------------------------
class Skill(models.Model):
    """Represents rows in the existing `skill_list` table.

    The project already has a `skill_list` table (with a UUID primary key)
    so this model maps to that table and is marked `managed = False` to avoid
    Django attempting to create or modify it via migrations.
    """
    # Map to actual Supabase/Postgres column names (observed: SkillID, SkillName, Description)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='SkillID')
    skill_name = models.CharField(max_length=100, db_column='SkillName')
    description = models.TextField(blank=True, db_column='Description')

    class Meta:
        db_table = 'skill_list'
        managed = False

    def __str__(self):
        return self.skill_name


class ResidentSkill(models.Model):
    """Maps to the existing `resident_skill_list` join table.

    This model is also marked `managed = False` because the table already
    exists in the database. Fields map to the existing column names.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='id')
    # resident_skills references the Supabase `resident` table. Use SupabaseResident
    # (managed=False) as the FK target so ORM queries align with DB FKs.
    resident = models.ForeignKey('SupabaseResident', on_delete=models.CASCADE, db_column='resident_id')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, db_column='skill_id')
    created_at = models.DateTimeField(null=True, blank=True, db_column='created_at')

    class Meta:
        # Actual table name in Supabase/Postgres is `resident_skills` (confirmed via inspect_table)
        db_table = 'resident_skills'
        managed = False
        unique_together = ('resident', 'skill')

    def __str__(self):
        return f"{self.resident} - {self.skill}"


class Certification(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    certification_name = models.CharField(max_length=150)
    issuer = models.CharField(max_length=150, blank=True)
    date_issued = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.certification_name} ({self.resident})"


# ----------------------------------------
# Jobs & Applications
# ----------------------------------------
class Job(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    posted_by = models.ForeignKey(Official, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Open")

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Hired', 'Hired'),
    ]

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    date_applied = models.DateTimeField(auto_now_add=True)
    application_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")

    def __str__(self):
        return f"{self.resident} → {self.job} ({self.application_status})"


# ----------------------------------------
# Trainings & Participation
# ----------------------------------------
class Training(models.Model):
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Completed', 'Completed'),
    ]

    training_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(Official, on_delete=models.CASCADE)
    date_scheduled = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Upcoming")

    def __str__(self):
        return self.training_name


class TrainingParticipation(models.Model):
    ATTENDANCE_CHOICES = [
        ('Registered', 'Registered'),
        ('Attended', 'Attended'),
        ('Completed', 'Completed'),
    ]

    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    date_registered = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(max_length=15, choices=ATTENDANCE_CHOICES, default="Registered")

    def __str__(self):
        return f"{self.resident} → {self.training} ({self.attendance_status})"

# ----------------------------------------
# Events
# ----------------------------------------
class Event(models.Model):
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Completed', 'Completed'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    date_event = models.DateField(null=True, blank=True)
    posted_by = models.ForeignKey(Official, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Upcoming")
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
