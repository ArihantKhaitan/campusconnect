from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import ModelForm

from .models import StudentProfile, User
from organizations.models import Club, College, Department


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control", "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))


class SignupForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Roles.STUDENT, "Student"),
            (User.Roles.CLUB, "Club Representative"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}))
    college = forms.CharField(max_length=255, required=False, label="College", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "College name"}))
    club_name = forms.CharField(max_length=255, required=False, label="Club name", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Club name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}))
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}))

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "college", "club_name", "profile_picture", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Username"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirm password"})

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        if role == User.Roles.CLUB:
            if not cleaned_data.get("club_name"):
                self.add_error("club_name", "Club name is required for club representatives.")
            if not cleaned_data.get("college"):
                self.add_error("college", "College is required for club representatives.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if user.role == User.Roles.STUDENT:
            user.first_name = self.cleaned_data.get("first_name", "")
            user.last_name = self.cleaned_data.get("last_name", "")
        else:
            user.first_name = ""
            user.last_name = ""
        profile_picture = self.cleaned_data.get("profile_picture")
        if profile_picture:
            user.profile_picture = profile_picture
        if commit:
            user.save()
            if user.role == User.Roles.CLUB:
                club_name = self.cleaned_data.get("club_name")
                college_name = self.cleaned_data.get("college")
                if club_name and college_name:
                    college_obj, _ = College.objects.get_or_create(name=college_name)
                    club, created = Club.objects.get_or_create(name=club_name, college=college_obj)
                    club.representative = user
                    club.save(update_fields=["representative"])
        return user


class ProfileEditForm(ModelForm):
    college = forms.ModelChoiceField(queryset=College.objects.all(), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.select_related("college"), required=False)
    club = forms.ModelChoiceField(queryset=Club.objects.select_related("college"), required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    batch = forms.CharField(max_length=20, required=False)
    roll_no = forms.CharField(max_length=50, required=False)
    registration_no = forms.CharField(max_length=50, required=False)
    remove_profile_picture = forms.BooleanField(required=False, label="Remove profile picture")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "profile_picture")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Username"})
        self.fields["first_name"].widget.attrs.update({"class": "form-control", "placeholder": "First name"})
        self.fields["last_name"].widget.attrs.update({"class": "form-control", "placeholder": "Last name"})
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Email address"})
        self.fields["profile_picture"].widget.attrs.update({"class": "form-control", "accept": "image/*"})
        self.fields["college"].widget.attrs.update({"class": "form-select"})
        self.fields["department"].widget.attrs.update({"class": "form-select"})
        self.fields["club"].widget.attrs.update({"class": "form-select"})
        self.fields["batch"].widget.attrs.update({"class": "form-control", "placeholder": "Batch"})
        self.fields["roll_no"].widget.attrs.update({"class": "form-control", "placeholder": "Roll number"})
        self.fields["registration_no"].widget.attrs.update({"class": "form-control", "placeholder": "Registration number"})

        if hasattr(self.user, "student_profile") and self.user.student_profile.college_id:
            self.fields["department"].queryset = Department.objects.filter(college=self.user.student_profile.college)
            self.initial.setdefault("college", self.user.student_profile.college)
            self.initial.setdefault("department", self.user.student_profile.department)
            self.initial.setdefault("batch", self.user.student_profile.batch)
            self.initial.setdefault("roll_no", self.user.student_profile.roll_no)
            self.initial.setdefault("registration_no", self.user.student_profile.registration_no)
        elif self.data.get("college"):
            try:
                self.fields["department"].queryset = Department.objects.filter(college_id=int(self.data.get("college")))
            except (TypeError, ValueError):
                self.fields["department"].queryset = Department.objects.none()
        else:
            self.fields["department"].queryset = Department.objects.none()

        managed_club = self.user.managed_clubs.first()
        if managed_club:
            self.initial.setdefault("club", managed_club)
            self.initial.setdefault("college", managed_club.college)

        if self.user.role != User.Roles.STUDENT:
            self.fields["college"].disabled = True
            self.fields["department"].disabled = True
            self.fields["batch"].disabled = True
            self.fields["roll_no"].disabled = True
            self.fields["registration_no"].disabled = True
        if self.user.role != User.Roles.CLUB:
            self.fields["club"].widget = forms.HiddenInput()
        else:
            self.fields["club"].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        college = cleaned_data.get("college")
        department = cleaned_data.get("department")
        if self.user.role == User.Roles.STUDENT and department and college and department.college_id != college.id:
            self.add_error("department", "Department must belong to the selected college.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if self.cleaned_data.get("remove_profile_picture") and user.profile_picture:
            if user.profile_picture.storage.exists(user.profile_picture.name):
                user.profile_picture.delete(save=False)
            user.profile_picture = None
        if commit:
            user.save()
        if user.role == User.Roles.STUDENT:
            StudentProfile.objects.update_or_create(
                user=user,
                defaults={
                    "college": self.cleaned_data.get("college"),
                    "department": self.cleaned_data.get("department"),
                    "batch": self.cleaned_data.get("batch", ""),
                    "roll_no": self.cleaned_data.get("roll_no", ""),
                    "registration_no": self.cleaned_data.get("registration_no", ""),
                },
            )
        return user


class ProfileSetupForm(forms.Form):
    role = forms.ChoiceField(
        choices=[
            (User.Roles.STUDENT, "Student"),
            (User.Roles.CLUB, "Club Representative"),
        ]
    )
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    profile_picture = forms.ImageField(required=False)
    college = forms.ModelChoiceField(queryset=College.objects.all(), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.select_related("college"), required=False)
    club = forms.ModelChoiceField(queryset=Club.objects.select_related("college"), required=False, label="Club name")
    batch = forms.CharField(max_length=20, required=False)
    roll_no = forms.CharField(max_length=50, required=False)
    registration_no = forms.CharField(max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-select" if isinstance(field, forms.ModelChoiceField) or isinstance(field, forms.ChoiceField) else "form-control")
        self.fields["profile_picture"].widget.attrs.update({"accept": "image/*"})
        self.fields["department"].queryset = Department.objects.none()
        if self.data.get("college"):
            try:
                college_id = int(self.data.get("college"))
                self.fields["department"].queryset = Department.objects.filter(college_id=college_id)
                self.fields["club"].queryset = Club.objects.filter(college_id=college_id)
            except (TypeError, ValueError):
                self.fields["club"].queryset = Club.objects.all()
        elif hasattr(self.user, "student_profile") and self.user.student_profile.college_id:
            college = self.user.student_profile.college
            self.fields["department"].queryset = Department.objects.filter(college=college)
            self.fields["club"].queryset = Club.objects.filter(college=college)
        else:
            self.fields["club"].queryset = Club.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        college = cleaned_data.get("college")
        department = cleaned_data.get("department")
        club = cleaned_data.get("club")

        if role == User.Roles.STUDENT:
            if not college:
                self.add_error("college", "College is required for students.")
            if department and college and department.college_id != college.id:
                self.add_error("department", "Department must belong to the selected college.")
        elif role == User.Roles.CLUB:
            if not club:
                self.add_error("club", "Club name is required for club representatives.")
            if college and club and club.college_id != college.id:
                self.add_error("club", "Club must belong to the selected college.")
        return cleaned_data

    def save(self):
        role = self.cleaned_data["role"]
        college = self.cleaned_data.get("college")
        department = self.cleaned_data.get("department")
        club = self.cleaned_data.get("club")

        self.user.role = role
        if role == User.Roles.STUDENT:
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.cleaned_data.get("last_name", "")
        else:
            self.user.first_name = ""
            self.user.last_name = ""
        profile_picture = self.cleaned_data.get("profile_picture")
        if profile_picture:
            self.user.profile_picture = profile_picture
        self.user.save()

        if role == User.Roles.STUDENT:
            StudentProfile.objects.update_or_create(
                user=self.user,
                defaults={
                    "college": college,
                    "department": department,
                    "batch": self.cleaned_data.get("batch", ""),
                    "roll_no": self.cleaned_data.get("roll_no", ""),
                    "registration_no": self.cleaned_data.get("registration_no", ""),
                },
            )
        elif hasattr(self.user, "student_profile"):
            self.user.student_profile.delete()

        if role == User.Roles.CLUB and club:
            club.representative = self.user
            club.save(update_fields=["representative"])

        return self.user
