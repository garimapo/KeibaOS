window.addEventListener('DOMContentLoaded', function () {
    var urlParams = new URLSearchParams(window.location.search);
    var scrollToElementId = urlParams.get('scrollTo');
    if (scrollToElementId) {
        ScrollWindow(scrollToElementId);
    }
});

function ScrollWindow(elem) {
    var element = document.getElementById(elem);
    var rect = element.getBoundingClientRect();
    var elemtop = rect.top + window.pageYOffset - 80;
    document.documentElement.scrollTop = elemtop;
}
