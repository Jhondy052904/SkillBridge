from django.db import models

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
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]

    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default="Pending")

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
    skills = models.TextField(blank=True, null=True) 
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


# ----------------------------------------
# Skills & Certifications
# ----------------------------------------
class Skill(models.Model):
    skill_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.skill_name


class ResidentSkill(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
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
