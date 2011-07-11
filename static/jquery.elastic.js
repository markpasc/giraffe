/**
 *    @name        Elastic
 *    @description Elastic is Jquery plugin that grow and shrink your textareas automaticliy
 *    @version     1.6.1
 *    @requires    Jquery 1.2.6+
 *    @author      Jan Jarfalk jan.jarfalk@unwrongest.com
 */

(function(jQuery){
    jQuery.fn.extend({
        elastic: function() {
            //    We will create a div clone of the textarea
            //    by copying these attributes from the textarea to the div.
            var mimics = [
                'paddingTop',
                'paddingRight',
                'paddingBottom',
                'paddingLeft',
                'fontSize',
                'lineHeight',
                'fontFamily',
                'width',
                'fontWeight'];

            return this.each( function() {

                // Elastic only works on textareas
                if ( this.type != 'textarea' ) {
                    return false;
                }

                var $textarea  = jQuery(this),
                    $twin      = jQuery('<div />').css({'position': 'absolute','display':'none', 'whiteSpace': 'pre-wrap'}),
                    lineHeight = parseInt($textarea.css('line-height'),10) || parseInt($textarea.css('font-size'),'10'),
                    minheight  = parseInt($textarea.css('height'),10) || lineHeight*3,
                    maxheight  = parseInt($textarea.css('max-height'),10) || Number.MAX_VALUE,
                    goalheight = 0,
                    i          = 0;

                // Append the twin to the DOM
                // We are going to meassure the height of this, not the textarea.
                $twin.appendTo($textarea.parent());

                // Copy the essential styles (mimics) from the textarea to the twin
                $.each(mimics, function (i, mimic) {
                    $twin.css(mimic, $textarea.css(mimic));
                });

                // Sets a given height and overflow state on the textarea
                function setHeightAndOverflow(height, overflow){
                    var curatedHeight = Math.floor(parseInt(height,10));
                    if($textarea.height() != curatedHeight){
                        $textarea.css({'height': curatedHeight + 'px','overflow':overflow});
                    }
                }

                // This function will update the height of the textarea if necessary
                function update() {

                    // Get curated content from the textarea.
                    var textareaContent = $textarea.val();
                    var twinContent = $twin.text();

                    if(textareaContent != twinContent){

                        // Add an extra white space so new rows are added when you are at the end of a row.
                        $twin.text(textareaContent);

                        // Change textarea height if twin plus the height of one line differs more than 3 pixel from textarea height
                        if(Math.abs($twin.height()+lineHeight - $textarea.height()) > 3){

                            var goalheight = $twin.height()+lineHeight;
                            if(goalheight >= maxheight) {
                                setHeightAndOverflow(maxheight,'auto');
                            } else if(goalheight <= minheight) {
                                setHeightAndOverflow(minheight,'hidden');
                            } else {
                                setHeightAndOverflow(goalheight,'hidden');
                            }

                        }

                    }

                }

                // Hide scrollbars
                $textarea.css({'overflow':'hidden'});

                // Update textarea size on keyup
                $textarea.keyup(function(){ update(); });

                // Run update once when elastic is initialized
                update();

            });

        }
    });
})(jQuery);