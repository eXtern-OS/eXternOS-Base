"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
function addDisposableListener(node, type, handler, useCapture) {
    node.addEventListener(type, handler, useCapture);
    return {
        dispose: function () {
            if (!handler) {
                return;
            }
            node.removeEventListener(type, handler, useCapture);
            node = null;
            handler = null;
        }
    };
}
exports.addDisposableListener = addDisposableListener;

//# sourceMappingURL=Dom.js.map
