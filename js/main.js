function invite() {
    window.location.href = 'https://discord.com/oauth2/authorize?client_id=737236600878137363&permissions=124992&scope=bot';
}

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