from django import forms
from django.core.exceptions import ValidationError
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import (
    Block,
    BlockPillarMission,
    ArchiveEntry,
    DailyPriority,
    DailyReview,
    Goal,
    Habit,
    JournalEntry,
    MeasurableTarget,
    Milestone,
    Pillar,
    PillarDailyLog,
    Review,
    Stage,
    StageReview,
    Task,
    VisionConfig,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 3)


class VisionConfigForm(StyledModelForm):
    class Meta:
        model = VisionConfig
        fields = ("name", "master_start", "master_deadline", "first_block_start", "master_vision", "timezone_name", "enable_mood_energy", "theme")
        widgets = {
            "master_start": forms.DateInput(attrs={"type": "date"}),
            "master_deadline": forms.DateInput(attrs={"type": "date"}),
            "first_block_start": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        master_start = cleaned.get("master_start")
        master_deadline = cleaned.get("master_deadline")
        first_block_start = cleaned.get("first_block_start")

        if master_deadline and master_start and master_deadline < master_start:
            self.add_error("master_deadline", "The master deadline must be on or after the master start.")
        if first_block_start and master_start and first_block_start < master_start:
            self.add_error("first_block_start", "The first block start must be on or after the master start.")
        if first_block_start and master_deadline and first_block_start > master_deadline:
            self.add_error("first_block_start", "The first block start must be on or before the master deadline.")
        if cleaned.get("timezone_name"):
            try:
                ZoneInfo(cleaned["timezone_name"])
            except (ZoneInfoNotFoundError, ValueError):
                self.add_error("timezone_name", "Enter a valid IANA timezone, such as Asia/Kolkata.")
        return cleaned


class BlockForm(StyledModelForm):
    class Meta:
        model = Block
        fields = (
            "name", "start_date", "deadline", "vision", "mission", "objectives", "weekly_targets",
            "monthly_milestones", "definition_of_done", "status", "final_review", "lessons_learned",
            "next_recommendations",
        )
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "deadline": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get("start_date")
        deadline = cleaned.get("deadline")
        if start_date and deadline and deadline < start_date:
            self.add_error("deadline", "The block deadline must be on or after the block start date.")
        return cleaned


class MissionForm(StyledModelForm):
    class Meta:
        model = BlockPillarMission
        fields = ("mission", "objectives", "daily_actions", "weekly_targets", "monthly_milestones", "definition_of_done", "status", "review")


class StageForm(StyledModelForm):
    class Meta:
        model = Stage
        fields = ("title", "vision", "mission", "syllabus", "resources", "objectives", "daily_practices", "weekly_milestones", "monthly_milestones", "completion_criteria", "evidence", "completed_at")
        widgets = {"completed_at": forms.DateInput(attrs={"type": "date"})}


class TargetForm(StyledModelForm):
    class Meta:
        model = MeasurableTarget
        fields = ("title", "block", "pillar", "stage", "unit", "target_value", "current_value", "due_date", "completion_criteria", "evidence", "status")
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}
        help_texts = {"status": "Targets are never marked achieved automatically; verify completion criteria and evidence first."}

    def clean(self):
        cleaned = super().clean()
        goal = cleaned.get("target_value")
        current = cleaned.get("current_value")
        if goal is not None and goal <= 0:
            self.add_error("target_value", "Enter a target greater than zero.")
        if current is not None and current < 0:
            self.add_error("current_value", "Current progress cannot be negative.")
        return cleaned


class MilestoneForm(StyledModelForm):
    class Meta:
        model = Milestone
        fields = ("title", "block", "pillar", "due_date", "description", "evidence")
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}


class GoalForm(StyledModelForm):
    class Meta:
        model = Goal
        fields = ("title", "description", "pillar", "block", "target", "current", "unit", "completion_criteria", "evidence", "deadline", "completed_at")
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("target") is not None and cleaned["target"] <= 0:
            self.add_error("target", "Enter a target greater than zero.")
        if cleaned.get("current") is not None and cleaned["current"] < 0:
            self.add_error("current", "Current progress cannot be negative.")
        return cleaned


class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "status", "priority", "due_date", "pillar", "block", "goal")
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}


