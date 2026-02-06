from django.db import models


class SchoolGrade(models.Model):
    # code = models.CharField(max_length=4, unique=True, help_text="Short code e.g. K, 1, 2, ..., 12")
    name = models.CharField(max_length=32, help_text="such as 2025, 2026", unique=True)

    def __str__(self):
        return self.name


