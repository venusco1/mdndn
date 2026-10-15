import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .dates import BLOCK_NAMES, block_dates, timeline_summary
from .forms import BlockForm, VisionConfigForm
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
    Pillar,
    PillarDailyLog,
    Review,
    Stage,
    Task,
    VisionConfig,
)


class VisionTimelineTests(TestCase):
    def test_master_day_number_counts_start_as_day_one(self):
        config = VisionConfig(
            master_start=date(2026, 10, 6),
            master_deadline=date(2029, 7, 18),
        )
        self.assertEqual(config.day_number(date(2026, 10, 6)), 1)
        self.assertEqual(config.day_number(date(2026, 10, 15)), 10)
        self.assertEqual(config.day_number(date(2029, 7, 18)), 1017)
        self.assertIsNone(config.day_number(date(2026, 10, 5)))
        self.assertIsNone(config.day_number(date(2029, 7, 19)))
        self.assertEqual(config.days_remaining(date(2029, 7, 18)), 0)

    def test_block_dates_and_buffer_are_calculated_without_stretching(self):
        first_start = date(2026, 10, 15)
        first_dates = block_dates(first_start, 1)
        last_dates = block_dates(first_start, 10)
        self.assertEqual(first_dates, (date(2026, 10, 15), date(2027, 1, 22)))
        self.assertEqual(last_dates, (date(2029, 4, 2), date(2029, 7, 10)))
        self.assertEqual((last_dates[1] - date(2026, 10, 6)).days, 1008)

        class CalendarBlock:
            def __init__(self, start_date, deadline):
                self.start_date = start_date
                self.deadline = deadline

        blocks = [CalendarBlock(*block_dates(first_start, number)) for number in range(1, 11)]
        summary = timeline_summary(date(2026, 10, 6), date(2029, 7, 18), first_start, blocks)
        self.assertEqual(summary, {
            "total_days": 1017,
            "block_days": 1000,
            "before_days": 9,
            "after_days": 8,
            "unallocated_days": 17,
        })


