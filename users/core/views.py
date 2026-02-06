import datetime

from django.shortcuts import HttpResponse, render, redirect, get_object_or_404
from common.services import admin_required
from users.core.forms import CreateSubAdminForm
from users.models import User, IdentityVerification, ReferralOrganization, DocumentType, \
    AthleteTypes
from django.contrib import messages
from users.task import send_sub_admin_login_details, send_password_mail
from users.services import utils
from django.core.paginator import Paginator
from users.services import send_parent_verification_mail
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group
from django.db.models import Q


@admin_required
def view_all_sub_admin(request):
    user_id = request.GET.get('id')
    if user_id:
        usr = get_object_or_404(User, id=user_id)
        action = request.GET.get("action")
        if action == "activate":
            usr.is_active = True
            messages.success(request, f"{usr.username} has been activated successfully.")
            usr.save()
        elif action == "deactivate":
            usr.is_active = False
            messages.success(request, f"{usr.username} has been deactivated successfully.")
            usr.save()
        elif action == "delete":
            usr.delete()
            messages.error(request, f"{usr.username} has been deleted successfully.")
        else:
            messages.warning(request, f"Hello {request.user.username} something you went wrong.")

        return redirect('sub_admin_management')

    sub_admins = User.objects.filter(Q(user_role="sub_admin") | Q(user_role="ar_staff"))
    return render(request, "users/view_all_sub_admin.html", locals())


@admin_required
def create_sub_admin(request):

    def generate_username(email):
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username

    permissions = Permission.objects.filter(
            content_type__app_label="users",
            codename__in=[
                "identity_verification",
                "edit_events",
                "view_revenue_share",
                # "view_all_event",
            ]
        )
    orgs = ReferralOrganization.objects.all()
    if request.method == "POST":
        form = CreateSubAdminForm(request.POST)
        if form.is_valid():
            password = utils.random_text_number(10)
            phone_number = form.cleaned_data['phone_number']
            usr = User.objects.create_user(
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                username=generate_username(form.cleaned_data['email']),
                email=form.cleaned_data['email'],
                phone_number=phone_number,
                user_role=form.cleaned_data['user_role'],
                is_set_password=False,
                is_active=True,
            )
            usr.set_password(password)
            usr.save()

            if form.cleaned_data['user_role'] == "sub_admin":
                group = Group.objects.get(name="Event Director")
                usr.groups.add(group)
            # else:
            #     group = Group.objects.get(name="AR Staff")

            selected_perms = form.cleaned_data.get("permissions")
            if selected_perms:
                usr.user_permissions.add(*selected_perms)

            organization = form.cleaned_data.get("organization")
            if organization:
                organization.users.add(usr)
                organization.save()

            messages.success(request, f"User account created successfully.")
            send_sub_admin_login_details.delay(username=usr.username, email=usr.email, password=password,
                                               phone_number=phone_number)
            return redirect("sub_admin_management")
        else:
            messages.error(request, f"Sub admin creation failed please check and fix the errors.")

    return render(request, "users/create_sub_admin.html", locals())


@admin_required
def sub_admin_profile(request, pk):
    usr = get_object_or_404(User, id=pk)
    permissions = usr.get_all_permissions()
    permissions = [i.split(".")[1] for i in permissions]
    all_permissions = Permission.objects.filter(
        content_type__app_label="users",
        codename__in=[
            "identity_verification",
            "edit_events",
            "view_revenue_share",
            # "view_all_event",
        ]
    )
    return render(request, "users/sub_admin_profile.html", locals())


