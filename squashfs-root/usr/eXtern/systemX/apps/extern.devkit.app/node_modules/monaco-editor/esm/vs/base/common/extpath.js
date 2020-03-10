import { startsWithIgnoreCase } from './strings.js';
import { sep } from './path.js';
export function isEqualOrParent(path, candidate, ignoreCase, separator) {
    if (separator === void 0) { separator = sep; }
    if (path === candidate) {
        return true;
    }
    if (!path || !candidate) {
        return false;
    }
    if (candidate.length > path.length) {
        return false;
    }
    if (ignoreCase) {
        var beginsWith = startsWithIgnoreCase(path, candidate);
        if (!beginsWith) {
            return false;
        }
        if (candidate.length === path.length) {
            return true; // same path, different casing
        }
        var sepOffset = candidate.length;
        if (candidate.charAt(candidate.length - 1) === separator) {
            sepOffset--; // adjust the expected sep offset in case our candidate already ends in separator character
        }
        return path.charAt(sepOffset) === separator;
    }
    if (candidate.charAt(candidate.length - 1) !== separator) {
        candidate += separator;
    }
    return path.indexOf(candidate) === 0;
}
export function isWindowsDriveLetter(char0) {
    return char0 >= 65 /* A */ && char0 <= 90 /* Z */ || char0 >= 97 /* a */ && char0 <= 122 /* z */;
}