class FrameworkSeedTests(TestCase):
    def test_seed_is_complete_idempotent_and_has_no_fake_activity(self):
        call_command("seed_vision30", verbosity=0)
        call_command("seed_vision30", verbosity=0)
        self.assertEqual(Pillar.objects.count(), 8)
        self.assertEqual(Stage.objects.count(), 80)
        self.assertEqual(Block.objects.count(), 10)
        self.assertEqual(BlockPillarMission.objects.count(), 80)
        self.assertEqual(list(Block.objects.values_list("name", flat=True)), BLOCK_NAMES)
        first = Block.objects.get(number=1)
        self.assertEqual(first.start_date, date(2026, 10, 15))
        self.assertEqual(first.deadline, date(2027, 1, 22))
        self.assertEqual(first.pillar_missions.count(), 8)
        self.assertEqual(DailyPriority.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(Goal.objects.count(), 0)
        self.assertEqual(Habit.objects.count(), 0)
        self.assertEqual(JournalEntry.objects.count(), 0)
        self.assertEqual(PillarDailyLog.objects.count(), 0)

    def test_invalid_block_and_config_dates_are_rejected(self):
        invalid_block = BlockForm({
            "name": "Broken block",
            "start_date": "2027-02-01",
            "deadline": "2027-01-31",
            "vision": "",
            "mission": "",
            "objectives": "",
            "weekly_targets": "",
            "monthly_milestones": "",
            "definition_of_done": "",
            "status": Block.Status.PLANNED,
            "final_review": "",
            "lessons_learned": "",
            "next_recommendations": "",
        })
        self.assertFalse(invalid_block.is_valid())
        self.assertIn("deadline", invalid_block.errors)

        invalid_config = VisionConfigForm({
            "name": "Vision 30",
            "master_start": "2026-10-07",
            "master_deadline": "2026-10-06",
            "first_block_start": "2026-10-05",
            "master_vision": "Build a stable foundation.",
            "timezone_name": "Asia/Kolkata",
            "enable_mood_energy": "on",
            "theme": VisionConfig.Theme.DARK,
        })
        self.assertFalse(invalid_config.is_valid())
        self.assertIn("master_deadline", invalid_config.errors)
        self.assertIn("first_block_start", invalid_config.errors)


class LifeOSWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_vision30", verbosity=0)
        cls.user = get_user_model().objects.create_user(username="owner", password="a-secure-test-password-42")

    def setUp(self):
        self.client.force_login(self.user)

    def test_read_only_home_and_user_guide_are_public(self):
        self.client.logout()

        home = self.client.get(reverse("home"))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, "Turn vision into")
        self.assertContains(home, reverse("user_guide"))

        guide = self.client.get(reverse("user_guide"))
        self.assertEqual(guide.status_code, 200)
        self.assertContains(guide, "Getting Started")
        self.assertContains(guide, reverse("today"))

        private_page = self.client.get(reverse("today"))
        self.assertEqual(private_page.status_code, 302)
        self.assertIn(reverse("login"), private_page.url)

    def test_app_requires_login_and_renders_every_primary_page(self):
        self.client.logout()
        response = self.client.get(reverse("today"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.client.force_login(self.user)

        urls = [
            "today", "dashboard", "overview", "vision", "blocks", "pillars",
            "goals_tasks", "tasks", "habits", "life", "reviews", "journal",
            "progress", "archive", "settings",
        ]
        for name in urls:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

        block = Block.objects.get(number=1)
        pillar = Pillar.objects.get(slug="mental")
        self.assertEqual(self.client.get(reverse("block_detail", args=[block.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("pillar_detail", args=[pillar.pk])).status_code, 200)

    def test_daily_checkin_task_habit_priority_and_journal_persist(self):
        today = date(2026, 10, 16)
        from django.utils import timezone

        with timezone.override("Asia/Kolkata"):
            pillar = Pillar.objects.get(slug="mental")
            response = self.client.post(reverse("save_pillar_daily", args=[pillar.pk]), {
                "status": "completed", "reflection": "Practised focused reading", "outcome_note": "Finished one lesson",
            })
            self.assertEqual(response.status_code, 302)
            self.assertTrue(PillarDailyLog.objects.filter(pillar=pillar, status="completed").exists())

            task_response = self.client.post(reverse("create_task"), {
                "title": "Plan next action", "description": "", "status": "todo", "priority": "high",
                "due_date": today.isoformat(), "pillar": str(pillar.pk), "block": "",
                "goal": "", "next": "today",
            })
            self.assertEqual(task_response.status_code, 302)
            task = Task.objects.get(title="Plan next action")
            self.client.post(reverse("update_task", args=[task.pk]), {"status": "completed", "next": "today"})
            task.refresh_from_db()
            self.assertEqual(task.status, Task.Status.COMPLETED)

            self.client.post(reverse("save_daily_priority"), {"rank": "1", "title": "Complete one important task"})
            self.assertTrue(DailyPriority.objects.filter(rank=1).exists())

            self.client.post(reverse("create_habit"), {"title": "Walk", "description": "", "pillar": str(pillar.pk), "active": "on"})
            habit = Habit.objects.get(title="Walk")
            self.client.post(reverse("toggle_habit", args=[habit.pk]), {"next": "today"})
            self.assertEqual(HabitCheckIn.objects.filter(habit=habit).count(), 1)
            self.client.post(reverse("toggle_habit", args=[habit.pk]), {"next": "today"})
            self.assertEqual(HabitCheckIn.objects.filter(habit=habit).count(), 0)

            self.client.post(reverse("create_journal"), {
                "date": today.isoformat(), "title": "First reflection", "mood": "focused",
                "text": "A real reflection.", "decision": "", "pillar": str(pillar.pk),
            })
            self.assertTrue(JournalEntry.objects.filter(title="First reflection").exists())

    def test_daily_reflection_saves_only_real_execution_scores(self):
        day = date(2026, 10, 16)
        pillar = Pillar.objects.get(slug="mental")
        PillarDailyLog.objects.create(pillar=pillar, date=day, status=PillarDailyLog.Status.COMPLETED)
        DailyPriority.objects.create(date=day, rank=1, title="Read a lesson", completed=False)
        with patch("lifeos.views.timezone.localdate", return_value=day):
            response = self.client.post(reverse("save_daily_review"), {
                "mood": "focused", "energy": "4", "evening_reflection": "A considered day.",
                "wins": "", "improvement": "",
            })
        self.assertEqual(response.status_code, 302)
        review = DailyReview.objects.get(date=day)
        self.assertEqual(review.execution_score, Decimal("50.00"))

        progress_response = self.client.get(reverse("progress"))
        self.assertContains(progress_response, "Execution consistency")
        self.assertContains(progress_response, "aria-valuenow=\"50\"")
        self.assertContains(progress_response, "2026-10-16")

        empty_day = date(2026, 10, 17)
        with patch("lifeos.views.timezone.localdate", return_value=empty_day):
            response = self.client.post(reverse("save_daily_review"), {
                "mood": "", "energy": "", "evening_reflection": "", "wins": "", "improvement": "",
            })
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(DailyReview.objects.get(date=empty_day).execution_score)

    def test_goals_targets_reviews_and_explicit_completion(self):
        block = Block.objects.get(number=1)
        pillar = Pillar.objects.get(slug="physical")
        response = self.client.post(reverse("create_target"), {
            "title": "Movement sessions", "block": str(block.pk), "pillar": str(pillar.pk),
            "stage": "", "unit": "sessions", "target_value": "12", "current_value": "12",
            "due_date": "2027-01-01", "completion_criteria": "Record sessions",
            "evidence": "", "status": "in_progress",
        })
        self.assertEqual(response.status_code, 302)
        target = MeasurableTarget.objects.get(title="Movement sessions")
        self.assertEqual(target.progress_percent, 100)
        self.assertEqual(target.status, MeasurableTarget.Status.IN_PROGRESS)

        response = self.client.post(reverse("save_review"), {
            "kind": "weekly", "period_start": "2026-10-12", "period_end": "2026-10-18",
            "block": "", "eight_pillar_performance": "Separate assessments.",
            "wins": "A real win", "execution_consistency": "3 of 4 planned actions.",
            "outcome_progress": "One measured result.", "target_progress": "", "problems": "",
            "missed_commitments": "", "corrective_actions": "", "trends": "", "achievements": "",
            "risks": "", "next_milestones": "", "target_evaluation": "", "evidence": "",
            "completed_missions": "", "incomplete_missions": "", "lessons_learned": "",
            "next_recommendations": "",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(kind="weekly", wins="A real win").exists())

    def test_legacy_import_is_additive_and_idempotent(self):
        payload = {
            "tasks": [{"id": "old-1", "title": "Imported task", "status": "todo", "priority": "high", "dueDate": ""}],
            "goals": [{"id": "old-goal", "title": "Imported outcome", "target": 5, "current": 2, "pillar": "financial"}],
            "habits": [{"id": "old-habit", "title": "Imported practice", "history": ["2026-10-12"]}],
            "journal": [{"date": "2026-10-12", "text": "Imported note", "mood": "calm"}],
            "history": [{"date": "2026-10-12", "scores": {"mental": 2, "physical": 1}}],
            "big3": ["Imported priority"],
        }
        raw = json.dumps(payload).encode()
        from django.core.files.uploadedfile import SimpleUploadedFile

        def upload():
            return SimpleUploadedFile("legacy.json", raw, content_type="application/json")

        response = self.client.post(reverse("import_backup"), {"import-backup": upload(), "import-reviewed": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.filter(title="Imported task").count(), 1)
        self.assertEqual(Goal.objects.filter(title="Imported outcome").count(), 1)
        self.assertEqual(HabitCheckIn.objects.count(), 1)
        self.assertEqual(JournalEntry.objects.filter(text="Imported note").count(), 1)
        self.assertTrue(PillarDailyLog.objects.filter(pillar__slug="mental", status="completed").exists())
        self.assertFalse(PillarDailyLog.objects.filter(pillar__slug="family").exists())
        self.assertEqual(ImportBatch.objects.count(), 1)

        self.client.post(reverse("import_backup"), {"import-backup": upload(), "import-reviewed": "on"})
        self.assertEqual(Task.objects.filter(title="Imported task").count(), 1)
        self.assertEqual(ImportBatch.objects.count(), 1)

    def test_export_contains_framework_and_personal_data(self):
        DailyReview.objects.create(date=date(2026, 10, 12), execution_score=Decimal("62.50"))
        response = self.client.get(reverse("export_backup"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(len(data["blocks"]), 10)
        self.assertEqual(len(data["pillars"]), 8)
        self.assertEqual(len(data["stages"]), 80)
        self.assertEqual(data["daily_reviews"][0]["execution_score"], "62.50")

    def test_version_two_backup_restores_relationships_and_history(self):
        payload = {
            "schema_version": 2,
            "config": {"name": "Vision 30"},
            "pillars": [],
            "blocks": [],
            "stages": [{"id": 501, "pillar": "mental", "number": 1, "title": "Restored Stage"}],
            "missions": [{"id": 601, "block": 1, "pillar": "mental", "stage": 501, "mission": "Restored mission"}],
            "targets": [{
                "id": 701, "title": "Learning hours", "block": 1, "pillar": "mental", "stage": 501,
                "unit": "hours", "target_value": "10.00", "current_value": "4.00", "due_date": "2027-01-01",
                "completion_criteria": "Maintain a log", "evidence": "Four hours", "status": "in_progress",
            }],
            "milestones": [{"id": 801, "title": "First milestone", "block": 1, "pillar": "mental", "due_date": "2027-01-01"}],
            "goals": [{
                "id": 901, "title": "Study goal", "pillar": "mental", "block": 1, "target": "20.00",
                "current": "5.00", "unit": "hours", "deadline": "2027-01-01",
            }],
            "tasks": [{
                "id": 1001, "title": "Read lesson", "status": "todo", "priority": "high",
                "pillar": "mental", "block": 1, "goal": 901, "due_date": "2026-10-20",
            }],
            "habits": [{"id": 1101, "title": "Reading", "pillar": "mental", "active": True}],
            "habit_checkins": [{"id": 1201, "habit": 1101, "date": "2026-10-12"}],
            "pillar_daily_logs": [{
                "id": 1301, "pillar": "mental", "date": "2026-10-12", "status": "completed",
                "reflection": "Read", "outcome_note": "Finished a chapter",
            }],
            "daily_priorities": [{"id": 1401, "date": "2026-10-12", "rank": 1, "title": "Study", "completed": True}],
            "daily_reviews": [{
                "id": 1501, "date": "2026-10-12", "mood": "focused", "energy": 4,
                "evening_reflection": "Good day", "wins": "Read", "improvement": "Plan earlier",
                "execution_score": "62.50",
            }],
            "reviews": [{
                "id": 1601, "kind": "weekly", "period_start": "2026-10-12", "period_end": "2026-10-18",
                "block": None, "wins": "Good week", "outcome_progress": "Evidence recorded",
            }],
            "journal": [{
                "id": 1701, "date": "2026-10-12", "title": "Thoughts", "mood": "calm",
                "text": "A note", "decision": "Continue", "pillar": "mental",
            }],
            "archive": [{
                "id": 1801, "date": "2026-10-12", "kind": "achievement", "title": "Saved note",
                "text": "Archived", "pillar": "mental",
            }],
            "stage_reviews": [{
                "id": 1901, "stage": 501, "reviewed_at": "2026-10-12", "evaluation": "On track",
                "evidence": "Study log", "lessons": "Short sessions work", "recommendations": "Continue",
            }],
        }
        from django.core.files.uploadedfile import SimpleUploadedFile

        response = self.client.post(reverse("import_backup"), {
            "import-backup": SimpleUploadedFile("vision30.json", json.dumps(payload).encode(), content_type="application/json"),
            "import-reviewed": "on",
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title="Read lesson")
        self.assertEqual(task.goal.title, "Study goal")
        self.assertEqual(task.block.number, 1)
        self.assertTrue(HabitCheckIn.objects.filter(habit__title="Reading", date=date(2026, 10, 12)).exists())
        self.assertTrue(ArchiveEntry.objects.filter(title="Saved note").exists())
        self.assertTrue(Stage.objects.filter(title="Restored Stage", pillar__slug="mental", number=1).exists())
        self.assertTrue(BlockPillarMission.objects.filter(block__number=1, pillar__slug="mental", mission="Restored mission").exists())
        self.assertTrue(MeasurableTarget.objects.filter(title="Learning hours", stage__title="Restored Stage").exists())
        self.assertEqual(JournalEntry.objects.get(title="Thoughts").decision, "Continue")
        self.assertEqual(Review.objects.get(wins="Good week").outcome_progress, "Evidence recorded")
        daily_review = DailyReview.objects.get(date=date(2026, 10, 12))
        self.assertEqual(daily_review.energy, 4)
        self.assertEqual(daily_review.execution_score, Decimal("62.50"))
