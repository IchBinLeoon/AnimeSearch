$('.to-fate-in').each(function() {
    $(this).addClass('invisible');
})

$(window).scroll(function() {
    inViewport();
});

$(window).resize(function() {
    inViewport();
});

function inViewport() {
    $('.to-fate-in').each(function() {
        const divPos = $(this).offset().top,
            topOfWindow = $(window).scrollTop();
        if(divPos < topOfWindow+400){
            $(this).addClass('visible');
        }
    });
}