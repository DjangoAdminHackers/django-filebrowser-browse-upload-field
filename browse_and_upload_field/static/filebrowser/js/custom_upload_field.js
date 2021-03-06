(function($){
    $(document).ready(function() {

        function showFB(id_prefix, url){
                FileBrowser.show(
                    id_prefix,
                    url,
                    function(){
                        // Set the text label when the filebrowser window is closed
                        var pathParts = $('#' + id_prefix).val().split('/');
                        var filename = pathParts[pathParts.length -1 ];
                        $('#' + id_prefix + '-textLabel').text(filename);
                    }
                );
            }

        function initUploader($el) {

            var action = $el.data('action');
            var csrf_token = $el.data('title');
            var dir = $el.data('directory');
            var folder = $el.data('folder');
            var format = $el.data('format');
            var id_prefix = $el.data('input-id');
            var title = $el.data('title');
            var url = $el.data('url') + '?pop=1';
            
            if (dir !== undefined) {
                url += '&dir=' + dir;
            }
            if (format !== undefined) {
                url += '&type=' + format;
            }

            if (id_prefix.indexOf('__prefix__') == -1){ // do not add the event listener for empty inline
                $('#' + id_prefix + '-fb_show').click(function(e){
                    e.preventDefault();
                    showFB(id_prefix, url);
                    return false;
                });
            }

            var uploader = new qq.FileUploader({

                element: $el[0],
                action: action,

                template: '<div class="fb-uploader">' +
                            '<div class="fb-upload-list"></div>' +
                            '<a href="javascript://" class="fb-upload-button" title="' + title + '">&nbsp;</a>' +
                            '<div class="fb-upload-drop-area"><span>Drop files here to upload</span></div>' +
                          '</div>',

                // Template for one item in file list
                fileTemplate: '<div class="fb-upload-item">' +
                                '<span class="fb-upload-file"></span>' +
                                '<span class="fb-upload-spinner">&nbsp;</span>' +
                                '<span class="fb-upload-size"></span>' +
                                '<a class="fb-upload-cancel" href="#"></a>' +
                                '<span class="fb-upload-failed-text"></span>' +
                                '<div class="progress-bar">' +
                                    '<div class="content"></div>' +
                                '</div>' +
                              '</div>',

                classes: {
                    // Used to get elements from templates
                    button: 'fb-upload-button',
                    drop: 'fb-upload-drop-area',
                    dropActive: 'fb-upload-drop-area-active',
                    list: 'fb-upload-list',

                    file: 'fb-upload-file',
                    spinner: 'fb-upload-spinner',
                    size: 'fb-upload-size',
                    cancel: 'fb-upload-cancel',

                    // Added to list item when upload completes
                    // Used in css to hide progress spinner
                    success: 'fb-upload-success',
                    fail: 'fb-upload-fail'
                },

                params: {
                    'csrf_token': csrf_token,
                    'csrf_name': 'csrfmiddlewaretoken',
                    'csrf_xname': 'X-CSRFToken',
                    'temporary': 'true',
                    'folder': folder
                },

                minSizeLimit: 0,
                debug: false,

                getItem: function(id) {
                    var items = $(this.element).find('.fb-upload-file').get();
                    var item = items.pop();

                    while (typeof item != "undefined") {
                        if (item.qqFileId == id) {
                            return $(item);
                        }
                        item = items.pop();
                    }
                },

                onProgress: function(id, fileName, loaded, total){
                    var bar = $(this.element).find('.progress-bar .content');
                    var new_width = '' + (loaded/total * 100) + '%';
                    bar.css('width', new_width);
                },

                onComplete: function(id, fileName, resp){
                    if (resp.success) {
                        $(this.element).find('.progress-bar').fadeOut();
                        $('#' + id_prefix).val(resp.uploaded_filename);

                        $('#' + id_prefix + '-textLabel').text(resp.filename);
                        var previewContainer = $el.parent().parent().find('p.preview');
                        previewContainer.find('a').attr('href', resp.url);
                        previewContainer.find('img').attr('src', resp.admin_thumbnail_url);
                        previewContainer.show();
                    }
                },

                showMessage: function(message){
                    alert(message);
                }
                
            });

            // Fix error in django.formset.js caused by the hidden uploader input with no id
            var $container = $el.closest('.fb-uploadfield');
            var id = $container.find('.vFileBrowseField').get(-1).id;
            $container.find('.fb-upload-button input').attr('id', id + '-uploadInput');

        }
        
        function initInline(element) {
            var $container = $(element).find('.fb-uploader-container');
            initUploader($container);
        }

        function initAddedInline(element) {
            var $container = $(element).find('.fb-uploader-container');
            var $textLabel = $(element).find('.fb-uploader-textlabel');
            var $preview = $(element).parent().find('p.preview');
            var $preview_link = $preview.find('a');
            var $preview_img = $preview_link.find('img');
            var $fb_show_link = $(element).parent().find('.fb-show-link');

            var totalFormInput = $container.closest('.inline-group').find('input[id$="TOTAL_FORMS"]');
            var nextRowIndex = totalFormInput.val() - 1;

            $container.attr('id', $container.attr('id').replace('__prefix__', nextRowIndex));
            $textLabel.attr('id', $textLabel.attr('id').replace('__prefix__', nextRowIndex));
            $preview_img.attr('id', $preview_img.attr('id').replace('__prefix__', nextRowIndex));
            $preview_link.attr('id', $preview_link.attr('id').replace('__prefix__', nextRowIndex));
            $preview.attr('id', $preview.attr('id').replace('__prefix__', nextRowIndex));
            $fb_show_link.attr('id', $fb_show_link.attr('id').replace('__prefix__', nextRowIndex));

            var inputId = $container.data('input-id');
            var newInputId = inputId.replace('__prefix__', nextRowIndex);
            $container.data('input-id', newInputId);
            $container.attr('data-input-id', newInputId); // Also keep the DOM in sync or else it's confusing as hell

            initUploader($container);

        }
        
        // See https://github.com/naugtur/insertionQuery
        // Hook to run code after 'add another' has been used on inlines
        // Hooking into the add-row click was unreliable and the only other options were timeout polling
        // For Django 1.9+ we can use https://code.djangoproject.com/ticket/15760 instead
        $('.fb-uploadfield').each(function(){initInline(this)});
        insertionQ('.fb-uploadfield').every(initAddedInline);

        $('form > div > fieldset')  // Non-inlines
            .add('.inline-group > div.inline-related:not(.tabular):not(.empty-form)')  // Stacked inlines
            .add('.inline-group tr:not(.empty-form)')  // Tabular inlines
            .find('.fb-uploader-container')
            .each(function(index) {
                initUploader($(this));
            });
        
    });
    
})(django.jQuery);
