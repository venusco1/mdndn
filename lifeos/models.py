from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class VisionConfig(models.Model):
    class Theme(models.TextChoices):
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"

    name = models.CharField(max_length=100, default="Vision 30")
    master_start = models.DateField(default="2026-10-06")
    master_deadline = models.DateField(default="2029-07-18")
    first_block_start = models.DateField(default="2026-10-15")
    master_vision = models.TextField(default="Build a stable, useful, credible life across all eight areas.")
    timezone_name = models.CharField(max_length=64, default="Asia/Kolkata")
    enable_mood_energy = models.BooleanField(default=True)
    theme = models.CharField(max_length=5, choices=Theme.choices, default=Theme.DARK)

    @classmethod
    def get_solo(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def day_number(self, date):
        if date < self.master_start or date > self.master_deadline:
            return None
        return (date - self.master_start).days + 1

    def days_remaining(self, date):
        return max(0, (self.master_deadline - date).days)

    def block_number_on(self, date):
        block = Block.objects.filter(start_date__lte=date, deadline__gte=date).order_by("number").first()
        return block

    def total_window_days(self):
        return (self.master_deadline - self.master_start).days + 1

    def planned_block_days(self):
        return sum((block.deadline - block.start_date).days + 1 for block in Block.objects.all())

    def __str__(self):
        return self.name


class Pillar(models.Model):
    class ScoringMethod(models.TextChoices):
        QUALITATIVE = "qualitative", "Qualitative evidence"
        NUMERIC = "numeric", "Pillar-specific numeric targets"
        CONSISTENCY = "consistency", "Practice consistency"
        CUSTOM = "custom", "Custom method"

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField(unique=True)
    description = models.TextField(blank=True)
    scoring_method = models.CharField(max_length=16, choices=ScoringMethod.choices, default=ScoringMethod.QUALITATIVE)
    scoring_notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Block(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    number = models.PositiveSmallIntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(10)])
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    deadline = models.DateField()
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    weekly_targets = models.TextField(blank=True)
    monthly_milestones = models.TextField(blank=True)
    definition_of_done = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)
    final_review = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    next_recommendations = models.TextField(blank=True)

    class Meta:
        ordering = ["number"]
        constraints = [models.CheckConstraint(condition=models.Q(deadline__gte=models.F("start_date")), name="block_deadline_after_start")]

    def __str__(self):
        return f"Block {self.number:02d} — {self.name}"

    @property
    def duration_days(self):
        return (self.deadline - self.start_date).days + 1

    def day_number(self, date):
        if not self.start_date <= date <= self.deadline:
            return None
        return (date - self.start_date).days + 1


class Stage(models.Model):
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="stages")
    number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    title = models.CharField(max_length=120)
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    syllabus = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    daily_practices = models.TextField(blank=True)
    weekly_milestones = models.TextField(blank=True)
    monthly_milestones = models.TextField(blank=True)
    completion_criteria = models.TextField(blank=True)
    evidence = models.TextField(blank=True)
    completed_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["pillar__order", "number"]
        constraints = [models.UniqueConstraint(fields=["pillar", "number"], name="unique_pillar_stage_number")]

    def __str__(self):
        return f"{self.pillar.name} · Stage {self.number:02d}"


class BlockPillarMission(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="pillar_missions")
    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="block_missions")
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="block_missions")
    mission = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    daily_actions = models.TextField(blank=True)
    weekly_targets = models.TextField(blank=True)
    monthly_milestones = models.TextField(blank=True)
    definition_of_done = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Block.Status.choices, default=Block.Status.PLANNED)
    review = models.TextField(blank=True)

    class Meta:
        ordering = ["pillar__order"]
        constraints = [
            models.UniqueConstraint(fields=["block", "pillar"], name="unique_block_pillar_mission"),
            models.UniqueConstraint(fields=["block", "stage"], name="unique_block_stage_mission"),
        ]

    def __str__(self):
        return f"{self.block} · {self.pillar.name}"


class MeasurableTarget(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        ACHIEVED = "achieved", "Achieved (reviewed)"
        DEFERRED = "deferred", "Deferred"

    title = models.CharField(max_length=180)
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, related_name="targets", null=True, blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="targets", null=True, blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, related_name="targets", null=True, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    target_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completion_criteria = models.TextField(blank=True)
    evidence = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NOT_STARTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "id"]

    def __str__(self):
        return self.title

    @property
    def progress_percent(self):
        if self.target_value is None or self.target_value <= 0 or self.current_value is None:
            return None
        return min(100, max(0, float(self.current_value / self.target_value * 100)))


