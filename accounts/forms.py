from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomerApplication, UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False, max_length=30)
    last_name = forms.CharField(required=False, max_length=150)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('company', 'phone', 'address', 'city', 'island')

class UserUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Email address'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Password'
    }))


class CustomerApplicationForm(forms.ModelForm):
    """Apply for a trade account.

    No password fields: the applicant never chooses one. An administrator
    reviews the application and the system generates the credentials, so this
    form cannot create a usable login by itself.
    """

    MAX_DOCUMENT_MB = 10
    ALLOWED_DOCUMENT_TYPES = ('.pdf', '.jpg', '.jpeg', '.png', '.webp', '.heic')

    class Meta:
        model = CustomerApplication
        fields = ('full_name', 'organisation', 'email', 'phone', 'document')
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'e.g. Sione Faleolo', 'autocomplete': 'name'}),
            'organisation': forms.TextInput(attrs={'placeholder': 'e.g. Ministry of Health', 'autocomplete': 'organization'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@organisation.ws', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'placeholder': '+685 …', 'autocomplete': 'tel'}),
            'document': forms.FileInput(attrs={'accept': '.pdf,image/*'}),
        }
        labels = {
            'full_name': 'Full name',
            'organisation': 'Company / Ministry / Institution',
            'email': 'Email address',
            'phone': 'Phone number',
            'document': 'Business licence or ID',
        }
        help_texts = {
            'email': 'Your sign-in details will be sent here once approved.',
            'document': 'PDF or photo, up to 10MB. Business licence, company registration or a photo ID.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'f-input' if name != 'document' else 'f-input f-file'
            field.widget.attrs['class'] = css
            field.required = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'There is already an account for this email address. Try signing in instead.'
            )
        if CustomerApplication.objects.filter(
            email__iexact=email, status=CustomerApplication.Status.PENDING
        ).exists():
            raise forms.ValidationError(
                'An application for this email address is already under review.'
            )
        return email

    def clean_document(self):
        document = self.cleaned_data['document']

        # A size cap belongs here rather than only in the web server config:
        # the limit the applicant is told about should be the one enforced.
        if document.size > self.MAX_DOCUMENT_MB * 1024 * 1024:
            raise forms.ValidationError(
                f'That file is larger than {self.MAX_DOCUMENT_MB}MB. Please upload a smaller copy.'
            )

        name = (document.name or '').lower()
        if not name.endswith(self.ALLOWED_DOCUMENT_TYPES):
            raise forms.ValidationError('Please upload a PDF or an image.')
        return document
