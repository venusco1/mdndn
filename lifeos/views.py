import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .dates import timeline_summary
from .forms import (
    ArchiveEntryForm,
    BlockForm,
    DailyPriorityForm,
    DailyReviewForm,
    GoalForm,
    HabitForm,
    JournalForm,
    LegacyImportForm,
    MilestoneForm,
    MissionForm,
    OnboardingBlockForm,
    OnboardingPillarForm,
    OnboardingStageForm,
    OnboardingVisionForm,
    PillarDailyLogForm,
    ReviewForm,
    StageForm,
    StageReviewForm,
    TargetForm,
    TaskForm,
    VisionConfigForm,
)
from .module_registry import get_all_modules, get_enabled_modules, get_module_info, get_module_status
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
    UserModulePreference,
    VisionConfig,
)


CORE_NAVIGATION = [
    ("today", "Today", "today"),
    ("dashboard", "Dashboard", "dashboard"),
    ("features", "Features", "features"),
    ("settings", "Settings", "settings"),
]

MODULE_NAVIGATION_MAP = {
    "vision": ("vision", "Vision 30", "vision"),
    "blocks": ("blocks", "Blocks", "blocks"),
    "pillars": ("pillars", "Pillars", "pillars"),
    "goals": ("goals_tasks", "Goals & Targets", "goals_tasks"),
    "tasks": ("tasks", "Tasks", "tasks"),
    "habits": ("habits", "Habits", "habits"),
    "reviews": ("reviews", "Reviews", "reviews"),
    "journal": ("journal", "Journal", "journal"),
    "progress": ("progress", "Progress", "progress"),
    "archive": ("archive", "Archive", "archive"),
}

PILLAR_ALIASES = {
    "mental": "mental",
    "physical": "physical",
    "spiritual": "spiritual",
    "financial": "financial",
    "personal": "personal",
    "character": "character",
    "business": "business",
    "family": "family",
}


def _shell_context(request, page_title, **extra):
    config = VisionConfig.get_solo()
    today = timezone.localdate()
    blocks = list(Block.objects.select_related().all())
    active_block = next((block for block in blocks if block.start_date <= today <= block.deadline), None)
    if active_block is None:
        active_block = next((block for block in blocks if block.status == Block.Status.ACTIVE), None)
    total_days = config.total_window_days()
    block_days = sum(block.duration_days for block in blocks)

    enabled_modules = get_enabled_modules(request.user) if request.user.is_authenticated else []
    navigation = list(CORE_NAVIGATION)
    for module_key in enabled_modules:
        if module_key in MODULE_NAVIGATION_MAP:
            navigation.append(MODULE_NAVIGATION_MAP[module_key])

    context = {
        "page_title": page_title,
        "navigation": navigation,
        "config": config,
        "today": today,
        "today_iso": today.isoformat(),
        "blocks": blocks,
        "active_block": active_block,
        "day_number": config.day_number(today),
        "days_remaining": config.days_remaining(today),
        "block_day": active_block.day_number(today) if active_block else None,
        "timeline": timeline_summary(config.master_start, config.master_deadline, config.first_block_start, blocks),
        "unallocated_days": max(0, total_days - block_days),
        "theme": config.theme,
        "days_until_start": max(0, (config.master_start - today).days),
        "enabled_modules": enabled_modules,
    }
    context.update(extra)
    return context


def _safe_destination(value, default):
    allowed = {"today", "dashboard", "goals_tasks", "tasks", "habits", "journal", "archive"}
    return value if value in allowed else default


def _daily_execution(date_value):
    logs = list(PillarDailyLog.objects.filter(date=date_value))
    tasks = list(Task.objects.filter(due_date=date_value))
    priorities = list(DailyPriority.objects.filter(date=date_value))
    habits = list(Habit.objects.filter(active=True))
    completed_habits = HabitCheckIn.objects.filter(date=date_value, habit__in=habits).count()
    total = len(logs) + len(tasks) + len(priorities) + len(habits)
    if not total:
        return None, 0
    done = (
        sum(1 if entry.status == PillarDailyLog.Status.COMPLETED else 0.5 if entry.status == PillarDailyLog.Status.PARTIAL else 0 for entry in logs)
        + sum(1 for task in tasks if task.status == Task.Status.COMPLETED)
        + completed_habits
        + sum(1 for priority in priorities if priority.completed)
    )
    return round(done / total * 100, 2), total


@login_required
def today(request):
    from .module_registry import initialize_user_modules

    initialize_user_modules(request.user)

    current_date = timezone.localdate()
    enabled_modules = get_enabled_modules(request.user)

    logs = {}
    tasks_due = []
    overdue_tasks = []
    habits = []
    checked_habits = set()
    priorities = []
    daily_review = None
    execution_score = None
    activity_total = 0
    active_missions = []

    if "pillars" in enabled_modules:
        logs = {entry.pillar_id: entry for entry in PillarDailyLog.objects.filter(date=current_date)}
    if "tasks" in enabled_modules:
        tasks_due = list(Task.objects.filter(due_date=current_date).select_related("pillar"))
        overdue_tasks = list(Task.objects.filter(due_date__lt=current_date).exclude(status=Task.Status.COMPLETED).select_related("pillar"))
    if "habits" in enabled_modules:
        habits = list(Habit.objects.filter(active=True).select_related("pillar"))
        checked_habits = set(HabitCheckIn.objects.filter(date=current_date, habit__in=habits).values_list("habit_id", flat=True))
    if "tasks" in enabled_modules:
        priorities = list(DailyPriority.objects.filter(date=current_date))
    daily_review = DailyReview.objects.filter(date=current_date).first()
    execution_score, activity_total = _daily_execution(current_date)
    if "vision" in enabled_modules:
        active_missions = list(BlockPillarMission.objects.filter(block__status=Block.Status.ACTIVE).select_related("pillar", "stage")[:8])

    return render(
        request,
        "lifeos/today.html",
        _shell_context(
            request,
            "Today",
            pillars=Pillar.objects.filter(active=True) if "pillars" in enabled_modules else [],
            logs=logs,
            tasks_due=tasks_due,
            overdue_tasks=overdue_tasks,
            habits=habits,
            checked_habits=checked_habits,
            priorities=priorities,
            priority_form=DailyPriorityForm(),
            daily_review=daily_review,
            daily_review_form=DailyReviewForm(instance=daily_review),
            execution_score=round(execution_score) if execution_score is not None else None,
            daily_entry_count=activity_total,
            active_missions=active_missions,
        ),
    )


@login_required
def dashboard(request):
    from .module_registry import initialize_user_modules

    initialize_user_modules(request.user)

    current_date = timezone.localdate()
    enabled_modules = get_enabled_modules(request.user)

    open_tasks = []
    targets = []
    active_habits = []
    open_goals = []
    milestones = []
    completed_blocks = []
    pillars = []

    if "tasks" in enabled_modules:
        open_tasks = list(Task.objects.exclude(status=Task.Status.COMPLETED).select_related("pillar")[:8])
    if "goals" in enabled_modules:
        targets = list(MeasurableTarget.objects.select_related("block", "pillar").all())
        open_goals = list(Goal.objects.filter(completed_at__isnull=True).select_related("pillar"))
    if "habits" in enabled_modules:
        active_habits = list(Habit.objects.filter(active=True))
    if "vision" in enabled_modules:
        milestones = list(Milestone.objects.filter(completed_at__isnull=True, due_date__gte=current_date).select_related("block", "pillar")[:8])
        completed_blocks = list(Block.objects.filter(status__in=[Block.Status.COMPLETED, Block.Status.ARCHIVED]))
    if "pillars" in enabled_modules:
        pillars = list(Pillar.objects.all())

    return render(
        request,
        "lifeos/dashboard.html",
        _shell_context(
            request,
            "Dashboard",
            open_tasks=open_tasks,
            active_habits=active_habits,
            open_goals=open_goals,
            current_targets=targets,
            milestones=milestones,
            completed_blocks=completed_blocks,
            enabled_modules=enabled_modules,
            pillars=pillars,
        ),
    )


@login_required
def overview(request):
    return dashboard(request)


@login_required
def vision(request):
    blocks = Block.objects.all()
    return render(request, "lifeos/vision.html", _shell_context(request, "Vision 30", pillars=Pillar.objects.all(), blocks=blocks))


@login_required
def blocks(request):
    return render(request, "lifeos/blocks.html", _shell_context(request, "Blocks", blocks=Block.objects.prefetch_related("pillar_missions", "targets", "milestones")))


@login_required
def block_detail(request, pk):
    block = get_object_or_404(Block.objects.prefetch_related("pillar_missions__pillar", "pillar_missions__stage", "targets__pillar", "milestones"), pk=pk)
    missions = list(block.pillar_missions.all())
    mission_forms = {mission.pk: MissionForm(instance=mission, prefix=f"mission-{mission.pk}") for mission in missions}
    return render(
        request,
        "lifeos/block_detail.html",
        _shell_context(
            request,
            str(block),
            selected_block=block,
            block_form=BlockForm(instance=block, prefix="block"),
            mission_forms=mission_forms,
            targets=block.targets.all(),
            milestones=block.milestones.all(),
            target_form=TargetForm(initial={"block": block}),
            milestone_form=MilestoneForm(initial={"block": block}),
            tasks=block.tasks.select_related("pillar"),
            reviews=block.reviews.all(),
            target_status_choices=MeasurableTarget.Status.choices,
        ),
    )


@login_required
def pillars(request):
    all_pillars = Pillar.objects.prefetch_related("stages", "targets", "block_missions")
    return render(request, "lifeos/pillars.html", _shell_context(request, "Pillars", pillars=all_pillars))


@login_required
def pillar_detail(request, pk):
    pillar = get_object_or_404(Pillar.objects.prefetch_related("stages", "block_missions__block", "block_missions__stage"), pk=pk)
    return render(
        request,
        "lifeos/pillar_detail.html",
        _shell_context(
            request,
            pillar.name,
            pillar=pillar,
            stage_forms={stage.pk: StageForm(instance=stage, prefix=f"stage-{stage.pk}") for stage in pillar.stages.all()},
            stage_reviews={stage.pk: StageReviewForm(prefix=f"stage-review-{stage.pk}") for stage in pillar.stages.all()},
            targets=pillar.targets.select_related("block", "stage"),
            missions=pillar.block_missions.select_related("block", "stage"),
            scoring_choices=Pillar.ScoringMethod.choices,
        ),
    )


@login_required
def goals_tasks(request):
    return render(
        request,
        "lifeos/goals_tasks.html",
        _shell_context(
            request,
            "Goals & Tasks",
            goals=Goal.objects.select_related("pillar", "block"),
            tasks=Task.objects.select_related("pillar", "block", "goal"),
            goal_form=GoalForm(),
            task_form=TaskForm(),
        ),
    )


@login_required
def tasks(request):
    return render(request, "lifeos/tasks.html", _shell_context(request, "Tasks", tasks=Task.objects.select_related("pillar", "block", "goal"), task_form=TaskForm()))


@login_required
def habits(request):
    current_date = timezone.localdate()
    return render(
        request,
        "lifeos/habits.html",
        _shell_context(
            request,
            "Habits",
            habits=Habit.objects.prefetch_related("checkins"),
            checked_habits=set(HabitCheckIn.objects.filter(date=current_date).values_list("habit_id", flat=True)),
            habit_form=HabitForm(),
        ),
    )


@login_required
def life(request):
    return render(request, "lifeos/life.html", _shell_context(request, "Life", pillars=Pillar.objects.all()))


def _review_period(kind, today):
    if kind == Review.Kind.WEEKLY:
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if kind == Review.Kind.MONTHLY:
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, next_month - timedelta(days=1)
    return None, None


@login_required
def reviews(request):
    kind = request.GET.get("kind", Review.Kind.WEEKLY)
    if kind not in Review.Kind.values:
        kind = Review.Kind.WEEKLY
    current_date = timezone.localdate()
    if kind == Review.Kind.BLOCK:
        block = Block.objects.filter(status=Block.Status.ACTIVE).first() or Block.objects.first()
        start, end = (block.start_date, block.deadline) if block else (current_date, current_date)
    else:
        block = None
        start, end = _review_period(kind, current_date)
    review_query = Review.objects.filter(kind=kind, period_start=start)
    review_query = review_query.filter(block=block) if block else review_query.filter(block__isnull=True)
    review = review_query.first()
    initial = {"period_start": start, "period_end": end, "block": block}
    form = ReviewForm(request.POST or None, instance=review, initial=initial)
    daily_review = DailyReview.objects.filter(date=current_date).first()
    return render(
        request,
        "lifeos/reviews.html",
        _shell_context(
            request,
            "Reviews",
            review_kind=kind,
            review=review,
            review_form=form,
            review_blocks=Block.objects.all(),
            review_history=Review.objects.select_related("block")[:30],
            daily_reviews=DailyReview.objects.all()[:14],
            daily_review=daily_review,
            today=current_date,
        ),
    )


