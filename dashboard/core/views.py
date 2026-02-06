from datetime import datetime
from common.models import ProjectSettings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from common.services import admin_required, sub_admin_required
from .forms import LoginForm, SettingForm, AdminProfile, SetPassword, ProjectSettingsForm
from django.contrib import messages
from users.models import User
from common.models import FeedReport, Setting
from django.core.paginator import Paginator
from players.core.utils import athlete_profile_action as delete_post
from coach.core.utils import users_management_actions
from .utils import date_formatter
import os, re
from django.http import StreamingHttpResponse, HttpResponse, FileResponse
import mimetypes
from django.conf import settings
from django.contrib.auth.decorators import login_required
from common.utils import paypal_checkout_session
from dashboard.models import AdminSubscriptionTransaction, AdminSubscription
from .forms import SportForm
from players.models import Sport
from django.db.models import Q
from users.services import send_forget_password_otp
from django.core.cache import cache
from users.services import send_otp_to_mail
from dashboard.core.forms import DiscountCodeForm
from users.models.discount_management import DiscountCode
from users.models.discount_management import DiscountCodeUsage

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email_lower = form.cleaned_data['email'].lower()
            user = authenticate(username=email_lower, password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                messages.success(request, "login successfully")
            else:
                form.add_error("password", "Incorrect password")

        if request.user.is_authenticated:

            if request.user.is_set_password is False or request.user.last_login is None:
                return redirect('change_password')

            return redirect(f"{request.GET.get('next') if request.GET.get('next') else '/'}")

    if request.user.is_authenticated:
        return redirect("/")
    return render(
        request,
        "dashboard/login.html",
        locals()
    )


@login_required(login_url='/login/')
def change_password(request):
    if request.method == "POST":
        form = SetPassword(request.POST)
        if form.is_valid():
            user = authenticate(username=request.user.username, password=form.cleaned_data['new_password'])
            if user is not None:
                form.add_error("new_password", "Password match previous")
            else:
                usr = request.user
                usr.set_password(form.cleaned_data['new_password'])
                messages.success(request, "Your password set successfully.")
                return redirect("/")

    return render(
        request,
        "dashboard/change_password.html",
        locals()
    )


@sub_admin_required
def dashboard(request):
    users = User.objects.all()
    from_date, to_date = date_formatter(request)
    if from_date and to_date:
        users = users.filter(date_joined__date__range=[from_date, to_date])

    athletes = users.filter(user_role="player").count()
    coach = users.filter(user_role="coach").count()
    fans = users.filter(user_role="fan").count()
    return render(request, "dashboard/dashboard.html", locals())


@login_required(login_url='/login/')
def user_logout(request):
    logout(request)
    return redirect("/login/")


@login_required(login_url='/login/')
def user_profile(request):
    if request.method == "POST":
        form = AdminProfile(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            profile_pic = form.cleaned_data.get("profile_pic")
            if profile_pic:
                user.profile_pic = profile_pic
            user.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
    return render(request, "dashboard/profile.html", locals())


@admin_required
def view_all_post_reports(request):
    page_number = request.GET.get("page")
    reposts = FeedReport.objects.all()
    paginator = Paginator(reposts, 25)
    reports = paginator.get_page(page_number)
    return render(request, "post/view_all_report.html", locals())


@admin_required
def view_report_post(request, pk):
    report = get_object_or_404(FeedReport, id=pk)
    post = report.feed
    if delete_post(request) or \
            users_management_actions(request, users=User.objects.filter(id=post.user.id)):
        return redirect("post_report_management")
    return render(request, "post/report_post_details.html", locals())


@admin_required
def content_management(request):
    setting = Setting.objects.all().first()
    if request.method == "POST":
        form = SettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "content updated successfully.")
            return redirect("content_management")
    else:
        form = SettingForm(instance=setting if setting else None)
    return render(request, "dashboard/content-management.html", locals())


def privacy_policy(request):
    setting = Setting.objects.all().first()
    return render(request, "dashboard/privacy-policy.html", locals())


def terms_condition(request):
    setting = Setting.objects.all().first()
    return render(request, "dashboard/terms-condition.html", locals())


def support_page(request):
    return render(request, "dashboard/support.html")


# CHUNK_SIZE = 8192  # 8 KB
CHUNK_SIZE = 65536  # 64 KB
ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']


def stream_video(request):
    file_path = request.GET.get("file_path").lstrip("/")
    if not file_path:
        return HttpResponse("Missing file_path", status=400)

    # Secure file path resolution (absolute path under MEDIA_ROOT)
    full_path = os.path.abspath(os.path.join(settings.BASE_DIR, file_path))

    # Ensure the file is under the media directory
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        return HttpResponse("Unauthorized file access", status=403)

    # Check if file exists
    if not os.path.exists(full_path):
        return HttpResponse("File not found", status=404)

    # Check file extension
    _, ext = os.path.splitext(full_path)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return HttpResponse("Unsupported file type", status=415)

    file_size = os.path.getsize(full_path)
    content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
    range_header = request.headers.get("Range", "").strip()

    # Handle Range requests for chunked streaming
    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            end = int(end) if end else file_size - 1
            length = end - start + 1

            def chunk_generator():
                with open(full_path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            break
                        yield chunk
                        remaining -= len(chunk)

            response = StreamingHttpResponse(chunk_generator(), status=206, content_type=content_type)
            response["Content-Length"] = str(length)
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Accept-Ranges"] = "bytes"
            return response

    # If no Range header, fallback to sending full file
    return FileResponse(open(full_path, 'rb'), content_type=content_type)


def redirect_on_store(request, action, mobile_os):
    if mobile_os == "iOS" or mobile_os.lower() == "ios":
        return redirect("https://apps.apple.com/us/app/athleterated/id6748231721")

    return redirect("https://play.google.com/store/apps/details?id=com.athleterated.athlete_rated")


@login_required
def subscription(request):
    if request.user.user_role != "sub_admin":
        messages.warning(request, "You do not need to pay for extra features.")
        return redirect("/")

    today = datetime.now().date()

    if AdminSubscription.objects.filter(
            user=request.user,
            start_date__lte=today,
            end_date__gte=today
    ).exists():
        messages.warning(request, "Your subscription is already active")
        return redirect("/")

    if request.method == "POST":
        try:
            paypal_res = paypal_checkout_session(
                price=199,
                success_url="/",
                cancel_url="/"
            )
            AdminSubscriptionTransaction.objects.create(
                user=request.user,
                session_id=paypal_res["id"],
                amount=199,
            )
            messages.warning(request,
                             "The subscription has been initiated. If you have completed the payment, please refresh the page to see it reflected.")
            return redirect(paypal_res['link'])
        except Exception as e:
            messages.error(request, f"Sorry we could not create payment duet to {str(e)}")

    return render(request, "users/subscription_page.html", locals())


@admin_required
def project_settings(request):
    project_config = ProjectSettings.objects.first()
    if request.method == "POST":
        project_config = ProjectSettingsForm(instance=project_config, data=request.POST)
        if project_config.is_valid():
            project_config.save()
            messages.success(request, "Project settings updated")
        else:
            messages.error(request, "Project settings update failed")
    else:
        project_config = ProjectSettingsForm(instance=project_config)

    return render(request, "dashboard/project_settings.html", locals())


def add_sport(request):
    if request.method == "POST":

        if 'delete_id' in request.POST:
            Sport.objects.filter(id=request.POST.get('delete_id')).delete()
            messages.error(request, "Sport deleted successfully")
            return redirect('add_sport')

        if 'edit_id' in request.POST:
            sport = get_object_or_404(Sport, id=request.POST.get('edit_id'))
            form = SportForm(request.POST, instance=sport)
            if form.is_valid():
                form.save()
                messages.success(request, "Sport updated successfully")
                return redirect('add_sport')

        form = SportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sport added successfully")
            return redirect('add_sport')

    else:
        form = SportForm()

    query = request.GET.get('q')
    sports_list = Sport.objects.all().order_by('name')
    if query:
        sports_list = sports_list.filter(Q(name__icontains=query))

    paginator = Paginator(sports_list, 10)
    page_number = request.GET.get('page')
    sports = paginator.get_page(page_number)

    return render(request, 'dashboard/add_sport.html', {
        'form': form,
        'sports': sports,
        'query': query
    })

def sport_details(request, pk):
    sport = get_object_or_404(Sport, id=pk)
    if not request.user.is_staff:
        return redirect('add_sport')

    return render(request, 'dashboard/sport_details.html', {'sport': sport})

def resend_otp(request):
    email= request.session.get('forgot_email')
    if not email:
        return redirect('forgot_password')
    try:
        user = User.objects.get(email=email)

    except User.DoesNotExist:
        return redirect('forgot_password')

    send_forget_password_otp(
        fullname=f"{user.first_name} {user.last_name}",
        user_email=user.email,
        phone_number=user.phone_number
    )
    messages.success(request, "OTP resend successfully.")
    return redirect('verify_forgot_otp')

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "This email does not exist in our records.")
            return render(request, "dashboard/forgot_password.html")

        request.session['forgot_email'] = email

        send_forget_password_otp(
            fullname=f"{user.first_name} {user.last_name}",
            user_email=user.email,
            phone_number=user.phone_number
        )
        return redirect('verify_forgot_otp')

    return render(request, "dashboard/forgot_password.html")


def verify_forgot_otp(request):
    email = request.session.get('forgot_email')

    if not email:
        return redirect('forgot_password')

    cache_otp = cache.get(f"forget_otp_{email}")

    if request.method == "POST":
        user_otp = request.POST.get("otp")

        if not cache_otp:
            messages.error(request, "OTP expired. Please resend.")
            return redirect('forgot_password')

        if str(user_otp).strip() != str(cache_otp):
            messages.error(request, "Please enter correct OTP.")
        else:
            cache.delete(f"forget_otp_{email}")
            return redirect('reset_password')

    return render(request, "dashboard/verify_forgot_otp.html", {"email": email})


def reset_password(request):
    email = request.session.get('forgot_email')

    if not email:
        return redirect('forgot_password')

    user = User.objects.get(email=email)

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_new_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords does not match.")
        else:
            user.set_password(new_password)
            user.save()

            request.session.flush()

            messages.success(request, "Password reset successfully.")
            return redirect('/')

    return render(request, "dashboard/reset_password.html")

def discount_management(request):
    query = request.GET.get("q", "")
    codes_list = DiscountCode.objects.all().order_by("-created_at")

    if query:
        codes_list = codes_list.filter(code_identifier__icontains=query)

    paginator = Paginator(codes_list, 20)
    page_number = request.GET.get("page")
    codes = paginator.get_page(page_number)

    action = request.GET.get("action")
    code_id = request.GET.get("id")
    if action and code_id:
        code_obj = get_object_or_404(DiscountCode, id=code_id)
        if action == "activate":
            code_obj.is_active = True
            code_obj.save()
        elif action == "deactivate":
            code_obj.is_active = False
            code_obj.save()
        elif action == "delete":
            code_obj.delete()

    return render(request, "dashboard/discount_management.html", {
        "codes": codes,
        "page_number": page_number,
        "query": query,
    })

def create_discount_code(request):
    if request.method == "POST":
        form = DiscountCodeForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            auto = request.POST.get("auto_generate")

            if not auto and not obj.code_identifier:
                messages.error(request, "Please enter code identifier")
                return render(request, "dashboard/create_discount_code.html", {
                    "form": form,
                    "edit": False
                })

            if auto:
                obj.code_identifier = None

            obj.save()
            messages.success(request, "Discount code created successfully")
            return redirect("discount_management")

    else:
        form = DiscountCodeForm()

    return render(request, "dashboard/create_discount_code.html", {
        "form": form,
        "edit": False
    })

def edit_discount_code(request, pk):
    code = get_object_or_404(DiscountCode, pk=pk)

    if request.method == "POST":
        form = DiscountCodeForm(request.POST, instance=code)
        auto = request.POST.get("auto_generate")

        if form.is_valid():
            obj = form.save(commit=False)
            if not auto and not obj.code_identifier:
                messages.error(request,"Please enter code identifier")
                return render(request, "dashboard/create_discount_code.html", {"form": form, "edit": True})

            if auto:
                obj.code_identifier = None

            obj.save()
            messages.success(request, "Discount code updated successfully")
            return redirect("discount_management")
    else:
        form = DiscountCodeForm(instance=code)

    return render(request, "dashboard/create_discount_code.html", {"form": form, "edit": True})

def usage_report(request, pk):
    code = get_object_or_404(DiscountCode, pk=pk)
    q = request.GET.get("q", "")
    usages = DiscountCodeUsage.objects.filter(discount=code)
    if q:
        usages = usages.filter(
            Q(user__email__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__user_role__icontains=q)
        )

    paginator = Paginator(usages.order_by("-created_at"), 2)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    remaining = code.usage_limit - code.current_usage
    return render(request, "dashboard/usage_report.html", {
        "code": code,
        "codes": page_obj,
        "remaining": remaining,
        "query": q,
    })