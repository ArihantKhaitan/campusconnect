from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, ProfileEditForm, ProfileSetupForm, SignupForm
from .models import User


class AuthPageView(TemplateView):
    template_name = "accounts/auth.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("login_form", LoginForm(request=self.request))
        context.setdefault("signup_form", SignupForm())
        context.setdefault("active_tab", self.request.GET.get("tab", "login"))
        return context


class CampusLoginView(LoginView):
    template_name = "accounts/auth.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["login_form"] = context.get("form")
        context.setdefault("signup_form", SignupForm())
        context["active_tab"] = "login"
        return context

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            return next_url
        return str(reverse_lazy("accounts:dashboard_redirect"))


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/auth.html"
    success_url = reverse_lazy("accounts:profile_setup")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["signup_form"] = context.get("form")
        context.setdefault("login_form", LoginForm(request=self.request))
        context["active_tab"] = "signup"
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(self.success_url)


class CampusLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:auth")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            user = form.save()
            if hasattr(request, "session") and request.user.pk == user.pk:
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
            return redirect("accounts:profile")
    else:
        form = ProfileEditForm(instance=request.user, user=request.user)

    managed_club = request.user.managed_clubs.select_related("college").first()
    profile = getattr(request.user, "student_profile", None)
    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "managed_club": managed_club,
            "student_profile": profile,
        },
    )


@login_required
def dashboard_redirect(request):
    if request.user.role == User.Roles.ADMIN:
        return redirect("core:admin_dashboard")
    if request.user.role == User.Roles.CLUB:
        return redirect("core:club_dashboard")
    return redirect("core:student_dashboard")


@login_required
def profile_setup(request):
    if request.GET.get("skip") == "1":
        return redirect("accounts:dashboard_redirect")

    if request.method == "POST":
        form = ProfileSetupForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:dashboard_redirect")
    else:
        initial = {"role": request.user.role, "first_name": request.user.first_name, "last_name": request.user.last_name}
        if hasattr(request.user, "student_profile"):
            profile = request.user.student_profile
            initial.update(
                {
                    "college": profile.college,
                    "department": profile.department,
                    "batch": profile.batch,
                    "roll_no": profile.roll_no,
                    "registration_no": profile.registration_no,
                }
            )
        managed_club = request.user.managed_clubs.first()
        if managed_club:
            initial["club"] = managed_club
            initial.setdefault("college", managed_club.college)
        form = ProfileSetupForm(initial=initial, user=request.user)
    return render(request, "accounts/profile_setup.html", {"form": form, "has_profile_picture": bool(request.user.profile_picture)})
