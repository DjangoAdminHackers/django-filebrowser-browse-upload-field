import json
import os
import re

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.encoding import smart_text

from filebrowser import signals
from filebrowser.base import FileObject
from filebrowser.sites import FileBrowserSite, storage, handle_file_upload
from filebrowser.utils import convert_filename

from filebrowser.settings import ADMIN_THUMBNAIL, OVERWRITE_EXISTING, DEFAULT_PERMISSIONS, UPLOAD_TEMPDIR


class CustomFileBrowserSite(FileBrowserSite):
    
    def _upload_file(self, request):
        """
        Upload file to the server.

        If temporary is true, we upload to UPLOAD_TEMP_DIR, otherwise
        we upload to site.directory
        """
        if request.method == "POST":
            folder = request.GET.get('folder', '')
            temporary = request.GET.get('temporary', '')
            temp_filename = None

            if len(request.FILES) == 0:
                return HttpResponseBadRequest('Invalid request! No files included.')
            if len(request.FILES) > 1:
                return HttpResponseBadRequest('Invalid request! Multiple files included.')

            filedata = list(request.FILES.values())[0]

            fb_uploadurl_re = re.compile(r'^.*(%s)' % reverse("filebrowser:fb_upload", current_app=self.name))
            folder = fb_uploadurl_re.sub('', folder)

            # temporary upload folder should be outside self.directory
            if folder == UPLOAD_TEMPDIR and temporary == "true":
                path = folder
            else:
                path = os.path.join(self.directory, folder)
            # we convert the filename before uploading in order
            # to check for existing files/folders
            file_name = convert_filename(filedata.name)
            filedata.name = file_name
            file_path = os.path.join(path, file_name)
            file_already_exists = self.storage.exists(file_path)

            # construct temporary filename by adding the upload folder, because
            # otherwise we don't have any clue if the file has temporary been
            # uploaded or not
            if folder == UPLOAD_TEMPDIR and temporary == "true":
                temp_filename = os.path.join(folder, file_name)

            # Check for name collision with a directory
            if file_already_exists and self.storage.isdir(file_path):
                ret_json = {'success': False, 'filename': file_name}
                return HttpResponse(json.dumps(ret_json))

            signals.filebrowser_pre_upload.send(sender=request, path=folder, file=filedata, site=self)
            uploadedfile = handle_file_upload(path, filedata, site=self)

            if file_already_exists and OVERWRITE_EXISTING:
                old_file = smart_text(file_path)
                new_file = smart_text(uploadedfile)
                self.storage.move(new_file, old_file, allow_overwrite=True)
                full_path = FileObject(smart_text(old_file), site=self).path_full
            else:
                file_name = smart_text(uploadedfile)
                filedata.name = os.path.relpath(file_name, path)
                full_path = FileObject(smart_text(file_name), site=self).path_full

            # set permissions
            if DEFAULT_PERMISSIONS is not None:
                os.chmod(full_path, DEFAULT_PERMISSIONS)

            f = FileObject(smart_text(file_name), site=self)
            signals.filebrowser_post_upload.send(sender=request, path=folder, file=f, site=self)

            # let Ajax Upload know whether we saved it or not
            ret_json = {
                'success': True,
                'filename': f.filename,
                'temp_filename': temp_filename,
                'url': f.url,
                'admin_thumbnail_url': f.version_generate(ADMIN_THUMBNAIL).url,
            }
            return HttpResponse(json.dumps(ret_json), content_type="application/json")


custom_filebrowser_site = CustomFileBrowserSite(name='filebrowser', storage=storage)
