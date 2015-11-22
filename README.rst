Django FileBrowser Browse and Upload Field
==================

This field combines the normal FilebrowseField with the direct upload functionality of the UploadField. The widget has both an upload and browse button.

Requirements
------------

* django-filebrowser-no-grappelli 3.6+ ( https://github.com/smacker/django-filebrowser-no-grappelli )

Installation
------------

* add 'browse_and_upload_field' to INSTALLED_APPS
* from browse_and_upload_field.fields import FileBrowseAndUploadField
* Use in the same way as the existing FileBrowseField and UploadField

    my_image = FileBrowseAndUploadField(max_length=512, null=True, blank=True, format="image", directory='images', upload_to='images')
