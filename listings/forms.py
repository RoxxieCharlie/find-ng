from django import forms


class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '080X XXX XXXX'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Emeka Johnson'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '080X XXX XXXX'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Choose a password'})
    )

ROLE_CHOICES = [
    ('owner', 'Owner'),
    ('manager', 'Manager'),
    ('staff', 'Staff member'),
    ('representative', 'Representative'),
]

VERIFICATION_CHOICES = [
    ('business_phone', 'Business phone number — the number known to customers'),
    ('cac', 'CAC registration number (if registered)'),
    ('other', 'Other — I will explain during the verification call'),
]

class ClaimForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Emeka Johnson'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '080X XXX XXXX'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='owner'
    )
    verification_method = forms.ChoiceField(
        choices=VERIFICATION_CHOICES,
        initial='business_phone'
    )
    business_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter the number customers use'})
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'e.g. I have been running this place since 2019…'})
    )
    confirm = forms.BooleanField()

    