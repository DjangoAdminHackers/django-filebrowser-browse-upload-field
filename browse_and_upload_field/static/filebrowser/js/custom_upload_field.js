(function($){
    $(document).ready(function() {
        
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
            
            $('#' + id_prefix + '-fb_show').click(function() {
                
                FileBrowser.show(
                    id_prefix,
                    url,
                    function(){
                        // Set the text label when the filebrowser window is closed
                        var pathParts = $('#' + id_prefix).val().split('/');
                        var filename = pathParts[pathParts.length -1 ];
                        $('#' + id_prefix + '-textLabel').text(filename); 
                    });
            });
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
                        $('#' + id_prefix).val(resp.temp_filename);
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
        
        // See https://github.com/naugtur/insertionQuery
        // Hook to run code after 'add another' has been used on inlines
        // Hooking into the add-row click was unreliable and the only other options were timeout polling
        // For Django 1.9+ we can use https://code.djangoproject.com/ticket/15760 instead
        insertionQ('.fb-uploadfield').every(function(element){
            
            var $el = $(element);
            var $container = $el.find('.fb-uploader-container');
            var inlineRowCount = $container.closest('.inline-group')
                    .find('.inline-related').length - 2; // 0 indexed, another -1 for the empty form
            
            var inputId = $container.data('input-id');
            var newInputId = inputId.replace('__prefix__', inlineRowCount);
            $container.data('input-id', newInputId);
            $container.attr('data-input-id', newInputId); // Also keep the DOM in sync or else it's confusing as hell
            
            var id = $container.attr('id');
            $container.attr('id', id.replace('__prefix__', inlineRowCount));
            
            initUploader($container);
            
        });        
        
        $('.fb-uploader-container').each(function(index) {
            var $el = $(this);
            initUploader($el);
        });

    });
    
})(django.jQuery);
