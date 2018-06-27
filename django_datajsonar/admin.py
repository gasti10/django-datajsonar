#!coding=utf8
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.conf.urls import url

from .views import config_csv
from .actions import process_node_register_file_action, confirm_delete
from .utils import download_config_csv
from .tasks import bulk_whitelist, read_datajson
from .models import DatasetIndexingFile, NodeRegisterFile, Node, ReadDataJsonTask
from .models import Catalog, Dataset, Distribution, Field


class CatalogAdmin(admin.ModelAdmin):
    list_display = ('title', 'identifier', 'present', 'updated')
    search_fields = ('identifier', 'present', 'updated')
    readonly_fields = ('identifier',)
    list_filter = ('present', 'updated')

    def get_search_results(self, request, queryset, search_term):
        queryset, distinct = \
            super(CatalogAdmin, self).get_search_results(request, queryset, search_term)
        if not search_term:
            return queryset, distinct

        ids_to_remove = []
        for obj in queryset:
            if search_term not in (obj.identifier,):
                ids_to_remove.append(obj.id)

        return queryset.exclude(id__in=ids_to_remove), distinct


class DatasetAdmin(admin.ModelAdmin):
    list_display = ('title', 'identifier', 'catalog', 'present', 'updated', 'indexable')
    search_fields = ('identifier', 'catalog__identifier', 'present', 'updated', 'indexable')
    readonly_fields = ('identifier', 'catalog')
    actions = ['make_indexable', 'make_unindexable', 'generate_config_file']

    list_filter = ('catalog__identifier', 'present', 'indexable')

    def make_unindexable(self, _, queryset):
        queryset.update(indexable=False)
    make_unindexable.short_description = 'Marcar como no indexable'

    def make_indexable(self, _, queryset):
        queryset.update(indexable=True)
    make_indexable.short_description = 'Marcar como indexable'

    def generate_config_file(self, _, queryset):
        indexables = queryset.filter(indexable=True)
        return download_config_csv(indexables)
    generate_config_file.short_description = 'Generar csv de configuración'

    def get_urls(self):
        urls = super(DatasetAdmin, self).get_urls()
        extra_urls = [url(r'^federacion-config\.csv/$', config_csv, name='config_csv'), ]
        return extra_urls + urls

    def get_search_results(self, request, queryset, search_term):
        queryset, distinct = \
            super(DatasetAdmin, self).get_search_results(request, queryset, search_term)
        if not search_term:
            return queryset, distinct

        ids_to_remove = []
        for obj in queryset:
            if search_term not in (obj.identifier,):
                ids_to_remove.append(obj.id)

        return queryset.exclude(id__in=ids_to_remove), distinct


class DistributionAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'title', 'get_dataset_title', 'get_catalog_id', 'last_updated', 'present', 'updated')
    search_fields = ('identifier', 'dataset__identifier', 'dataset__catalog__identifier')
    list_filter = ('dataset__catalog__identifier', )

    def get_dataset_title(self, obj):
        return obj.dataset.title
    get_dataset_title.short_description = 'Dataset'
    get_dataset_title.admin_order_field = 'dataset__title'

    def get_catalog_id(self, obj):
        return obj.dataset.catalog.identifier
    get_catalog_id.short_description = 'Catalog'
    get_catalog_id.admin_order_field = 'dataset__catalog__identifier'

    def get_search_results(self, request, queryset, search_term):
        queryset, distinct = \
            super(DistributionAdmin, self).get_search_results(request, queryset, search_term)
        if not search_term:
            return queryset, distinct

        ids_to_remove = []
        for obj in queryset:
            if search_term not in (obj.identifier, obj.dataset.identifier):
                ids_to_remove.append(obj.id)

        return queryset.exclude(id__in=ids_to_remove), distinct


class FieldAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'identifier', 'get_distribution_title', 'get_dataset_title', 'get_catalog_id')
    search_fields = (
        'distribution__identifier',
        'distribution__dataset__identifier',
        'distribution__dataset__catalog__identifier'
    )
    list_filter = (
        'distribution__dataset__catalog__identifier',
    )

    def get_catalog_id(self, obj):
        return obj.distribution.dataset.catalog.identifier
    get_catalog_id.short_description = 'Catalog'
    get_catalog_id.admin_order_field = 'distribution__dataset__catalog__identifier'

    def get_dataset_title(self, field):
        return field.distribution.dataset.title
    get_dataset_title.short_description = 'Dataset'
    get_dataset_title.admin_order_field = 'distribution__dataset__identifier'

    def get_distribution_title(self, field):
        return field.distribution.title
    get_distribution_title.short_description = 'Distribution'
    get_distribution_title.admin_order_field = 'distribution__title'

    def get_title(self, obj):
        return obj.title or 'No title'
    get_title.short_description = 'Title'

    def get_search_results(self, request, queryset, search_term):
        queryset, distinct = \
            super(FieldAdmin, self).get_search_results(request, queryset, search_term)
        if not search_term:
            return queryset, distinct

        ids_to_remove = []
        for obj in queryset:
            if search_term not in (obj.distribution.identifier,
                                   obj.distribution.dataset.identifier):
                ids_to_remove.append(obj.id)

        return queryset.exclude(id__in=ids_to_remove), distinct


class BaseRegisterFileAdmin(admin.ModelAdmin):
    actions = ['process_register_file']
    list_display = ('__unicode__', 'state', )
    readonly_fields = ('created', 'modified', 'state', 'logs')

    def process_register_file(self, _, queryset):
        raise NotImplementedError
    process_register_file.short_description = 'Ejecutar'

    def get_form(self, request, obj=None, **kwargs):
        form = super(BaseRegisterFileAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['uploader'].initial = request.user
        return form

    def save_form(self, request, form, change):
        return super(BaseRegisterFileAdmin, self).save_form(request, form, change)


class NodeRegisterFileAdmin(BaseRegisterFileAdmin):

    def process_register_file(self, _, queryset):
        for model in queryset:
            model.state = NodeRegisterFile.state = NodeRegisterFile.PROCESSING
            model.logs = u'-'
            model.save()
            process_node_register_file_action(model)


class NodeAdmin(admin.ModelAdmin):

    list_display = ('catalog_id', 'indexable')
    exclude = ('catalog',)
    actions = ('delete_model', 'run_indexing', 'make_indexable', 'make_unindexable')

    def get_actions(self, request):
        # Borro la acción de borrado default
        actions = super(NodeAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def make_unindexable(self, _, queryset):
        queryset.update(indexable=False)
    make_unindexable.short_description = 'Marcar como no indexable'

    def make_indexable(self, _, queryset):
        queryset.update(indexable=True)
    make_indexable.short_description = 'Marcar como indexable'

    def delete_model(self, _, queryset):
        register_files = NodeRegisterFile.objects.all()
        for node in queryset:
            if node.indexable:
                confirm_delete(node, register_files)


class AbstractTaskAdmin(admin.ModelAdmin):
    readonly_fields = ('status', 'created', 'finished', 'logs',)
    list_display = ('__unicode__', 'status')

    # Clase del modelo asociado
    model = None

    # Task (callable) a correr asincrónicamente. Por default recible solo una instancia
    # del AbstractTask asociado a este admin, overridear save_model
    # si se quiere otro comportamiento
    task = None

    def save_model(self, request, obj, form, change):
        super(AbstractTaskAdmin, self).save_model(request, obj, form, change)
        self.task.delay(obj)  # Ejecuta callable

    def add_view(self, request, form_url='', extra_context=None):
        # Bloqueo la creación de nuevos modelos cuando está corriendo la tarea
        if self.model.objects.filter(status=self.model.RUNNING):
            messages.error(request, "Ya está corriendo una indexación")
            return super(AbstractTaskAdmin, self).changelist_view(request, None)

        return super(AbstractTaskAdmin, self).add_view(request, form_url, extra_context)


class DataJsonAdmin(AbstractTaskAdmin):
    model = ReadDataJsonTask
    task = read_datajson


class DatasetIndexingFileAdmin(BaseRegisterFileAdmin):
    def process_register_file(self, _, queryset):
        for model in queryset:
            model.state = DatasetIndexingFile.state = DatasetIndexingFile.PROCESSING
            model.logs = u'-'  # Valor default mientras se ejecuta
            model.save()
            bulk_whitelist.delay(model.id)


admin.site.register(Catalog, CatalogAdmin)
admin.site.register(Dataset, DatasetAdmin)
admin.site.register(Distribution, DistributionAdmin)
admin.site.register(Field, FieldAdmin)

admin.site.register(DatasetIndexingFile, DatasetIndexingFileAdmin)
admin.site.register(NodeRegisterFile, NodeRegisterFileAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(ReadDataJsonTask, DataJsonAdmin)
