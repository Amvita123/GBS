from django.db import models
from .common import CommonFields


class Skill(CommonFields):
    CATEGORY_CHOICES = [
        ('Shooting', 'Shooting'),
        ('Dribbling', 'Dribbling'),
        ('Defense', 'Defense'),
        ('Passing', 'Passing'),
        ('Rebounding', 'Rebounding'),
        ('Ball Handling', 'Ball Handling'),
        ('Footwork', 'Footwork'),
        ('Speed & Agility', 'Speed & Agility'),
        ('Team Play', 'Team Play'),
        ('Jumping', 'Jumping'),
        ('Defending', 'Defending'),
        ('Layups', 'Layups'),
        ('Foot Movement', 'Foot Movement'),
        ('Blocking', 'Blocking'),
        ('Bounce Pass', 'Bounce Pass'),
        ('Chest Pass', 'Chest Pass'),
        ('Overhead Pass', 'Overhead Pass'),
        ('Jump Shot', 'Jump Shot'),
        ('Running with the balls', 'Running with the balls'),
        ('stealing', 'stealing'),
        ('Form Shooting', 'Form shooting'),
        ('Shots', 'Shots'),
        ('Bank Shot', 'Bank Shot'),
        ('Defensive Slides', 'Defensive Slides'),
        ('Behind the back-crossover(towards middle)', 'Behind the back-crossover(towards middle)'),
        ('Agility(defense drills)', 'Agility(defense drills)'),
        ('Screens', 'Screens'),
    ]
    name = models.CharField(max_length=255, help_text="Enter the name of skill")
    description = models.TextField(help_text="Provide a brief description of the skill")
    level = models.CharField(max_length=50, choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ], help_text="Select the skill difficulty level")
    file_url = models.FileField(blank=True, null=True, help_text="Provide a link to a video demonstration (optional)")

    def __str__(self):
        return f"{self.name} "