@login_required
def journal(request):
    return render(request, "lifeos/journal.html", _shell_context(request, "Journal", entries=JournalEntry.objects.select_related("pillar"), journal_form=JournalForm(initial={"date": timezone.localdate()})))


@login_required
def progress(request):
    targets = MeasurableTarget.objects.select_related("block", "pillar", "stage").all()
    goals = Goal.objects.select_related("block", "pillar").all()
    recent_execution = list(DailyReview.objects.filter(execution_score__isnull=False).order_by("-date")[:14])
    today = timezone.localdate()
    current_start = today - timedelta(days=6)
    previous_start = today - timedelta(days=13)
    current_values = [
        float(value) for value in DailyReview.objects.filter(date__gte=current_start, date__lte=today, execution_score__isnull=False).values_list("execution_score", flat=True)
    ]
    previous_values = [
        float(value) for value in DailyReview.objects.filter(date__gte=previous_start, date__lt=current_start, execution_score__isnull=False).values_list("execution_score", flat=True)
    ]
    current_average = sum(current_values) / len(current_values) if current_values else None
    previous_average = sum(previous_values) / len(previous_values) if previous_values else None
    pillars_with_targets = []
    for pillar in Pillar.objects.all():
        pillar_targets = [target for target in targets if target.pillar_id == pillar.id]
        pillars_with_targets.append({"pillar": pillar, "targets": pillar_targets})
    return render(
        request,
        "lifeos/progress.html",
        _shell_context(
            request,
            "Progress",
            targets=targets,
            goals=goals,
            recent_execution=reversed(recent_execution),
            current_execution_average=current_average,
            previous_execution_average=previous_average,
            execution_average_change=current_average - previous_average if current_average is not None and previous_average is not None else None,
            current_execution_count=len(current_values),
            previous_execution_count=len(previous_values),
            pillars_with_targets=pillars_with_targets,
            reviews=Review.objects.select_related("block")[:20],
            daily_entries=DailyReview.objects.all()[:30],
        ),
    )


@login_required
def archive(request):
    return render(
        request,
        "lifeos/archive.html",
        _shell_context(
            request,
            "Archive",
            blocks=Block.objects.filter(status__in=[Block.Status.COMPLETED, Block.Status.ARCHIVED]),
            reviews=Review.objects.select_related("block"),
            journal_entries=JournalEntry.objects.all(),
            archive_entries=ArchiveEntry.objects.select_related("pillar"),
            archive_form=ArchiveEntryForm(initial={"date": timezone.localdate()}),
            stage_reviews=StageReview.objects.select_related("stage__pillar"),
        ),
    )


@login_required
def settings_page(request):
    return render(
        request,
        "lifeos/settings.html",
        _shell_context(
            request,
            "Settings",
            settings_form=VisionConfigForm(instance=VisionConfig.get_solo(), prefix="settings"),
            import_form=LegacyImportForm(prefix="import"),
            config=VisionConfig.get_solo(),
        ),
    )


