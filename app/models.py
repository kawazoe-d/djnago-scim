from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_extensions.db.models import TimeStampedModel
from django_scim.models import AbstractSCIMGroupMixin, AbstractSCIMUserMixin


class Company(models.Model):
    name = models.CharField(
        _('Name'),
        max_length=100,
    )

class UserManager(BaseUserManager):
    """ユーザーマネージャー."""

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        """メールアドレスでの登録を必須にする"""
        if not username:#
            raise ValueError('Users must have an name')
        username = self.model.normalize_username(username)
        

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):#
        """is_staff(管理サイトにログインできるか)と、is_superuer(全ての権限)をFalseに"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)#

    def create_superuser(self, username, password, **extra_fields):#
        """スーパーユーザーは、is_staffとis_superuserをTrueに"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)#


class User(AbstractSCIMUserMixin, TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    # company = models.ForeignKey(
    #     'app.Company',
    #     on_delete=models.CASCADE,
    # )

    # Why override this? Can't we just use what the AbstractSCIMUser mixin
    # gives us? The USERNAME_FIELD needs to be "unique" and for flexibility, 
    # AbstractSCIMUser.username is not unique by default.
    username = models.CharField(
        _('SCIM Username'),
        max_length=254,
        null=True,
        blank=True,
        default=None,
        unique=True,
        help_text=_("A service provider's unique identifier for the user"),
    )

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']
    #nameを入れないとcreatesuperuserで作成できない

    email = models.EmailField(
        _('Email'),
    )

    first_name = models.CharField(
        _('First Name'),
        max_length=100,
    )

    last_name = models.CharField(
        _('Last Name'),
        max_length=100,
    )

    USERNAME_FIELD = 'username'

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.first_name + (' ' + self.last_name[0] if self.last_name else '')


class Group(TimeStampedModel, AbstractSCIMGroupMixin):
    company = models.ForeignKey(
        'app.Company',
        on_delete=models.CASCADE,
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMembership',
        through_fields=('group', 'user'),
    )

    @property
    def name(self):
        return self.scim_display_name


class GroupMembership(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    group = models.ForeignKey(
        to='app.Group',
        on_delete=models.CASCADE
    )
