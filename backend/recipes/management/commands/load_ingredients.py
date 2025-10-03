import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов из JSON файла в базу"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Путь к JSON файлу с ингредиентами",
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_path"])

        if not json_path.is_absolute():
            json_path = Path(settings.BASE_DIR) / json_path
        if not json_path.exists():
            self.stderr.write(
                self.style.ERROR(f"Файл не найден: {json_path}")
            )
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        objs = []
        skipped = 0
        seen = set()

        for item in data:
            name = (item.get("name") or "").strip()
            unit = (item.get("measurement_unit") or "").strip()
            if not name or not unit:
                skipped += 1
                continue
            key = (name.lower(), unit.lower())
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            objs.append(Ingredient(name=name, measurement_unit=unit))

        with transaction.atomic():
            created_list = Ingredient.objects.bulk_create(
                objs, ignore_conflicts=True
            )
        created = len(created_list)

        self.stdout.write(
            self.style.SUCCESS(
                f"Загрузка завершена. "
                f"Добавлено: {created}, пропущено: {skipped}"
            )
        )


# class Command(BaseCommand):
#     help = "Загрузка ингредиентов из JSON файла в базу"
#
#     def add_arguments(self, parser):
#         parser.add_argument(
#             "json_path",
#             type=str,
#             help="Путь к JSON файлу с ингредиентами",
#         )
#
#     def handle(self, *args, **options):
#         json_path = Path(options["json_path"])
#         if not json_path.is_absolute():
#             self.stderr.write(
#                 self.style.ERROR(f"Файл {json_path} не найден")
#             )
#             return
#
#         with open(json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#
#         created, skipped = 0, 0
#         objs = []
#         for item in data:
#             name = item["name"].strip()
#             unit = item["measurement_unit"].strip()
#             if not name or not unit:
#                 skipped += 1
#                 continue
#             objs.append(Ingredient(name=name, measurement_unit=unit))
#
#         # bulk_create c ignore_conflicts=True (Django 4.1+)
#         Ingredient.objects.bulk_create(objs, ignore_conflicts=True)
#         created = len(objs)
#
#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"Загрузка завершена. "
#                 f"Добавлено: {created}, пропущено: {skipped}"
#             )
#         )