@admin_required
def identity_verification(request):
    pk = request.GET.get("id")
    if request.GET.get("action") == "delete_doc":
        doc = get_object_or_404(DocumentType, id=pk)
        messages.success(request, f"document deleted successfully.")
        doc.delete()
        return redirect("identity_verification")

    elif request.GET.get("action") == "delete_athlete":
        athlete = get_object_or_404(AthleteTypes, id=pk)
        messages.success(request, f"delete athlete successfully.")
        athlete.delete()
        return redirect("identity_verification")



    elif request.GET.get("action") == "delete_identity":
        from django.contrib.auth import get_user_model
        current_user = get_user_model()
        user = get_object_or_404(current_user, id=pk)
        IdentityVerification.objects.filter(user_id=pk).delete()
        user.is_identity_verified = False
        user.save()
        messages.success(request, "Identity deleted successfully.")
        return redirect("identity_verification")


    elif request.GET.get("action") == "delete_identity":
        IdentityVerification.objects.filter(user_id=pk).delete()
        messages.success(request, "Identity deleted successfully.")
        return redirect("identity_verification")

    if request.method == "POST":
        if "add_referrer" in request.POST:
            name = request.POST['name']
            try:
                ReferralOrganization.objects.create(name=name)
                messages.success(request, "Referrer created successfully.")
                return redirect("identity_verification")
            except Exception as e:
                print(e)
                messages.error(request, f"Failed to create organization: an entry with the name '{name}' already exists.")
        elif "add_document_type" in request.POST:
            title = request.POST['name']
            try:
                DocumentType.objects.create(
                    title=title
                )
                messages.success(request, "Document type created successfully.")
                return redirect("identity_verification")
            except Exception as e:
                print(e)
                messages.error(request, f"Failed to create document type: an entry with the name '{title}' already exists.")

        elif "add_athlete_type" in request.POST:
            title = request.POST['title']
            try:
                AthleteTypes.objects.create(
                    title=title
                )
                messages.success(request, "Athlete type created successfully.")
                return redirect("identity_verification")
            except Exception as e:
                print(e)
                messages.error(request,
                               f"Failed to create athlete type: an entry with the name '{title}' already exists.")

    page_number = request.GET.get("page", 1)
    verification_ids = IdentityVerification.objects.raw('''
        SELECT DISTINCT ON (user_id) id
        FROM users_identityverification
        WHERE is_active = true
        ORDER BY user_id, created_at DESC
    ''')

    id_list = [v.id for v in verification_ids]

    verification_users = IdentityVerification.objects.filter(
        id__in=id_list
    ).order_by('-created_at')
    refer_organization = ReferralOrganization.objects.all()
    document_types = DocumentType.objects.all()
    athlete_types = AthleteTypes.objects.all()
    paginator = Paginator(verification_users, 25)
    paginator = Paginator(verification_users, 100)
    verification_users = paginator.get_page(page_number)
    return render(request, "users/identity_verification.html", locals())

from users.models.discount_management import DiscountCodeUsage
@admin_required
def identity_detail(request, pk):
    verification_users = IdentityVerification.objects.select_related("user").filter(user__id=pk).order_by("-created_at")
    discount_usage = DiscountCodeUsage.objects.select_related("discount").filter(user__id=pk).first()

    if request.method == "POST":
        if "verification_parent" in request.POST:
            verification_obj = verification_users.first()
            if request.POST.get("parent_email"):
                verification_obj.parent_email = request.POST.get("parent_email")

            verification_obj.parent_legal_name = request.POST.get("parent_legal_name", verification_obj.parent_legal_name)

            if request.POST.get("parent_phone_number"):
                verification_obj.parent_phone_number = request.POST.get("parent_phone_number", verification_obj.parent_phone_number)

            verification_obj.save()

            send_parent_verification_mail(verification_obj)
            messages.success(request, "Verification send successfully.")
            return redirect("identity_verification_detail", pk)

        else:
            verification_users = IdentityVerification.objects.select_related("user").filter(user__id=pk).latest(
                "created_at")
            if request.POST.get("action") == "accept":
                user = verification_users.user
                user.is_identity_verified = True
                verification_users.status = "accept"
                user.save()
                messages.success(request, "Identity Document verified successfully.")
            else:
                reasons = request.POST.getlist('reason', [])
                custom_reason = request.POST.get('custom_reason', '').strip()
                reasons.append(custom_reason)
                verification_users.reject_reason = reasons

                messages.warning(request, "Account reject successfully")
                verification_users.status = "reject"

            verification_users.remark = request.POST.get("remark", "")
            verification_users.save()
            return redirect("identity_verification_detail", pk)

    return render(request, "users/verification_details.html", locals())


@admin_required
def identity_verification_transaction_detail(request, pk):
    verification_users = IdentityVerification.objects.select_related("user").filter(user__id=pk).order_by("-created_at")
    return render(request, "users/verification_transactions.html", locals())


def parent_verification(request, pk):
    year = datetime.datetime.now().year
    verification_obj = get_object_or_404(IdentityVerification, id=pk)
    if verification_obj.parent_verified != "pending":
        parent_verified = verification_obj.parent_verified
        if parent_verified == "accept":
            consent_given = True
        return render(request, "users/parent_res.html", locals())

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "accept":
            verification_obj.parent_verified = "accept"
            consent_given = True
        else:
            verification_obj.parent_verified = "reject"

        verification_obj.save()
        return render(request, "users/parent_res.html", locals())

    return render(request, "users/parent_verification.html", locals())


@admin_required
def resend_password(request, pk):
    athlete = User.objects.filter(id=pk).first()  # user_role="player",
    password = utils.random_text_number(8)
    athlete.set_password(password)
    send_password_mail.delay(
        username=athlete.username,
        email=athlete.email,
        password=password,
        phone_number=athlete.phone_number
    )
    athlete.save()
    messages.success(request, "Password has been sent successfully.")

    if request.GET.get("is_admin"):
        return redirect("sub_admin_profile", pk)

    return redirect("athlete_profile", pk)


@admin_required
def revenue_detail(request, referer):
    page_number = request.GET.get("page", 1)
    verification_users = IdentityVerification.objects.filter(refer_by=referer)
    paginator = Paginator(verification_users, 100)
    verification_users = paginator.get_page(page_number)
    return render(request, "users/revenue.html", locals())


