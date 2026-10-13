from datetime import date, timedelta


BLOCK_NAMES = [
    "Foundation",
    "Discipline",
    "Strength",
    "Capability",
    "Financial & Professional Growth",
    "Optimization",
    "Expansion",
    "Leadership & Responsibility",
    "Stability & Refinement",
    "Vision 30",
]

PILLAR_DATA = [
    ("mental", "Mental & Intelligence", "Build focused learning, self-awareness, and structured thinking."),
    ("physical", "Physical Health", "Establish exercise, nutrition, sleep, and recovery."),
    ("spiritual", "Islamic & Spiritual Life", "Establish consistent worship, Qur'an engagement, and Islamic learning."),
    ("financial", "Financial Stability", "Establish awareness and control of personal and business finances."),
    ("personal", "Personal Development", "Establish personal development and life-management systems."),
    ("character", "Character & Discipline", "Develop reliability, responsibility, patience, and discipline."),
    ("family", "Family & Relationships", "Improve presence, communication, trust, and responsibility."),
    ("business", "Business & Professional Life", "Establish focused work, professional learning, and business operating systems."),
]


def block_dates(first_start, number):
    start = first_start + timedelta(days=100 * (number - 1))
    return start, start + timedelta(days=99)


def timeline_summary(master_start, master_deadline, first_block_start, blocks):
    total_days = (master_deadline - master_start).days + 1
    covered = sum((block.deadline - block.start_date).days + 1 for block in blocks)
    before = max(0, (first_block_start - master_start).days)
    after = max(0, (master_deadline - max((block.deadline for block in blocks), default=first_block_start)).days)
    return {
        "total_days": total_days,
        "block_days": covered,
        "before_days": before,
        "after_days": after,
        "unallocated_days": max(0, total_days - covered),
    }


def default_mission(slug):
    return next(mission for key, _name, mission in PILLAR_DATA if key == slug)


def as_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