class Milestone(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="milestones", null=True, blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="milestones", null=True, blank=True)
    title = models.CharField(max_length=180)
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    completed_at = models.DateField(null=True, blank=True)
    evidence = models.TextField(blank=True)

    class Meta:
        ordering = ["due_date", "id"]

    def __str__(self):
        return self.title


class Goal(models.Model):
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="goals", null=True, blank=True)
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, related_name="goals", null=True, blank=True)
    target = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    current = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    completion_criteria = models.TextField(blank=True)
    evidence = models.TextField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    completed_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["deadline", "id"]

    def __str__(self):
        return self.title

    @property
    def progress_percent(self):
        if self.target is None or self.target <= 0 or self.current is None:
            return None
        return min(100, max(0, float(self.current / self.target * 100)))


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="tasks", null=True, blank=True)
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, related_name="tasks", null=True, blank=True)
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, related_name="tasks", null=True, blank=True)
    completed_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "-priority", "id"]

    def __str__(self):
        return self.title


class Habit(models.Model):
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="habits", null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class HabitCheckIn(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="checkins")
    date = models.DateField(default=timezone.localdate)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["habit", "date"], name="unique_habit_checkin_date")]
        ordering = ["-date"]


class PillarDailyLog(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PARTIAL = "partial", "Partially completed"
        NOT_COMPLETED = "not_completed", "Not completed"

    pillar = models.ForeignKey(Pillar, on_delete=models.CASCADE, related_name="daily_logs")
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NOT_COMPLETED)
    reflection = models.TextField(blank=True)
    outcome_note = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["pillar", "date"], name="unique_pillar_daily_log")]
        ordering = ["pillar__order"]


class DailyPriority(models.Model):
    date = models.DateField(default=timezone.localdate)
    rank = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    title = models.CharField(max_length=180)
    completed = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["date", "rank"], name="unique_daily_priority_rank")]
        ordering = ["rank"]


class DailyReview(models.Model):
    class Mood(models.TextChoices):
        CALM = "calm", "Calm"
        FOCUSED = "focused", "Focused"
        GRATEFUL = "grateful", "Grateful"
        TIRED = "tired", "Tired"
        STRESSED = "stressed", "Stressed"

    date = models.DateField(unique=True, default=timezone.localdate)
    mood = models.CharField(max_length=12, choices=Mood.choices, blank=True)
    energy = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    execution_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    evening_reflection = models.TextField(blank=True)
    wins = models.TextField(blank=True)
    improvement = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]


class Review(models.Model):
    class Kind(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        BLOCK = "block", "Block"

    kind = models.CharField(max_length=8, choices=Kind.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    block = models.ForeignKey(Block, on_delete=models.SET_NULL, related_name="reviews", null=True, blank=True)
    eight_pillar_performance = models.TextField(blank=True)
    target_progress = models.TextField(blank=True)
    wins = models.TextField(blank=True)
    problems = models.TextField(blank=True)
    missed_commitments = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    trends = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    risks = models.TextField(blank=True)
    next_milestones = models.TextField(blank=True)
    target_evaluation = models.TextField(blank=True)
    evidence = models.TextField(blank=True)
    completed_missions = models.TextField(blank=True)
    incomplete_missions = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    next_recommendations = models.TextField(blank=True)
    execution_consistency = models.TextField(blank=True)
    outcome_progress = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_start", "kind"]
        constraints = [models.UniqueConstraint(fields=["kind", "period_start", "block"], name="unique_period_review")]

    def __str__(self):
        return f"{self.get_kind_display()} review · {self.period_start}"


class JournalEntry(models.Model):
    date = models.DateField(default=timezone.localdate)
    title = models.CharField(max_length=180, blank=True)
    mood = models.CharField(max_length=32, blank=True)
    text = models.TextField()
    decision = models.TextField(blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="journal_entries", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.title or f"Journal · {self.date}"


class ArchiveEntry(models.Model):
    class Kind(models.TextChoices):
        ACHIEVEMENT = "achievement", "Achievement"
        REVIEW = "review", "Review"
        MILESTONE = "milestone", "Milestone"
        MEMORY = "memory", "Memory"

    date = models.DateField(default=timezone.localdate)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.ACHIEVEMENT)
    title = models.CharField(max_length=180)
    text = models.TextField(blank=True)
    pillar = models.ForeignKey(Pillar, on_delete=models.SET_NULL, related_name="archive_entries", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.title


class StageReview(models.Model):
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="reviews")
    reviewed_at = models.DateField(default=timezone.localdate)
    evaluation = models.TextField(blank=True)
    evidence = models.TextField(blank=True)
    lessons = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    class Meta:
        ordering = ["-reviewed_at"]


class ImportBatch(models.Model):
    checksum = models.CharField(max_length=64, unique=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    record_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Imported backup · {self.imported_at:%Y-%m-%d}"
