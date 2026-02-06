import django_filters
from users.models import User
from django.db.models import Q
from players.models import Follow


class UserProfileFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')

    date_joined_after = django_filters.DateFilter(
        field_name='date_joined',
        lookup_expr='gte'
    )
    date_joined_before = django_filters.DateFilter(
        field_name='date_joined',
        lookup_expr='lte'
    )
    role = django_filters.CharFilter(method='filter_by_role')
    name = django_filters.CharFilter(method="filter_by_name")
    user_role = django_filters.CharFilter(method="filter_user_role")
    q = django_filters.CharFilter(method="query_search")
    id = django_filters.CharFilter()

    def filter_by_role(self, queryset, name, value):
        return queryset.filter(groups__name=value)

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )

    def filter_user_role(self, queryset, name, value):
        return queryset.filter(
            user_role=value
        )

    def query_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(player__position__name__icontains=value)
        )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'is_active',
            'date_joined_after',
            'date_joined_before',
            'role',
            "name",
            "user_role",
            "q",
            "id"
        ]


class FollowingFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains', field_name='followers__username')
    email = django_filters.CharFilter(lookup_expr='icontains', field_name='followers__email')
    first_name = django_filters.CharFilter(lookup_expr='icontains', field_name='followers__first_name')
    last_name = django_filters.CharFilter(lookup_expr='icontains', field_name='followers__last_name')
    q = django_filters.CharFilter(method='filter_follower')

    def filter_follower(self, queryset, name, q):
        user_follow = queryset.filter(
            Q(follower__username__icontains=q) |
            Q(follower__first_name__icontains=q) |
            Q(follower__last_name__icontains=q) |
            Q(follower__email__icontains=q)
        )
        return user_follow

    class Meta:
        model = Follow
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "q"
        ]


class FollowerFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains', field_name='following__username')
    email = django_filters.CharFilter(lookup_expr='icontains', field_name='following__email')
    first_name = django_filters.CharFilter(lookup_expr='icontains', field_name='following__first_name')
    last_name = django_filters.CharFilter(lookup_expr='icontains', field_name='following__last_name')
    q = django_filters.CharFilter(method='filter_following')

    def filter_following(self, queryset, name, q):
        user_follow = queryset.filter(
            Q(following__username__icontains=q) |
            Q(following__first_name__icontains=q) |
            Q(following__last_name__icontains=q) |
            Q(following__email__icontains=q)
        )
        return user_follow

    class Meta:
        model = Follow
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "q"
        ]

