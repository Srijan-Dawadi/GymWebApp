from django import forms
from .models import Member, MembershipPlan


class MemberForm(forms.ModelForm):
    face_descriptor = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Member
        fields = ['full_name', 'phone', 'email', 'photo', 'face_descriptor', 'join_date', 'membership_plan']
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_face_descriptor(self):
        import json
        data = self.cleaned_data.get('face_descriptor')
        if not data:
            raise forms.ValidationError("Face descriptor is required. Please capture your face using the webcam.")
        try:
            descriptor = json.loads(data)
            if not isinstance(descriptor, list) or len(descriptor) != 128:
                raise forms.ValidationError("Invalid face descriptor format.")
        except (json.JSONDecodeError, TypeError):
            raise forms.ValidationError("Invalid face descriptor data.")
        return descriptor
