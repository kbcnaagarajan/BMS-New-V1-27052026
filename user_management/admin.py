from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Company, Department, Designation, Module, Permission, Role, User, UserActivity


class PermissionInline(admin.TabularInline):
    model = Permission
    extra = 1


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'parent', 'sequence', 'is_menu_item', 'is_active']
    list_filter = ['is_menu_item', 'is_active']
    search_fields = ['name', 'key']
    inlines = [PermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['codename', 'name', 'module', 'permission_type']
    list_filter = ['module', 'permission_type']
    search_fields = ['codename', 'name']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'country', 'is_active', 'company_admin']
    search_fields = ['name', 'email']
    list_filter = ['is_active', 'country']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'code', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name', 'company__name']


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'level', 'is_active']
    list_filter = ['company', 'is_active']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'category', 'is_system_role', 'is_active']
    list_filter = ['company', 'category', 'is_system_role', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    fieldsets = (
        (None, {'fields': ('name', 'company', 'category', 'description')}),
        ('Permissions', {'fields': ('permissions',)}),
        ('Status', {'fields': ('is_system_role', 'is_active')}),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'company', 'is_active']
    list_filter = ['user_type', 'is_active', 'company']
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'middle_name', 'last_name', 'employee_id', 'phone', 'gender', 'date_of_birth', 'profile_image')}),
        ('Organization', {'fields': ('company', 'department', 'designation', 'roles', 'user_type', 'joining_date')}),
        ('Address', {'fields': ('address', 'country', 'state', 'city')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser', 'is_client_user', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'password1', 'password2', 'user_type', 'company'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions', 'roles')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'action']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'created_at']
