from setuptools import find_packages
from setuptools import setup

setup(
    name='django-filebrowser-browse-upload-field',
    version='0.0.1',
    description='django-filebrowser-browse-upload-field',
    author='Andy Baker',
    author_email='andy@andybak.net',
    packages=find_packages(),
    package_data={
        'browse_and_upload_field': [
            'templates/filebrowser/*.html',
            'static/filebrowser/js/*.js',
        ]
    },
    include_package_data=True,
)
