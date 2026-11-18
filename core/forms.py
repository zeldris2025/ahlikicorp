from django import forms
from .captcha import verify_recaptcha
from .models import ContactMessage, NewsletterSubscriber

class ContactForm(forms.ModelForm):
    def __init__(self, *args, captcha_token=None, remote_ip=None, **kwargs):
        super().__init__(*args, **kwargs)
        # The checkbox posts its own field, outside this form's fields.
        self.captcha_token = captcha_token
        self.remote_ip = remote_ip

    def clean(self):
        cleaned = super().clean()
        if self.is_bound and not verify_recaptcha(self.captcha_token, self.remote_ip):
            raise forms.ValidationError(
                "Please tick \"I'm not a robot\" before sending your message.",
                code='captcha',
            )
        return cleaned

    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'phone', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Phone (optional)'}),
            'subject': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'rows': 5, 'placeholder': 'Your message'}),
        }

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Your email'}),
        }
