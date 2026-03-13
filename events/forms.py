from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    end_datetime = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    registration_deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "image",
            "venue",
            "category",
            "start_datetime",
            "end_datetime",
            "registration_deadline",
            "participant_limit",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"category", "status"}:
                field.widget.attrs.setdefault("class", "form-select")
            elif name == "image":
                field.widget.attrs.setdefault("class", "form-control")
                field.widget.attrs.setdefault("accept", "image/*")
            else:
                field.widget.attrs.setdefault("class", "form-control")
        for field_name in ["start_datetime", "end_datetime", "registration_deadline"]:
            value = self.initial.get(field_name) or getattr(self.instance, field_name, None)
            if value:
                self.initial[field_name] = value.strftime("%Y-%m-%dT%H:%M")
