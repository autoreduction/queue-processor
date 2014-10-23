/**
    Check is the provided value is a number (int or float)
*/
if(typeof window.isNumber != 'function'){
    window.isNumber = function isNumber(n){
        return !isNaN(parseFloat(n)) && isFinite(n);
    };
}
/**
    Provide string helpers for startsWith and endsWith
*/
if(typeof String.prototype.endsWith != 'function'){
    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };
}
if(typeof String.prototype.startsWith != 'function'){
    String.prototype.startsWith = function (str){
        return this.slice(0, str.length) == str;
    };
}
/**
    Provide string helper to convert text to title case
*/
if(typeof String.prototype.toTitleCase != 'function'){
    String.prototype.toTitleCase = function () {
        var i, str, lowers, uppers;
        var uppercase = new RegExp('[A-Z]');
        str = this.replace(/([^\W_]+[^\s-]*) */g, function (txt) {
            //Do a quick check for *likely* acronyms (4 or less characters and all uppercase)
            if (txt.length <= 4 && txt.match(uppercase)) {
                return txt;
            }
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
     
        // Certain minor words should be left lowercase unless 
        // they are the first or last words in the string
        lowers = ['A', 'An', 'The', 'And', 'But', 'Or', 'For', 'Nor', 'As', 'At',
        'By', 'For', 'From', 'In', 'Into', 'Near', 'Of', 'On', 'Onto', 'To', 'With'];
        for (i = 0; i < lowers.length; i++) {
            str = str.replace(new RegExp('\\s' + lowers[i] + '\\s', 'g'),
                function (txt) {
                    return txt.toLowerCase();
                });
        }
        // Certain words such as initialisms or acronyms should be left uppercase
        uppers = ['Id', 'Stfc'];
        for (i = 0; i < uppers.length; i++) {
            str = str.replace(new RegExp('\\b' + uppers[i] + '\\b', 'g'), uppers[i].toUpperCase());
        }
        return str;
    };
}
/**
    String helper to replace all matches
*/
if(typeof String.prototype.replaceAll != 'function'){
    String.prototype.replaceAll = function (search, replacement) {
        return this.replace(new RegExp(search, 'g'), replacement);
    };
}
/**
    Check is the user is using IE
*/
if(typeof window.isIE != 'function'){
    window.isIE = function isIE(){
        var ua = window.navigator.userAgent;
        return (ua.indexOf('MSIE ') >=0 || ua.indexOf('Trident/') >= 0)
    };
}