function getElementsByTagNames(list,obj) {
    if (!obj) var obj = document;
    var tagNames = list.split(',');
    var resultArray = new Array();
    for (var i=0;i<tagNames.length;i++) {
        var tags = obj.getElementsByTagName(tagNames[i]);
        for (var j=0;j<tags.length;j++) {
            resultArray.push(tags[j]);
        }
    }
    var testNode = resultArray[0];
    if (!testNode) return [];
    if (testNode.sourceIndex) {
        resultArray.sort(function (a,b) {
                return a.sourceIndex - b.sourceIndex;
                });
    }
    else if (testNode.compareDocumentPosition) {
        resultArray.sort(function (a,b) {
                return 3 - (a.compareDocumentPosition(b) & 6);
                });
    }
    return resultArray;
}

function createTOC() {
    var y = document.getElementById('innertoc');
    var a = y.appendChild(document.createElement('span'));
    a.id = 'contentheader';
    var z = y.appendChild(document.createElement('div'));
    var toBeTOCced = getElementsByTagNames('h2,h3');
    if (toBeTOCced.length < 2) return false;

    for (var i=0;i<toBeTOCced.length;i++) {
        var tmp = document.createElement('a');
        tmp.innerHTML = toBeTOCced[i].innerHTML;
        tmp.className = 'page';
        z.appendChild(tmp);
        if (toBeTOCced[i].nodeName == 'H3')
            tmp.className += ' indent';
        if (toBeTOCced[i].nodeName == 'H4')
            tmp.className += ' extraindent';
        var headerId = toBeTOCced[i].id || 'link' + i;
        tmp.href = '#' + headerId;
        toBeTOCced[i].id = headerId;
        if (toBeTOCced[i].nodeName == 'H1') {
            tmp.innerHTML = 'Top';
            tmp.href = '#top';
            toBeTOCced[i].id = 'top';
        }
    }
    return y;
}

function showFullDetailsTable() {
    var table = document.getElementById('fullDetails');
    table.style.display = 'block';
    var link = document.getElementById('showFullDetailsLink');
    link.style.display = 'none';
}
function showFullLibrarySummary(tbodyId, aId) {
    var tbody = document.getElementById(tbodyId);
    if(tbody.style.display == 'none') {
        //show it again
        tbody.style.display = '';
        document.getElementById(aId).innerHTML = 'hide';
    } else {
        tbody.style.display = 'none';
        document.getElementById(aId).innerHTML = 'more';
    }
}