class HabitForm(StyledModelForm):
    class Meta:
        model = Habit
        fields = ("title", "description", "pillar", "active")


class DailyPriorityForm(StyledModelForm):
    class Meta:
        model = DailyPriority
        fields = ("rank", "title")


class PillarDailyLogForm(StyledModelForm):
    class Meta:
        model = PillarDailyLog
        fields = ("status", "reflection", "outcome_note")


class DailyReviewForm(StyledModelForm):
    class Meta:
        model = DailyReview
        fields = ("mood", "energy", "evening_reflection", "wins", "improvement")
        widgets = {"energy": forms.NumberInput(attrs={"min": 1, "max": 5})}


class ReviewForm(StyledModelForm):
    class Meta:
        model = Review
        fields = (
            "period_start", "period_end", "block", "eight_pillar_performance", "target_progress", "wins",
            "problems", "missed_commitments", "corrective_actions", "trends", "achievements", "risks",
            "next_milestones", "target_evaluation", "evidence", "completed_missions", "incomplete_missions",
            "lessons_learned", "next_recommendations", "execution_consistency", "outcome_progress",
        )
        widgets = {"period_start": forms.DateInput(attrs={"type": "date"}), "period_end": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("period_start") and cleaned.get("period_end") and cleaned["period_end"] < cleaned["period_start"]:
            self.add_error("period_end", "The review period must end on or after it starts.")
        return cleaned


class JournalForm(StyledModelForm):
    class Meta:
        model = JournalEntry
        fields = ("date", "title", "mood", "text", "decision", "pillar")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class ArchiveEntryForm(StyledModelForm):
    class Meta:
        model = ArchiveEntry
        fields = ("date", "kind", "title", "text", "pillar")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class StageReviewForm(StyledModelForm):
    class Meta:
        model = StageReview
        fields = ("reviewed_at", "evaluation", "evidence", "lessons", "recommendations")
        widgets = {"reviewed_at": forms.DateInput(attrs={"type": "date"})}


class LegacyImportForm(forms.Form):
    backup = forms.FileField()
    reviewed = forms.BooleanField(
        required=True,
        label="I reviewed this backup and want to import its saved records.",
    )

    def clean_backup(self):
        backup = self.cleaned_data["backup"]
        if backup.size > 10 * 1024 * 1024:
            raise ValidationError("Backup files must be smaller than 10 MB.")
        if not backup.name.lower().endswith(".json"):
            raise ValidationError("Choose a JSON backup file.")
        return backup


class OnboardingVisionForm(StyledModelForm):
    class Meta:
        model = VisionConfig
        fields = ("name", "master_start", "master_deadline", "master_vision", "timezone_name", "theme")
        widgets = {
            "master_start": forms.DateInput(attrs={"type": "date"}),
            "master_deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        master_start = cleaned.get("master_start")
        master_deadline = cleaned.get("master_deadline")

        if master_deadline and master_start:
            duration_years = (master_deadline - master_start).days / 365.25
            if duration_years > 5:
                self.add_error("master_deadline", "Vision duration cannot exceed 5 years.")
            if master_deadline < master_start:
                self.add_error("master_deadline", "The master deadline must be on or after the master start.")
        if cleaned.get("timezone_name"):
            try:
                ZoneInfo(cleaned["timezone_name"])
            except (ZoneInfoNotFoundError, ValueError):
                self.add_error("timezone_name", "Enter a valid IANA timezone, such as Asia/Kolkata.")
        return cleaned


class OnboardingBlockForm(StyledModelForm):
    class Meta:
        model = Block
        fields = ("number", "name", "start_date", "deadline")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get("start_date")
        deadline = cleaned.get("deadline")
        if start_date and deadline and deadline < start_date:
            self.add_error("deadline", "The block deadline must be on or after the block start date.")
        return cleaned


class OnboardingPillarForm(StyledModelForm):
    class Meta:
        model = Pillar
        fields = ("name", "slug", "order", "description")


class OnboardingStageForm(StyledModelForm):
    class Meta:
        model = Stage
        fields = ("number", "title", "vision", "mission")
