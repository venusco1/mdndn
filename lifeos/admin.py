from django.contrib import admin

from .models import (
    Block,
    BlockPillarMission,
    ArchiveEntry,
    DailyPriority,
    DailyReview,
    Goal,
    Habit,
    HabitCheckIn,
    ImportBatch,
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


class StageInline(admin.TabularInline):
    model = Stage
    extra = 0
    fields = ("number", "title", "vision", "mission")


class MissionInline(admin.TabularInline):
    model = BlockPillarMission
    extra = 0
    fields = ("pillar", "stage", "mission", "status")


@admin.register(Pillar)
class PillarAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "scoring_method", "active")
    list_editable = ("scoring_method", "active")
    inlines = [StageInline]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "start_date", "deadline", "status")
    list_editable = ("status",)
    inlines = [MissionInline]


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("pillar", "number", "title", "completed_at")
    list_filter = ("pillar", "number")


@admin.register(VisionConfig)
class VisionConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "master_start", "master_deadline", "first_block_start")


@admin.register(MeasurableTarget)
class TargetAdmin(admin.ModelAdmin):
    list_display = ("title", "block", "pillar", "status", "due_date")
    list_filter = ("status", "block", "pillar")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "due_date", "pillar")
    list_filter = ("status", "priority", "pillar")


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "pillar", "block", "deadline", "completed_at")


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("title", "pillar", "active")
    list_filter = ("active", "pillar")


admin.site.register(
    [ArchiveEntry, Milestone, HabitCheckIn, PillarDailyLog, DailyPriority, DailyReview, Review, JournalEntry, StageReview, ImportBatch]
)
