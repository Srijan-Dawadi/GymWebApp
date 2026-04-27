from django import forms
from .models import Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['full_name', 'phone', 'email', 'photo', 'join_date', 'membership_plan']
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        # On create (no existing instance), a photo is required
        if not photo and not self.instance.pk:
            raise forms.ValidationError("Please capture a photo of the member.")
        return photo
