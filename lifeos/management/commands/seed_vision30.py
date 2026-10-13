from datetime import date

from django.core.management.base import BaseCommand

from lifeos.dates import BLOCK_NAMES, PILLAR_DATA, block_dates
from lifeos.models import Block, BlockPillarMission, Pillar, Stage, VisionConfig


class Command(BaseCommand):
    help = "Create the editable Vision 30 framework without adding personal activity or progress."

    def handle(self, *args, **options):
        VisionConfig.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Vision 30",
                "master_start": date(2026, 10, 6),
                "master_deadline": date(2029, 7, 18),
                "first_block_start": date(2026, 10, 15),
                "master_vision": "Build a stable foundation for all eight areas of life.",
            },
        )
        pillars = {}
        for order, (slug, name, description) in enumerate(PILLAR_DATA, start=1):
            pillar, _ = Pillar.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "order": order, "description": description},
            )
            pillars[slug] = pillar
            for number in range(1, 11):
                Stage.objects.get_or_create(
                    pillar=pillar,
                    number=number,
                    defaults={
                        "title": f"Stage {number:02d}",
                        "vision": f"Develop {pillar.name.lower()} across Stage {number:02d}.",
                        "mission": description if number == 1 else "",
                    },
                )

        first_start = date(2026, 10, 15)
        for number, name in enumerate(BLOCK_NAMES, start=1):
            start, deadline = block_dates(first_start, number)
            block, _ = Block.objects.get_or_create(
                number=number,
                defaults={
                    "name": name,
                    "start_date": start,
                    "deadline": deadline,
                    "vision": "Build a stable foundation for all eight areas of life." if number == 1 else "",
                    "mission": (
                        "Establish the essential habits, skills, knowledge, and systems required "
                        "to progress to Stage 02 in all eight pillars."
                        if number == 1
                        else ""
                    ),
                    "status": Block.Status.ACTIVE if number == 1 else Block.Status.PLANNED,
                    "definition_of_done": (
                        "Review target-by-target evidence and all eight Stage 01 missions; record "
                        "lessons and recommendations before preparing Block 02."
                        if number == 1
                        else ""
                    ),
                },
            )
            for slug, _name, mission_text in PILLAR_DATA:
                pillar = pillars[slug]
                stage = Stage.objects.get(pillar=pillar, number=number)
                BlockPillarMission.objects.get_or_create(
                    block=block,
                    pillar=pillar,
                    defaults={
                        "stage": stage,
                        "mission": mission_text if number == 1 else "",
                    },
                )
        self.stdout.write(self.style.SUCCESS("Vision 30 framework is ready (8 pillars, 80 stages, 10 blocks)."))
