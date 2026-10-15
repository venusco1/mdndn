from .models import UserModulePreference


MODULE_REGISTRY = {
    "vision": {
        "name": "Vision 30",
        "description": "Manage your long-term vision, set deadlines, and track progress across multiple years.",
        "icon": "🎯",
        "url_name": "vision",
        "dependencies": [],
        "data_models": ["Block", "Pillar", "Stage"],
        "setup_url": "onboarding_vision",
    },
    "blocks": {
        "name": "Blocks",
        "description": "Divide your vision into structured time periods with specific goals and milestones.",
        "icon": "📅",
        "url_name": "blocks",
        "dependencies": ["vision"],
        "data_models": ["Block"],
        "setup_url": "onboarding_blocks",
    },
    "pillars": {
        "name": "Pillars",
        "description": "Organize your life into major areas (health, career, relationships, etc.) with progressive stages.",
        "icon": "🏛️",
        "url_name": "pillars",
        "dependencies": [],
        "data_models": ["Pillar", "Stage"],
        "setup_url": "onboarding_pillars",
    },
    "goals": {
        "name": "Goals & Targets",
        "description": "Define measurable outcomes and track your progress with specific targets.",
        "icon": "🎯",
        "url_name": "goals_tasks",
        "dependencies": [],
        "data_models": ["Goal", "MeasurableTarget"],
        "setup_url": "goals_tasks",
    },
    "tasks": {
        "name": "Tasks",
        "description": "Manage actionable work with priorities, due dates, and completion tracking.",
        "icon": "✅",
        "url_name": "tasks",
        "dependencies": [],
        "data_models": ["Task"],
        "setup_url": "tasks",
    },
    "habits": {
        "name": "Habits",
        "description": "Track recurring behaviors and build consistency with daily check-ins.",
        "icon": "🔄",
        "url_name": "habits",
        "dependencies": [],
        "data_models": ["Habit", "HabitCheckIn"],
        "setup_url": "habits",
    },
    "reviews": {
        "name": "Reviews",
        "description": "Conduct weekly, monthly, and block reviews to evaluate your progress.",
        "icon": "📊",
        "url_name": "reviews",
        "dependencies": [],
        "data_models": ["Review", "DailyReview"],
        "setup_url": "reviews",
    },
    "journal": {
        "name": "Journal",
        "description": "Record daily thoughts, reflections, and decisions to track your journey.",
        "icon": "📝",
        "url_name": "journal",
        "dependencies": [],
        "data_models": ["JournalEntry"],
        "setup_url": "journal",
    },
    "progress": {
        "name": "Progress & Analytics",
        "description": "Review performance statistics, track execution scores, and analyze trends.",
        "icon": "📈",
        "url_name": "progress",
        "dependencies": [],
        "data_models": ["DailyReview", "Review", "MeasurableTarget", "Goal"],
        "setup_url": "progress",
    },
    "archive": {
        "name": "Archive",
        "description": "Store achievements, milestones, memories, and completed reviews for reference.",
        "icon": "🗄️",
        "url_name": "archive",
        "dependencies": [],
        "data_models": ["ArchiveEntry"],
        "setup_url": "archive",
    },
}


def get_module_info(module_key):
    """Get module information from the registry."""
    return MODULE_REGISTRY.get(module_key)


def get_all_modules():
    """Get all available modules."""
    return MODULE_REGISTRY


def get_enabled_modules(user):
    """Get list of enabled module keys for a user."""
    return list(
        UserModulePreference.objects.filter(user=user, is_enabled=True).values_list("module_key", flat=True)
    )


def is_module_enabled(user, module_key):
    """Check if a module is enabled for a user."""
    return UserModulePreference.objects.filter(user=user, module_key=module_key, is_enabled=True).exists()


def enable_module(user, module_key):
    """Enable a module for a user."""
    preference, created = UserModulePreference.objects.get_or_create(user=user, module_key=module_key, defaults={"is_enabled": True})
    if not created and not preference.is_enabled:
        preference.is_enabled = True
        preference.save()
    return preference


def disable_module(user, module_key):
    """Disable a module for a user (preserves data)."""
    preference = UserModulePreference.objects.filter(user=user, module_key=module_key).first()
    if preference:
        preference.is_enabled = False
        preference.save()
    return preference


def get_module_data_count(user, module_key):
    """Get the count of records for a module's data models."""
    from django.apps import apps

    module_info = get_module_info(module_key)
    if not module_info:
        return 0

    total_count = 0
    for model_name in module_info.get("data_models", []):
        try:
            model = apps.get_model("lifeos", model_name)
            total_count += model.objects.count()
        except LookupError:
            pass
    return total_count


def get_module_status(user, module_key):
    """Get the status of a module for a user."""
    if not is_module_enabled(user, module_key):
        return "disabled"

    data_count = get_module_data_count(user, module_key)
    if data_count == 0:
        return "empty"
    return "in_use"


def initialize_user_modules(user):
    """Initialize default module preferences for a new user."""
    for module_key in MODULE_REGISTRY.keys():
        UserModulePreference.objects.get_or_create(user=user, module_key=module_key, defaults={"is_enabled": False})
