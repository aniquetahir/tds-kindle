article = document.getElementsByTagName('article')[0];
document.getElementById('root').remove();
document.body.innerHTML = article.outerHTML + document.body.innerHTML;