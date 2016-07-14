# coding: utf-8

# PYTHON IMPORTS
import os

# DJANGO IMPORTS
from django.conf import settings
from django.core import urlresolvers
from django.core.files.move import file_move_safe
from django.core.files.storage import get_storage_class
from django.db import models
from django.db.models.fields import CharField
from django import forms
from django.forms.widgets import Input
from django.template.loader import render_to_string
from django.utils.encoding import smart_text
from django.utils.six import with_metaclass
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.templatetags.admin_static import static

# FILEBROWSER IMPORTS
from filebrowser.settings import UPLOAD_TEMPDIR, ADMIN_THUMBNAIL, EXTENSIONS
from filebrowser.base import FileObject
from filebrowser.sites import site


class FileBrowseAndUploadWidget(Input):
    input_type = 'text'

    class Media:
        js = (
            'filebrowser/js/AddFileBrowser.js',
            'filebrowser/js/fileuploader.js',
            'filebrowser/js/insQ.js',
            'filebrowser/js/custom_upload_field.js',
        )
        css = {
            'all': (
                'filebrowser/css/uploadfield.css',
                'filebrowser/css/custom_browse_and_upload_field.css',
            )
        }

    def __init__(self, attrs=None):
        super(FileBrowseAndUploadWidget, self).__init__(attrs)
        self.site = attrs.get('filebrowser_site', '')
        self.directory = attrs.get('directory', '')
        self.extensions = attrs.get('extensions', '')
        self.format = attrs.get('format', '')
        self.upload_to = attrs.get('upload_to', '')
        self.temp_upload_dir = attrs.get('temp_upload_dir', '')
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}
        super(FileBrowseAndUploadWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        url = urlresolvers.reverse(self.site.name + ":fb_browse")
        if value is None:
            value = ""
        if value != "" and not isinstance(value, FileObject):
            value = FileObject(value, site=self.site)
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        final_attrs['search_icon'] = static('filebrowser/img/filebrowser_icon_show.gif')
        final_attrs['url'] = url
        final_attrs['directory'] = self.directory or self.upload_to
        final_attrs['filebrowser_directory'] = self.site.directory
        final_attrs['extensions'] = self.extensions
        final_attrs['format'] = self.format
        final_attrs['upload_to'] = self.upload_to
        final_attrs['temp_upload_dir'] = UPLOAD_TEMPDIR
        final_attrs['ADMIN_THUMBNAIL'] = ADMIN_THUMBNAIL
        filebrowser_site = self.site
        if value:
            # If we have an image then filebrowser should open to that directory rather than the default
            try:
                final_attrs['directory'] = os.path.split(value.original.path_relative_directory)[0]
            except Exception:
                pass
        return render_to_string("filebrowser/custom_browse_and_upload_field.html", locals())


class FileBrowseAndUploadFormField(forms.CharField):

    default_error_messages = {
        'extension': _(u'Extension %(ext)s is not allowed. Only %(allowed)s is allowed.'),
    }

    def __init__(self, max_length=None, min_length=None, site=None, directory=None, extensions=None, format=None, upload_to=None, temp_upload_dir=None, *args, **kwargs):
        self.max_length, self.min_length = max_length, min_length
        self.site = kwargs.pop('filebrowser_site', site)
        self.directory = directory
        self.format = format or ''
        self.extensions = extensions or EXTENSIONS.get(format.title())
        self.upload_to = upload_to
        self.temp_upload_dir = temp_upload_dir
        super(FileBrowseAndUploadFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(FileBrowseAndUploadFormField, self).clean(value)
        if value == '':
            return value
        file_extension = os.path.splitext(value)[1].lower()
        if self.extensions and file_extension not in self.extensions:
            raise forms.ValidationError(self.error_messages['extension'] % {'ext': file_extension, 'allowed': ", ".join(self.extensions)})
        return value


class FileBrowseAndUploadField(with_metaclass(models.SubfieldBase, CharField)):

    description = "FileBrowseAndUploadField"

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('filebrowser_site', site)
        self.directory = kwargs.pop('directory', '')
        self.extensions = kwargs.pop('extensions', '')
        self.format = kwargs.pop('format', '')
        self.upload_to = kwargs.pop('upload_to', '')
        self.temp_upload_dir = kwargs.pop('temp_upload_dir', '') or UPLOAD_TEMPDIR
        kwargs['max_length'] = kwargs.get('max_length', False) or 255 
        return super(FileBrowseAndUploadField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value or isinstance(value, FileObject):
            return value
        return FileObject(value, site=self.site)

    def get_db_prep_value(self, value, connection, prepared=False):
        if not value:
            return value
        elif getattr(value, 'path', False):
            return value.path
        else:  # If we've passed a default then it will be just a string. Sometimes happens with migrations
            return value

    def get_prep_value(self, value):
        if not value:
            return value
        return value.path

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        if not value:
            return value
        return value.path

    def formfield(self, **kwargs):
        attrs = {}
        attrs["filebrowser_site"] = self.site
        attrs["directory"] = self.directory
        attrs["extensions"] = self.extensions
        attrs["format"] = self.format
        attrs["upload_to"] = self.upload_to
        attrs["temp_upload_dir"] = self.temp_upload_dir
        defaults = {
            'form_class': FileBrowseAndUploadFormField,
            'widget': FileBrowseAndUploadWidget(attrs=attrs),
            'filebrowser_site': self.site,
            'directory': self.directory,
            'extensions': self.extensions,
            'format': self.format,
            'upload_to': self.upload_to,
            'temp_upload_dir': self.temp_upload_dir
        }
        return super(FileBrowseAndUploadField, self).formfield(**defaults)
    
    def upload_callback(self, sender, instance, created, using, **kwargs):
        
        opts = instance._meta
        field = getattr(instance, self.name)
        
        if field:
            
            filename = os.path.basename(smart_text(field))
            upload_to = opts.get_field(self.name).upload_to
            filebrowser_directory = self.site.directory
            
            if getattr(upload_to, '__call__', None):
                upload_to = os.path.split(upload_to(instance, filename))[0]
            
            if self.temp_upload_dir in field.path:
                new_file = get_storage_class()().get_available_name(
                    os.path.join(
                        settings.MEDIA_ROOT,
                        filebrowser_directory,
                        upload_to,
                        filename,
                    )
                )
                new_path = os.path.split(new_file)[0]
                if not os.path.isdir(new_path):
                    os.makedirs(new_path)
                    os.chmod(new_path, 0775)
                file_move_safe(os.path.join(settings.MEDIA_ROOT, field.path), new_file, allow_overwrite=False)
                os.chmod(new_file, 0775)
                setattr(instance, self.name, new_file.replace(settings.MEDIA_ROOT + "/", ""))
                instance.save()
                
                # Now generate all versions if this is an image
                if self.format.title() == 'Image':
                    for v in settings.FILEBROWSER_VERSIONS:
                        # Getattr again as the property has been changed
                        version = getattr(instance, self.name).version_generate(v)
                        os.chmod(os.path.join(settings.MEDIA_ROOT, version.path), 0775)
    
    def contribute_to_class(self, cls, name):
        models.signals.post_save.connect(self.upload_callback, sender=cls)
        super(FileBrowseAndUploadField, self).contribute_to_class(cls, name)
        

if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^filebrowser\.fields\.FileBrowseAndUploadField"])
