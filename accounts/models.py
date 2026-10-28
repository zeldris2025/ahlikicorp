from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=255, blank=True, help_text="Company name for B2B users")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    island = models.CharField(max_length=100, blank=True, help_text="Samoan island")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} Profile"

    class Meta:
        verbose_name_plural = "User Profiles"


def application_document_path(instance, filename):
    """Keep uploaded licences in month folders, not one flat directory.

    ``created_at`` is still unset while the first save is in flight, so the
    current date is used for a new application rather than crashing on None.
    """
    from django.utils import timezone
    from django.utils.text import get_valid_filename

    stamp = instance.created_at or timezone.now()
    return f'applications/{stamp:%Y/%m}/{get_valid_filename(filename)}'


class CustomerApplication(models.Model):
    """A request for a trade account, pending review by an administrator.

    Nobody self-registers: an application creates one of these, and the User
    account is only created when an administrator approves it. That is the
    whole point of the gate — a quote can then only ever come from someone
    whose identity and business have been checked by a person.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Declined'

    full_name = models.CharField('full name', max_length=120)
    organisation = models.CharField(
        'company / ministry / institution',
        max_length=160,
    )
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    document = models.FileField(
        'business licence or ID',
        upload_to=application_document_path,
        help_text='Business licence, company registration or a photo ID.',
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    review_notes = models.TextField(
        blank=True,
        help_text='Internal. Included in the decline email only if you choose to send it.',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_applications'
    )
    # Set on approval, so a second approval cannot create a second account.
    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='application'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'customer application'

    def __str__(self):
        return f'{self.full_name} — {self.organisation}'

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING
