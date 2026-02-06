from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_superuser(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("Email is required."))
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_role", "admin")

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, **extra_fields):
        if not email:
            raise ValueError(_("Email is required."))
        extra_fields.setdefault("is_active", False)
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(user.password)
        user.save(using=self._db)
        return user