@login_required
@require_POST
def save_settings(request):
    config = VisionConfig.get_solo()
    form = VisionConfigForm(request.POST, instance=config, prefix="settings")
    if form.is_valid():
        form.save()
        messages.success(request, "Vision 30 settings saved.")
    else:
        messages.error(request, "Settings were not saved. Check the highlighted fields.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect("settings")


def _valid_model_form(request, form_class, *, instance=None, success_message, fail_redirect, prefix=None, extra=None):
    form = form_class(request.POST, instance=instance, prefix=prefix)
    if form.is_valid():
        form.save()
        messages.success(request, success_message)
    else:
        messages.error(request, "The record was not saved. Correct the highlighted fields.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect(fail_redirect, **(extra or {}))


@login_required
@require_POST
def save_block(request, pk):
    block = get_object_or_404(Block, pk=pk)
    return _valid_model_form(request, BlockForm, instance=block, prefix="block", success_message="Block saved.", fail_redirect="block_detail", extra={"pk": pk})


@login_required
@require_POST
def save_mission(request, pk):
    mission = get_object_or_404(BlockPillarMission.objects.select_related("block"), pk=pk)
    return _valid_model_form(request, MissionForm, instance=mission, prefix=f"mission-{pk}", success_message=f"{mission.pillar.name} mission saved.", fail_redirect="block_detail", extra={"pk": mission.block_id})


@login_required
@require_POST
def save_stage(request, pk):
    stage = get_object_or_404(Stage, pk=pk)
    form = StageForm(request.POST, instance=stage, prefix=f"stage-{pk}")
    if form.is_valid():
        form.save()
        messages.success(request, f"{stage} saved.")
    else:
        messages.error(request, "Stage was not saved. Correct the highlighted fields.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect("pillar_detail", pk=stage.pillar_id)


@login_required
@require_POST
def save_pillar_scoring(request, pk):
    pillar = get_object_or_404(Pillar, pk=pk)
    scoring_method = request.POST.get("scoring_method", "")
    if scoring_method not in Pillar.ScoringMethod.values:
        messages.error(request, "Choose a valid pillar measurement method.")
    else:
        pillar.scoring_method = scoring_method
        pillar.scoring_notes = request.POST.get("scoring_notes", "").strip()[:5000]
        pillar.save(update_fields=["scoring_method", "scoring_notes"])
        messages.success(request, f"Measurement method saved for {pillar.name}.")
    return redirect("pillar_detail", pk=pk)


@login_required
@require_POST
def create_target(request):
    form = TargetForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Measurable target saved.")
        block_id = request.POST.get("block")
        if block_id:
            return redirect("block_detail", pk=block_id)
    else:
        messages.error(request, "Target was not saved. Review its title, measurements, and dates.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect("goals_tasks")


@login_required
@require_POST
def update_target(request, pk):
    target = get_object_or_404(MeasurableTarget, pk=pk)
    form = TargetForm(request.POST, instance=target)
    if form.is_valid():
        form.save()
        messages.success(request, "Target and evidence updated.")
    else:
        messages.error(request, "Target was not updated. Check the submitted values.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect("block_detail", pk=target.block_id) if target.block_id else redirect("progress")


@login_required
@require_POST
def create_milestone(request):
    form = MilestoneForm(request.POST)
    if form.is_valid():
        milestone = form.save()
        messages.success(request, "Milestone saved.")
        if milestone.block_id:
            return redirect("block_detail", pk=milestone.block_id)
    else:
        messages.error(request, "Milestone was not saved. Check the title and date.")
    return redirect("goals_tasks")


@login_required
@require_POST
def create_goal(request):
    form = GoalForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Goal saved.")
    else:
        messages.error(request, "Goal was not saved. Add a title and valid target.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect(_safe_destination(request.POST.get("next"), "goals_tasks"))


@login_required
@require_POST
def update_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    form = GoalForm(request.POST, instance=goal)
    if form.is_valid():
        form.save()
        messages.success(request, "Goal progress, evidence and completion status saved.")
    else:
        messages.error(request, "Goal was not updated. Review its title, target, and progress.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect("goals_tasks")


@login_required
@require_POST
def create_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        if task.status == Task.Status.COMPLETED:
            task.completed_at = timezone.localdate()
        task.save()
        messages.success(request, "Task saved.")
    else:
        messages.error(request, "Task was not saved. Check the title and due date.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect(_safe_destination(request.POST.get("next"), "tasks"))


@login_required
@require_POST
def update_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.POST.get("status") == Task.Status.COMPLETED:
        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.localdate()
    elif request.POST.get("status") in Task.Status.values:
        task.status = request.POST["status"]
        task.completed_at = None
    task.save(update_fields=["status", "completed_at"])
    messages.success(request, "Task status updated.")
    return redirect(_safe_destination(request.POST.get("next"), "tasks"))


@login_required
@require_POST
def create_habit(request):
    form = HabitForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Habit saved.")
    else:
        messages.error(request, "Habit was not saved. Add a name.")
    return redirect("habits")


@login_required
@require_POST
def toggle_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk)
    checkin, created = HabitCheckIn.objects.get_or_create(habit=habit, date=timezone.localdate())
    if not created:
        checkin.delete()
    messages.success(request, f"{habit.title}: {'checked in' if created else 'check-in removed'}.")
    return redirect(_safe_destination(request.POST.get("next"), "habits"))


@login_required
@require_POST
def save_daily_priority(request):
    form = DailyPriorityForm(request.POST)
    if form.is_valid():
        priority, _ = DailyPriority.objects.update_or_create(
            date=timezone.localdate(), rank=form.cleaned_data["rank"],
            defaults={"title": form.cleaned_data["title"]},
        )
        messages.success(request, "Today's priority saved.")
    else:
        messages.error(request, "Choose a priority number and enter a title.")
    return redirect("today")


@login_required
@require_POST
def toggle_priority(request, pk):
    priority = get_object_or_404(DailyPriority, pk=pk, date=timezone.localdate())
    priority.completed = not priority.completed
    priority.save(update_fields=["completed"])
    return redirect("today")


@login_required
@require_POST
def toggle_milestone(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk)
    milestone.completed_at = None if milestone.completed_at else timezone.localdate()
    milestone.save(update_fields=["completed_at"])
    messages.success(request, f"Milestone {'completed' if milestone.completed_at else 'reopened'}.")
    return redirect("block_detail", pk=milestone.block_id) if milestone.block_id else redirect("goals_tasks")


@login_required
@require_POST
def save_pillar_daily(request, pk):
    pillar = get_object_or_404(Pillar, pk=pk, active=True)
    log, _ = PillarDailyLog.objects.get_or_create(pillar=pillar, date=timezone.localdate())
    form = PillarDailyLogForm(request.POST, instance=log)
    if form.is_valid():
        form.save()
        messages.success(request, f"{pillar.name} check-in saved.")
    else:
        messages.error(request, "Check-in was not saved.")
    return redirect("today")


@login_required
@require_POST
def save_daily_review(request):
    review, _ = DailyReview.objects.get_or_create(date=timezone.localdate())
    form = DailyReviewForm(request.POST, instance=review)
    if form.is_valid():
        review = form.save()
        review.execution_score = _daily_execution(review.date)[0]
        review.save(update_fields=["execution_score"])
        messages.success(request, "Daily reflection saved.")
    else:
        messages.error(request, "Daily reflection was not saved. Check the mood and energy values.")
    return redirect("today")


@login_required
@require_POST
def save_review(request):
    kind = request.POST.get("kind", Review.Kind.WEEKLY)
    if kind not in Review.Kind.values:
        return HttpResponseBadRequest("Unknown review type.")
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.kind = kind
        if kind == Review.Kind.BLOCK and not review.block_id:
            review.block = Block.objects.filter(status=Block.Status.ACTIVE).first()
        review.save()
        messages.success(request, "Review saved.")
    else:
        messages.error(request, "Review was not saved. Correct the highlighted dates and fields.")
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {' '.join(errors)}")
    return redirect(f"{redirect('reviews').url}?kind={kind}")


@login_required
@require_POST
def create_journal(request):
    form = JournalForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Journal entry saved.")
    else:
        messages.error(request, "Journal entry was not saved. Add your reflection.")
    return redirect("journal")


@login_required
@require_POST
def create_archive_entry(request):
    form = ArchiveEntryForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Archive entry saved.")
    else:
        messages.error(request, "Archive entry was not saved. Check its title and date.")
    return redirect("archive")


@login_required
@require_POST
def save_stage_review(request, pk):
    stage = get_object_or_404(Stage, pk=pk)
    form = StageReviewForm(request.POST, prefix=f"stage-review-{pk}")
    if form.is_valid():
        stage_review = form.save(commit=False)
        stage_review.stage = stage
        stage_review.save()
        stage.evidence = stage_review.evidence or stage.evidence
        stage.save(update_fields=["evidence"])
        messages.success(request, f"Review saved for {stage}.")
    else:
        messages.error(request, "Stage review was not saved.")
    return redirect("pillar_detail", pk=stage.pillar_id)


@login_required
@require_POST
def delete_record(request, kind, pk):
    models = {"task": Task, "goal": Goal, "habit": Habit, "journal": JournalEntry, "milestone": Milestone, "archive": ArchiveEntry}
    model = models.get(kind)
    if not model:
        return HttpResponseBadRequest("Unknown record type.")
    record = get_object_or_404(model, pk=pk)
    record.delete()
    messages.success(request, f"{kind.capitalize()} deleted.")
    destination = _safe_destination(request.POST.get("next"), "archive")
    return redirect(destination)


def _serialize_records(queryset, fk_fields=()):
    results = []
    for obj in queryset:
        row = {}
        for field in obj._meta.concrete_fields:
            if field.primary_key:
                row[field.name] = obj.pk
            elif field.name in fk_fields:
                related = getattr(obj, field.name)
                row[field.name] = related.slug if isinstance(related, Pillar) else related.number if isinstance(related, Block) else related.pk if related else None
            else:
                value = getattr(obj, field.attname)
                row[field.name] = value.isoformat() if hasattr(value, "isoformat") else value
        results.append(row)
    return results


@login_required
def export_backup(request):
    config = VisionConfig.get_solo()
    data = {
        "schema_version": 2,
        "exported_at": timezone.now(),
        "config": _serialize_records(VisionConfig.objects.filter(pk=config.pk))[0],
        "pillars": _serialize_records(Pillar.objects.all()),
        "blocks": _serialize_records(Block.objects.all()),
        "stages": _serialize_records(Stage.objects.select_related("pillar").all(), ("pillar",)),
        "missions": _serialize_records(BlockPillarMission.objects.select_related("block", "pillar", "stage").all(), ("block", "pillar", "stage")),
        "targets": _serialize_records(MeasurableTarget.objects.select_related("block", "pillar", "stage").all(), ("block", "pillar", "stage")),
        "milestones": _serialize_records(Milestone.objects.select_related("block", "pillar").all(), ("block", "pillar")),
        "goals": _serialize_records(Goal.objects.select_related("block", "pillar").all(), ("pillar", "block")),
        "tasks": _serialize_records(Task.objects.select_related("pillar", "block", "goal").all(), ("pillar", "block", "goal")),
        "habits": _serialize_records(Habit.objects.select_related("pillar").all(), ("pillar",)),
        "habit_checkins": _serialize_records(HabitCheckIn.objects.select_related("habit").all(), ("habit",)),
        "pillar_daily_logs": _serialize_records(PillarDailyLog.objects.select_related("pillar").all(), ("pillar",)),
        "daily_priorities": _serialize_records(DailyPriority.objects.all()),
        "daily_reviews": _serialize_records(DailyReview.objects.all()),
        "reviews": _serialize_records(Review.objects.select_related("block").all(), ("block",)),
        "journal": _serialize_records(JournalEntry.objects.select_related("pillar").all(), ("pillar",)),
        "archive": _serialize_records(ArchiveEntry.objects.select_related("pillar").all(), ("pillar",)),
        "stage_reviews": _serialize_records(StageReview.objects.select_related("stage").all(), ("stage",)),
    }
    payload = json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)
    response = HttpResponse(payload, content_type="application/json; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="vision30-backup-{timezone.localdate():%Y-%m-%d}.json"'
    return response


def _as_iso_date(value, *, required=False):
    if not value:
        if required:
            raise ValueError("A required date is missing.")
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid date: {value!r}.") from error


def _decimal(value, field_name):
    if value in (None, ""):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{field_name} must be a valid number.") from error
    if not result.is_finite():
        raise ValueError(f"{field_name} must be a finite number.")
    if abs(result) >= Decimal("1000000000000") or result.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} must fit within 12 integer digits and 2 decimal places.")
    return result


def _list(data, key):
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f'The "{key}" field must be a list of objects.')
    return value


def _import_v2(payload, pillar_map, block_map):
    count = 0
    config_data = payload.get("config")
    if config_data is not None:
        if not isinstance(config_data, dict):
            raise ValueError('The "config" field must be an object.')
        config = VisionConfig.get_solo()
        for field in ("name", "master_vision"):
            if field in config_data:
                setattr(config, field, str(config_data[field]))
        for field in ("master_start", "master_deadline", "first_block_start"):
            if field in config_data:
                setattr(config, field, _as_iso_date(config_data[field], required=True))
        if "timezone_name" in config_data:
            try:
                ZoneInfo(str(config_data["timezone_name"]))
            except (ZoneInfoNotFoundError, ValueError) as error:
                raise ValueError("Backup contains an invalid timezone.") from error
            config.timezone_name = str(config_data["timezone_name"])
        if "enable_mood_energy" in config_data:
            config.enable_mood_energy = bool(config_data["enable_mood_energy"])
        if config_data.get("theme") in VisionConfig.Theme.values:
            config.theme = config_data["theme"]
        config.save()
        count += 1

    source_pillars = {}
    for item in _list(payload, "pillars"):
        slug = str(item.get("slug", ""))
        pillar = pillar_map.get(slug)
        if not pillar:
            raise ValueError(f"Backup refers to an unknown pillar: {slug}.")
        for field in ("name", "order", "description", "scoring_method", "scoring_notes", "active"):
            if field in item and field != "scoring_method" or field == "scoring_method" and item.get(field) in Pillar.ScoringMethod.values:
                setattr(pillar, field, item[field])
        pillar.save()
        source_pillars[str(item.get("id", ""))] = pillar
        count += 1

    source_blocks = {}
    for item in _list(payload, "blocks"):
        try:
            number = int(item["number"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Each block in a Vision 30 backup needs a valid number.") from error
        block = block_map.get(number)
        if not block:
            raise ValueError(f"Backup refers to an unknown block number: {number}.")
        for field in ("name", "start_date", "deadline", "vision", "mission", "objectives", "weekly_targets", "monthly_milestones", "definition_of_done", "final_review", "lessons_learned", "next_recommendations"):
            if field in item:
                setattr(block, field, _as_iso_date(item[field], required=True) if field in ("start_date", "deadline") else str(item[field]))
        if item.get("status") in Block.Status.values:
            block.status = item["status"]
        if block.deadline < block.start_date:
            raise ValueError(f"Block {number:02d} deadline precedes its start date.")
        block.save()
        source_blocks[str(item.get("id", ""))] = block
        count += 1

    source_stages = {}
    for item in _list(payload, "stages"):
        pillar = pillar_map.get(str(item.get("pillar", "")))
        if not pillar:
            raise ValueError("A stage in the backup refers to an unknown pillar.")
        number = int(item.get("number", 0))
        stage = Stage.objects.filter(pillar=pillar, number=number).first()
        if not stage:
            raise ValueError(f"Backup refers to an unknown stage number: {number}.")
        for field in ("title", "vision", "mission", "syllabus", "resources", "objectives", "daily_practices", "weekly_milestones", "monthly_milestones", "completion_criteria", "evidence"):
            if field in item:
                setattr(stage, field, str(item[field]))
        if "completed_at" in item:
            stage.completed_at = _as_iso_date(item["completed_at"])
        stage.save()
        source_stages[str(item.get("id", ""))] = stage
        count += 1

    for item in _list(payload, "missions"):
        block = block_map.get(item.get("block"))
        pillar = pillar_map.get(str(item.get("pillar", "")))
        stage = source_stages.get(str(item.get("stage", "")))
        if not block or not pillar or not stage:
            raise ValueError("A block mission refers to a missing block, pillar or stage.")
        mission, _ = BlockPillarMission.objects.get_or_create(
            block=block, pillar=pillar, defaults={"stage": stage}
        )
        mission.stage = stage
        for field in ("mission", "objectives", "daily_actions", "weekly_targets", "monthly_milestones", "definition_of_done", "review"):
            if field in item:
                setattr(mission, field, str(item[field]))
        if item.get("status") in Block.Status.values:
            mission.status = item["status"]
        mission.save()
        count += 1

    for item in _list(payload, "targets"):
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        block = block_map.get(item.get("block")) if item.get("block") is not None else None
        pillar = pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None
        stage = source_stages.get(str(item.get("stage", ""))) if item.get("stage") else None
        status = item.get("status") if item.get("status") in MeasurableTarget.Status.values else MeasurableTarget.Status.NOT_STARTED
        MeasurableTarget.objects.create(
            title=title[:180], block=block, pillar=pillar, stage=stage, unit=str(item.get("unit", ""))[:40],
            target_value=_decimal(item.get("target_value"), "Target value"),
            current_value=_decimal(item.get("current_value"), "Current value"),
            due_date=_as_iso_date(item.get("due_date")), completion_criteria=str(item.get("completion_criteria", "")),
            evidence=str(item.get("evidence", "")), status=status,
        )
        count += 1

    for item in _list(payload, "milestones"):
        title = str(item.get("title", "")).strip()
        if title:
            Milestone.objects.create(
                title=title[:180], block=block_map.get(item.get("block")) if item.get("block") is not None else None,
                pillar=pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None,
                due_date=_as_iso_date(item.get("due_date")), description=str(item.get("description", "")),
                completed_at=_as_iso_date(item.get("completed_at")), evidence=str(item.get("evidence", "")),
            )
            count += 1

    source_goals = {}
    for item in _list(payload, "goals"):
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        goal = Goal.objects.create(
            title=title[:180], description=str(item.get("description", "")),
            pillar=pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None,
            block=block_map.get(item.get("block")) if item.get("block") is not None else None,
            target=_decimal(item.get("target"), "Goal target"), current=_decimal(item.get("current"), "Goal progress"),
            unit=str(item.get("unit", ""))[:40], completion_criteria=str(item.get("completion_criteria", "")),
            evidence=str(item.get("evidence", "")), deadline=_as_iso_date(item.get("deadline")),
            completed_at=_as_iso_date(item.get("completed_at")),
        )
        source_goals[str(item.get("id", ""))] = goal
        count += 1

    for item in _list(payload, "tasks"):
        title = str(item.get("title", "")).strip()
        if title:
            status = item.get("status") if item.get("status") in Task.Status.values else Task.Status.TODO
            Task.objects.create(
                title=title[:180], description=str(item.get("description", "")), status=status,
                priority=item.get("priority") if item.get("priority") in Task.Priority.values else Task.Priority.MEDIUM,
                due_date=_as_iso_date(item.get("due_date")),
                pillar=pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None,
                block=block_map.get(item.get("block")) if item.get("block") is not None else None,
                goal=source_goals.get(str(item.get("goal", ""))) if item.get("goal") else None,
                completed_at=_as_iso_date(item.get("completed_at")),
            )
            count += 1

    source_habits = {}
    for item in _list(payload, "habits"):
        title = str(item.get("title", "")).strip()
        if title:
            habit = Habit.objects.create(
                title=title[:180], description=str(item.get("description", "")),
                pillar=pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None,
                active=bool(item.get("active", True)),
            )
            source_habits[str(item.get("id", ""))] = habit
            count += 1
    for item in _list(payload, "habit_checkins"):
        habit = source_habits.get(str(item.get("habit", "")))
        if habit:
            _, created = HabitCheckIn.objects.get_or_create(habit=habit, date=_as_iso_date(item.get("date"), required=True))
            count += int(created)

    for item in _list(payload, "pillar_daily_logs"):
        pillar = pillar_map.get(str(item.get("pillar", "")))
        if not pillar:
            raise ValueError("A daily pillar check-in refers to an unknown pillar.")
        status = item.get("status")
        if status not in PillarDailyLog.Status.values:
            raise ValueError("A daily pillar check-in has an invalid status.")
        _, created = PillarDailyLog.objects.get_or_create(
            pillar=pillar, date=_as_iso_date(item.get("date"), required=True),
            defaults={"status": status, "reflection": str(item.get("reflection", "")), "outcome_note": str(item.get("outcome_note", ""))},
        )
        count += int(created)
    for item in _list(payload, "daily_priorities"):
        rank = int(item.get("rank", 0))
        if 1 <= rank <= 3:
            _, created = DailyPriority.objects.get_or_create(
                date=_as_iso_date(item.get("date"), required=True), rank=rank,
                defaults={"title": str(item.get("title", ""))[:180], "completed": bool(item.get("completed", False))},
            )
            count += int(created)
    for item in _list(payload, "daily_reviews"):
        entry_date = _as_iso_date(item.get("date"), required=True)
        defaults = {
            "mood": item.get("mood") if item.get("mood") in DailyReview.Mood.values else "",
            "energy": item.get("energy") if item.get("energy") in range(1, 6) else None,
            "evening_reflection": str(item.get("evening_reflection", "")), "wins": str(item.get("wins", "")),
            "improvement": str(item.get("improvement", "")),
        }
        execution_score = item.get("execution_score")
        if execution_score is not None:
            try:
                execution_score = Decimal(str(execution_score))
            except (InvalidOperation, ValueError):
                raise ValueError("A daily execution score must be a number between 0 and 100.")
            if not execution_score.is_finite() or not 0 <= execution_score <= 100:
                raise ValueError("A daily execution score must be a number between 0 and 100.")
        defaults["execution_score"] = execution_score
        _, created = DailyReview.objects.get_or_create(date=entry_date, defaults=defaults)
        count += int(created)

    for item in _list(payload, "reviews"):
        kind = item.get("kind")
        if kind not in Review.Kind.values:
            raise ValueError("A review has an invalid review type.")
        start = _as_iso_date(item.get("period_start"), required=True)
        end = _as_iso_date(item.get("period_end"), required=True)
        block = block_map.get(item.get("block")) if item.get("block") is not None else None
        if end < start:
            raise ValueError("A review period ends before it begins.")
        existing = Review.objects.filter(kind=kind, period_start=start, block=block).first()
        if not existing:
            fields = (
                "eight_pillar_performance", "target_progress", "wins", "problems", "missed_commitments",
                "corrective_actions", "trends", "achievements", "risks", "next_milestones", "target_evaluation",
                "evidence", "completed_missions", "incomplete_missions", "lessons_learned",
                "next_recommendations", "execution_consistency", "outcome_progress",
            )
            defaults = {field: str(item.get(field, "")) for field in fields}
            Review.objects.create(kind=kind, period_start=start, period_end=end, block=block, **defaults)
            count += 1

    for item in _list(payload, "journal"):
        text = str(item.get("text", "")).strip()
        if text:
            JournalEntry.objects.create(
                date=_as_iso_date(item.get("date")) or timezone.localdate(),
                title=str(item.get("title", ""))[:180], mood=str(item.get("mood", ""))[:32],
                text=text, decision=str(item.get("decision", "")),
                pillar=pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None,
            )
            count += 1
    for item in _list(payload, "archive"):
        title = str(item.get("title", "")).strip()
        if title:
            kind = item.get("kind") if item.get("kind") in ArchiveEntry.Kind.values else ArchiveEntry.Kind.ACHIEVEMENT
            ArchiveEntry.objects.create(
                date=_as_iso_date(item.get("date")) or timezone.localdate(), kind=kind, title=title[:180],
                text=str(item.get("text", "")),
                pillar=pillar_map.get(str(item.get("pillar", ""))) if item.get("pillar") else None,
            )
            count += 1
    for item in _list(payload, "stage_reviews"):
        stage = source_stages.get(str(item.get("stage", "")))
        if stage:
            StageReview.objects.create(
                stage=stage, reviewed_at=_as_iso_date(item.get("reviewed_at")) or timezone.localdate(),
                evaluation=str(item.get("evaluation", "")), evidence=str(item.get("evidence", "")),
                lessons=str(item.get("lessons", "")), recommendations=str(item.get("recommendations", "")),
            )
            count += 1
    return count


@transaction.atomic
def _import_legacy(payload, checksum):
    if ImportBatch.objects.filter(checksum=checksum).exists():
        return 0
    if not isinstance(payload, dict):
        raise ValueError("The selected backup must contain a JSON object.")
    version = payload.get("schema_version", 1)
    if version not in (1, 2):
        raise ValueError("This backup version is not supported.")
    count = 0
    pillar_map = {pillar.slug: pillar for pillar in Pillar.objects.all()}
    block_map = {block.number: block for block in Block.objects.all()}
    for slug, alias in PILLAR_ALIASES.items():
        if slug in pillar_map:
            pillar_map[alias] = pillar_map[slug]

    if version == 1:
        for item in _list(payload, "goals"):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            Goal.objects.create(
                title=title[:180],
                description=str(item.get("description", "")),
                pillar=pillar_map.get(str(item.get("pillar", ""))),
                target=_decimal(item.get("target"), "Goal target"),
                current=_decimal(item.get("current"), "Goal progress"),
                unit=str(item.get("unit", ""))[:40],
                deadline=_as_iso_date(item.get("deadline")),
            )
            count += 1
        for item in _list(payload, "tasks"):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            Task.objects.create(
                title=title[:180],
                description=str(item.get("description", "")),
                status=item.get("status") if item.get("status") in Task.Status.values else Task.Status.TODO,
                priority=item.get("priority") if item.get("priority") in Task.Priority.values else Task.Priority.MEDIUM,
                due_date=_as_iso_date(item.get("dueDate") or item.get("due_date")),
                pillar=pillar_map.get(str(item.get("pillar", ""))),
            )
            count += 1
        for item in _list(payload, "habits"):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            habit = Habit.objects.create(title=title[:180])
            count += 1
            dates = item.get("history", [])
            if not isinstance(dates, list):
                raise ValueError("Habit history must be a list of dates.")
            for habit_date in set(filter(None, (_as_iso_date(value) for value in dates))):
                HabitCheckIn.objects.get_or_create(habit=habit, date=habit_date)
                count += 1
        for item in _list(payload, "journal"):
            text = str(item.get("text", "")).strip()
            if text:
                JournalEntry.objects.create(
                    date=_as_iso_date(item.get("date")) or timezone.localdate(),
                    title=str(item.get("title", ""))[:180],
                    mood=str(item.get("mood", ""))[:32],
                    text=text,
                )
                count += 1
        for item in _list(payload, "archive"):
            title = str(item.get("title", "")).strip()
            if title:
                ArchiveEntry.objects.create(
                    date=_as_iso_date(item.get("date")) or timezone.localdate(),
                    title=title[:180],
                    kind=item.get("type") if item.get("type") in ArchiveEntry.Kind.values else ArchiveEntry.Kind.ACHIEVEMENT,
                    text=str(item.get("text", "")),
                )
                count += 1
        for item in _list(payload, "history"):
            scores = item.get("scores", {})
            if not isinstance(scores, dict):
                raise ValueError("Each legacy history record must contain a score object.")
            log_date = _as_iso_date(item.get("date"), required=True)
            for slug, pillar in pillar_map.items():
                if slug not in PILLAR_ALIASES:
                    continue
                raw_score = scores.get(slug)
                if raw_score is None:
                    continue
                score = max(0, min(2, round(float(raw_score))))
                status = [PillarDailyLog.Status.NOT_COMPLETED, PillarDailyLog.Status.PARTIAL, PillarDailyLog.Status.COMPLETED][score]
                _, created = PillarDailyLog.objects.get_or_create(
                    pillar=pillar, date=log_date,
                    defaults={"status": status, "reflection": "Imported from the legacy daily pillar score."},
                )
                count += int(created)
        priorities = payload.get("big3", [])
        if priorities is not None and not isinstance(priorities, list):
            raise ValueError('The "big3" field must be a list.')
        for rank, title in enumerate(priorities or [], start=1):
            title = str(title).strip()
            if title and rank <= 3:
                _, created = DailyPriority.objects.get_or_create(date=timezone.localdate(), rank=rank, defaults={"title": title[:180]})
                count += int(created)
        current_scores = payload.get("scores", {})
        if current_scores is not None and not isinstance(current_scores, dict):
            raise ValueError('The "scores" field must be an object.')
        for slug, raw_score in (current_scores or {}).items():
            pillar = pillar_map.get(str(slug))
            if not pillar:
                continue
            score = max(0, min(2, round(float(raw_score))))
            status = [PillarDailyLog.Status.NOT_COMPLETED, PillarDailyLog.Status.PARTIAL, PillarDailyLog.Status.COMPLETED][score]
            _, created = PillarDailyLog.objects.get_or_create(
                pillar=pillar, date=timezone.localdate(),
                defaults={"status": status, "reflection": "Imported from the legacy current pillar check-in."},
            )
            count += int(created)
    else:
        count += _import_v2(payload, pillar_map, block_map)

    ImportBatch.objects.create(checksum=checksum, record_count=count)
    return count


@login_required
@require_POST
def import_backup(request):
    form = LegacyImportForm(request.POST, request.FILES, prefix="import")
    if not form.is_valid():
        messages.error(request, "Choose a valid JSON backup smaller than 10 MB.")
        return redirect("settings")
    uploaded = form.cleaned_data["backup"]
    raw = uploaded.read()
    try:
        payload = json.loads(raw.decode("utf-8"))
        imported = _import_legacy(payload, hashlib.sha256(raw).hexdigest())
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as error:
        messages.error(request, f"Backup was not imported: {error}")
        return redirect("settings")
    if imported == 0:
        messages.info(request, "This exact backup has already been imported; no duplicate records were added.")
    else:
        messages.success(request, f"Imported {imported} records. Existing records were kept.")
    return redirect("settings")


@login_required
def onboarding_vision(request):
    config = VisionConfig.get_solo()
    form = OnboardingVisionForm(request.POST or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        config.first_block_start = form.cleaned_data.get("master_start", config.master_start)
        config.save(update_fields=["first_block_start"])
        return redirect("onboarding_blocks")
    return render(request, "lifeos/onboarding_vision.html", _shell_context(request, "Step 1: Your Vision", vision_form=form))


@login_required
def onboarding_blocks(request):
    blocks = Block.objects.all()
    if request.method == "POST":
        block_count = int(request.POST.get("block_count", 3))
        return render(request, "lifeos/onboarding_blocks_form.html", _shell_context(request, "Step 2: Your Blocks", block_count=block_count, blocks=blocks))
    return render(request, "lifeos/onboarding_blocks.html", _shell_context(request, "Step 2: Your Blocks", blocks=blocks))


@login_required
@require_POST
def onboarding_save_blocks(request):
    block_count = int(request.POST.get("block_count", 0))
    Block.objects.all().delete()
    for i in range(1, block_count + 1):
        name = request.POST.get(f"block_{i}_name", f"Block {i}")
        start_date = request.POST.get(f"block_{i}_start_date")
        deadline = request.POST.get(f"block_{i}_deadline")
        if start_date and deadline:
            Block.objects.create(number=i, name=name, start_date=date.fromisoformat(start_date), deadline=date.fromisoformat(deadline))
    messages.success(request, f"Created {block_count} blocks.")
    return redirect("onboarding_pillars")


@login_required
def onboarding_pillars(request):
    pillars = Pillar.objects.prefetch_related("stages").all()
    if request.method == "POST":
        pillar_count = int(request.POST.get("pillar_count", 1))
        return render(
            request,
            "lifeos/onboarding_pillars_form.html",
            _shell_context(request, "Step 3: Your Pillars", pillar_count=pillar_count, pillars=pillars),
        )
    return render(request, "lifeos/onboarding_pillars.html", _shell_context(request, "Step 3: Your Pillars", pillars=pillars))


@login_required
@require_POST
def onboarding_save_pillars(request):
    pillar_count = int(request.POST.get("pillar_count", 0))
    Pillar.objects.all().delete()
    for i in range(1, pillar_count + 1):
        name = request.POST.get(f"pillar_{i}_name", f"Pillar {i}")
        slug = request.POST.get(f"pillar_{i}_slug", name.lower().replace(" ", "-"))
        description = request.POST.get(f"pillar_{i}_description", "")
        pillar = Pillar.objects.create(name=name, slug=slug, order=i, description=description)
        Stage.objects.create(pillar=pillar, number=1, title="Stage 1", vision="", mission="")
    messages.success(request, f"Created {pillar_count} pillars. You can add more stages later from the pillar detail page.")
    return redirect("onboarding_complete")


@login_required
def onboarding_complete(request):
    config = VisionConfig.get_solo()
    blocks = Block.objects.all()
    pillars = Pillar.objects.prefetch_related("stages").all()
    return render(request, "lifeos/onboarding_complete.html", _shell_context(request, "Setup Complete", config=config, blocks=blocks, pillars=pillars))


@login_required
def features_page(request):
    from .module_registry import initialize_user_modules, get_module_data_count

    initialize_user_modules(request.user)

    all_modules = get_all_modules()
    enabled_modules = get_enabled_modules(request.user)

    modules_with_status = []
    for module_key, module_info in all_modules.items():
        status = get_module_status(request.user, module_key)
        data_count = get_module_data_count(request.user, module_key)
        modules_with_status.append(
            {
                "key": module_key,
                "name": module_info["name"],
                "description": module_info["description"],
                "icon": module_info["icon"],
                "url_name": module_info["url_name"],
                "dependencies": module_info["dependencies"],
                "setup_url": module_info.get("setup_url"),
                "is_enabled": module_key in enabled_modules,
                "status": status,
                "data_count": data_count,
            }
        )

    return render(request, "lifeos/features.html", _shell_context(request, "Features", modules=modules_with_status))


@login_required
def enable_module_view(request, module_key):
    from .module_registry import enable_module, get_module_info, is_module_enabled

    module_info = get_module_info(module_key)
    if not module_info:
        messages.error(request, "Unknown module.")
        return redirect("features")

    for dep in module_info["dependencies"]:
        if not is_module_enabled(request.user, dep):
            messages.warning(request, f"Please enable {dep} first.")
            return redirect("features")

    enable_module(request.user, module_key)
    messages.success(request, f"{module_info['name']} has been enabled.")
    return redirect("features")


@login_required
def disable_module_view(request, module_key):
    from .module_registry import disable_module, get_module_info

    module_info = get_module_info(module_key)
    if not module_info:
        messages.error(request, "Unknown module.")
        return redirect("features")

    disable_module(request.user, module_key)
    messages.success(request, f"{module_info['name']} has been disabled. Your data is preserved.")
    return redirect("features")
