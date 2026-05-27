from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Company, Department, Designation, Module, Permission, Role, User
from .serializers import (
    CompanySerializer, DepartmentSerializer, DesignationSerializer,
    ModuleSerializer, PermissionSerializer, RoleSerializer,
    UserSerializer, UserMinimalSerializer, LoginSerializer
)
from .mixins import CompanyScopeMixin, CompanyAdminMixin, StaffDetailRestrictedMixin
from .rbac import build_user_menu


class CompanyViewSet(CompanyAdminMixin, viewsets.ModelViewSet):
    """
    Superadmin: sees ALL companies (overview only)
    Regular users: see only their own company
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    search_fields = ['name', 'email']
    filterset_fields = ['is_active']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Company.objects.all()
        if user.company:
            return Company.objects.filter(id=user.company.id)
        return Company.objects.none()

    def perform_create(self, serializer):
        company = serializer.save()
        # Create default admin role for the new company
        admin_role, _ = Role.objects.get_or_create(
            company=company,
            name=f'{company.name} Admin',
            defaults={'category': 'company_admin', 'is_system_role': True}
        )


class DepartmentViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ['name', 'company__name']
    filterset_fields = ['company', 'is_active']

    def perform_create(self, serializer):
        if not serializer.validated_data.get('company') and self.request.user.company:
            serializer.save(company=self.request.user.company)
        else:
            serializer.save()


class DesignationViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    search_fields = ['title']
    filterset_fields = ['company', 'is_active']

    def perform_create(self, serializer):
        if not serializer.validated_data.get('company') and self.request.user.company:
            serializer.save(company=self.request.user.company)
        else:
            serializer.save()


class ModuleViewSet(viewsets.ModelViewSet):
    """Only superadmin can manage modules."""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Module.objects.all()
        return self.request.user.get_accessible_modules()


class PermissionViewSet(viewsets.ModelViewSet):
    """Only superadmin can manage permissions."""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_fields = ['module', 'permission_type']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Permission.objects.all()
        return Permission.objects.filter(
            module__in=self.request.user.get_accessible_modules()
        )


class RoleViewSet(CompanyScopeMixin, viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    search_fields = ['name']
    filterset_fields = ['company', 'is_system_role', 'category']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Role.objects.all()
        if user.company:
            return Role.objects.filter(company=user.company)
        return Role.objects.none()

    def perform_create(self, serializer):
        if not serializer.validated_data.get('company') and self.request.user.company:
            serializer.save(company=self.request.user.company)
        else:
            serializer.save()


class UserViewSet(StaffDetailRestrictedMixin, viewsets.ModelViewSet):
    """
    Superadmin: sees all users (aggregated), cannot drill into staff details
    Company admin: sees all users within their company
    Regular user: sees only themselves
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']
    filterset_fields = ['user_type', 'is_active', 'company', 'department']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserMinimalSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            # Superadmin sees all users but without drill-down
            return User.objects.all()
        if user.is_company_admin_user() and user.company:
            return User.objects.filter(company=user.company)
        if user.company:
            return User.objects.filter(company=user.company, is_active=True)
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        user_type = request.query_params.get('user_type')
        qs = self.get_queryset().filter(is_active=True)
        if user_type:
            qs = qs.filter(user_type=user_type)
        serializer = UserMinimalSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def project_managers(self, request):
        qs = self.get_queryset().filter(
            user_type__in=['project_manager', 'delivery_manager'],
            is_active=True
        )
        serializer = UserMinimalSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def accessible(self, request):
        """Return users visible to current user based on role."""
        qs = request.user.get_visible_profiles()
        serializer = UserMinimalSerializer(qs, many=True)
        return Response(serializer.data)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request=request, username=email, password=password)
        if user and user.is_active:
            refresh = RefreshToken.for_user(user)

            # Attach company info to token claims
            if user.company:
                refresh['company_id'] = user.company.id
            refresh['user_type'] = user.user_type

            # Build RBAC context for login response
            menu = build_user_menu(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'menu': menu,
                'permissions': UserSerializer(user).data.get('module_permissions', {}),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        user = self.request.user
        return user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        data = serializer.data
        data['menu'] = build_user_menu(user)
        return Response(data)
