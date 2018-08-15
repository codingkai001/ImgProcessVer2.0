window.onload = function () {
    setInterval("scroll()", 1000);

};

function scroll() {
    var title = document.getElementById("title");
    // alert(title.innerHTML);
    var first = title.innerHTML.toString().substring(0, 1);
    var last = title.innerHTML.toString().substring(1, title.innerHTML.length);
    title.innerHTML = last + first;
}