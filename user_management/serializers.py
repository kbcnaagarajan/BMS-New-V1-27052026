from rest_framework import serializers
from .models import Company, Department, Designation, Module, Permission, Role, User


class CompanySerializer(serializers.ModelSerializer):
    admin_name = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

    def get_admin_name(self, obj):
        return obj.company_admin.full_name if obj.company_admin else ''


class DepartmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Department
        fields = '__all__'


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.name', read_only=True)
    module_key = serializers.CharField(source='module.key', read_only=True)

    class Meta:
        model = Permission
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    permission_details = PermissionSerializer(source='permissions', many=True, read_only=True)

    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_title = serializers.CharField(source='designation.title', read_only=True)
    role_names = serializers.SerializerMethodField()
    module_permissions = serializers.SerializerMethodField()
    accessible_modules = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'middle_name', 'last_name', 'full_name',
                  'employee_id', 'phone', 'gender', 'date_of_birth', 'profile_image',
                  'user_type', 'company', 'company_name', 'department', 'department_name',
                  'designation', 'designation_title', 'roles', 'role_names',
                  'address', 'country', 'state', 'city', 'joining_date',
                  'is_active', 'is_client_user', 'is_superuser',
                  'is_company_admin_user', 'is_super_admin', 'is_pm_or_above',
                  'date_joined', 'last_login',
                  'module_permissions', 'accessible_modules']
        read_only_fields = ['date_joined', 'last_login']

    def get_role_names(self, obj):
        return [role.name for role in obj.roles.all()]

    def get_module_permissions(self, obj):
        """Return all module permissions for RBAC."""
        perms = {}
        if obj.is_superuser:
            from .models import Module
            for m in Module.objects.filter(is_active=True):
                perms[m.key] = ['view', 'create', 'edit', 'delete', 'approve', 'export', 'import', 'assign', 'manage']
        else:
            for role in obj.roles.filter(is_active=True):
                for perm in role.permissions.all():
                    key = perm.module.key
                    if key not in perms:
                        perms[key] = []
                    if perm.permission_type not in perms[key]:
                        perms[key].append(perm.permission_type)
        return perms

    def get_accessible_modules(self, obj):
        """Return list of module keys the user can access."""
        if obj.is_superuser:
            from .models import Module
            return list(Module.objects.filter(is_active=True).values_list('key', flat=True))
        return list(obj.roles.filter(
            is_active=True
        ).values_list('permissions__module__key', flat=True).distinct())


class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name',
                  'profile_image', 'user_type', 'employee_id', 'company']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    """Shape of the login response with RBAC context."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    menu = serializers.ListField()
    permissions = serializers.DictField()
