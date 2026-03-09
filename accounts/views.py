from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy


WORKER_GROUPS = {
    "RANG_TAYYORLOVCHI",
    "QUYUVCHI",
    "APPARATCHI",
    "PALIROFKACHI",
    "SARTIROVKACHI",
    "OMBORCHI",
    "JONATUVCHI",
    "MASTER",
}


class UserLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user

        if user.is_superuser:
            return reverse_lazy("dashboard_home")

        user_groups = set(user.groups.values_list("name", flat=True))

        if user_groups.intersection(WORKER_GROUPS):
            return reverse_lazy("worker_dashboard")

        return reverse_lazy("dashboard_home")


class UserLogoutView(LogoutView):
    pass