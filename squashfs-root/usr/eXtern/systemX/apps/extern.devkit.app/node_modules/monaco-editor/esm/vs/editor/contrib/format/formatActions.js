/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
import { alert } from '../../../base/browser/ui/aria/aria.js';
import { isNonEmptyArray } from '../../../base/common/arrays.js';
import { CancellationToken } from '../../../base/common/cancellation.js';
import { KeyChord } from '../../../base/common/keyCodes.js';
import { dispose } from '../../../base/common/lifecycle.js';
import { EditorState } from '../../browser/core/editorState.js';
import { EditorAction, registerEditorAction, registerEditorContribution } from '../../browser/editorExtensions.js';
import { ICodeEditorService } from '../../browser/services/codeEditorService.js';
import { CharacterSet } from '../../common/core/characterClassifier.js';
import { Range } from '../../common/core/range.js';
import { EditorContextKeys } from '../../common/editorContextKeys.js';
import { DocumentRangeFormattingEditProviderRegistry, OnTypeFormattingEditProviderRegistry } from '../../common/modes.js';
import { IEditorWorkerService } from '../../common/services/editorWorkerService.js';
import { getOnTypeFormattingEdits, getDocumentFormattingEdits, getDocumentRangeFormattingEdits } from './format.js';
import { FormattingEdit } from './formattingEdit.js';
import * as nls from '../../../nls.js';
import { CommandsRegistry } from '../../../platform/commands/common/commands.js';
import { ContextKeyExpr } from '../../../platform/contextkey/common/contextkey.js';
import { ITelemetryService } from '../../../platform/telemetry/common/telemetry.js';
function alertFormattingEdits(edits) {
    edits = edits.filter(function (edit) { return edit.range; });
    if (!edits.length) {
        return;
    }
    var range = edits[0].range;
    for (var i = 1; i < edits.length; i++) {
        range = Range.plusRange(range, edits[i].range);
    }
    var startLineNumber = range.startLineNumber, endLineNumber = range.endLineNumber;
    if (startLineNumber === endLineNumber) {
        if (edits.length === 1) {
            alert(nls.localize('hint11', "Made 1 formatting edit on line {0}", startLineNumber));
        }
        else {
            alert(nls.localize('hintn1', "Made {0} formatting edits on line {1}", edits.length, startLineNumber));
        }
    }
    else {
        if (edits.length === 1) {
            alert(nls.localize('hint1n', "Made 1 formatting edit between lines {0} and {1}", startLineNumber, endLineNumber));
        }
        else {
            alert(nls.localize('hintnn', "Made {0} formatting edits between lines {1} and {2}", edits.length, startLineNumber, endLineNumber));
        }
    }
}
function formatDocumentRange(telemetryService, workerService, editor, rangeOrRangeType, options, token) {
    var state = new EditorState(editor, 1 /* Value */ | 4 /* Position */);
    var model = editor.getModel();
    var range;
    if (rangeOrRangeType === 0 /* Full */) {
        // full
        range = model.getFullModelRange();
    }
    else if (rangeOrRangeType === 1 /* Selection */) {
        // selection or line (when empty)
        range = editor.getSelection();
        if (range.isEmpty()) {
            range = new Range(range.startLineNumber, 1, range.endLineNumber, model.getLineMaxColumn(range.endLineNumber));
        }
    }
    else {
        // as is
        range = rangeOrRangeType;
    }
    return getDocumentRangeFormattingEdits(telemetryService, workerService, model, range, options, 2 /* Manual */, token).then(function (edits) {
        // make edit only when the editor didn't change while
        // computing and only when there are edits
        if (state.validate(editor) && isNonEmptyArray(edits)) {
            FormattingEdit.execute(editor, edits);
            alertFormattingEdits(edits);
            editor.focus();
            editor.revealPositionInCenterIfOutsideViewport(editor.getPosition(), 1 /* Immediate */);
        }
    });
}
function formatDocument(telemetryService, workerService, editor, options, token) {
    var allEdits = [];
    var state = new EditorState(editor, 1 /* Value */ | 4 /* Position */);
    return getDocumentFormattingEdits(telemetryService, workerService, editor.getModel(), options, 2 /* Manual */, token).then(function (edits) {
        // make edit only when the editor didn't change while
        // computing and only when there are edits
        if (state.validate(editor) && isNonEmptyArray(edits)) {
            FormattingEdit.execute(editor, edits);
            alertFormattingEdits(allEdits);
            editor.pushUndoStop();
            editor.focus();
            editor.revealPositionInCenterIfOutsideViewport(editor.getPosition(), 1 /* Immediate */);
        }
    });
}
var FormatOnType = /** @class */ (function () {
    function FormatOnType(editor, _telemetryService, _workerService) {
        var _this = this;
        this._telemetryService = _telemetryService;
        this._workerService = _workerService;
        this._callOnDispose = [];
        this._callOnModel = [];
        this._editor = editor;
        this._callOnDispose.push(editor.onDidChangeConfiguration(function () { return _this.update(); }));
        this._callOnDispose.push(editor.onDidChangeModel(function () { return _this.update(); }));
        this._callOnDispose.push(editor.onDidChangeModelLanguage(function () { return _this.update(); }));
        this._callOnDispose.push(OnTypeFormattingEditProviderRegistry.onDidChange(this.update, this));
    }
    FormatOnType.prototype.update = function () {
        var _this = this;
        // clean up
        this._callOnModel = dispose(this._callOnModel);
        // we are disabled
        if (!this._editor.getConfiguration().contribInfo.formatOnType) {
            return;
        }
        // no model
        if (!this._editor.hasModel()) {
            return;
        }
        var model = this._editor.getModel();
        // no support
        var support = OnTypeFormattingEditProviderRegistry.ordered(model)[0];
        if (!support || !support.autoFormatTriggerCharacters) {
            return;
        }
        // register typing listeners that will trigger the format
        var triggerChars = new CharacterSet();
        for (var _i = 0, _a = support.autoFormatTriggerCharacters; _i < _a.length; _i++) {
            var ch = _a[_i];
            triggerChars.add(ch.charCodeAt(0));
        }
        this._callOnModel.push(this._editor.onDidType(function (text) {
            var lastCharCode = text.charCodeAt(text.length - 1);
            if (triggerChars.has(lastCharCode)) {
                _this.trigger(String.fromCharCode(lastCharCode));
            }
        }));
    };
    FormatOnType.prototype.trigger = function (ch) {
        var _this = this;
        if (!this._editor.hasModel()) {
            return;
        }
        if (this._editor.getSelections().length > 1) {
            return;
        }
        var model = this._editor.getModel();
        var position = this._editor.getPosition();
        var canceled = false;
        // install a listener that checks if edits happens before the
        // position on which we format right now. If so, we won't
        // apply the format edits
        var unbind = this._editor.onDidChangeModelContent(function (e) {
            if (e.isFlush) {
                // a model.setValue() was called
                // cancel only once
                canceled = true;
                unbind.dispose();
                return;
            }
            for (var i = 0, len = e.changes.length; i < len; i++) {
                var change = e.changes[i];
                if (change.range.endLineNumber <= position.lineNumber) {
                    // cancel only once
                    canceled = true;
                    unbind.dispose();
                    return;
                }
            }
        });
        getOnTypeFormattingEdits(this._telemetryService, this._workerService, model, position, ch, model.getFormattingOptions()).then(function (edits) {
            unbind.dispose();
            if (canceled) {
                return;
            }
            if (isNonEmptyArray(edits)) {
                FormattingEdit.execute(_this._editor, edits);
                alertFormattingEdits(edits);
            }
        }, function (err) {
            unbind.dispose();
            throw err;
        });
    };
    FormatOnType.prototype.getId = function () {
        return FormatOnType.ID;
    };
    FormatOnType.prototype.dispose = function () {
        this._callOnDispose = dispose(this._callOnDispose);
        this._callOnModel = dispose(this._callOnModel);
    };
    FormatOnType.ID = 'editor.contrib.autoFormat';
    FormatOnType = __decorate([
        __param(1, ITelemetryService),
        __param(2, IEditorWorkerService)
    ], FormatOnType);
    return FormatOnType;
}());
var FormatOnPaste = /** @class */ (function () {
    function FormatOnPaste(editor, workerService, telemetryService) {
        var _this = this;
        this.editor = editor;
        this.workerService = workerService;
        this.telemetryService = telemetryService;
        this.callOnDispose = [];
        this.callOnModel = [];
        this.callOnDispose.push(editor.onDidChangeConfiguration(function () { return _this.update(); }));
        this.callOnDispose.push(editor.onDidChangeModel(function () { return _this.update(); }));
        this.callOnDispose.push(editor.onDidChangeModelLanguage(function () { return _this.update(); }));
        this.callOnDispose.push(DocumentRangeFormattingEditProviderRegistry.onDidChange(this.update, this));
    }
    FormatOnPaste.prototype.update = function () {
        var _this = this;
        // clean up
        this.callOnModel = dispose(this.callOnModel);
        // we are disabled
        if (!this.editor.getConfiguration().contribInfo.formatOnPaste) {
            return;
        }
        // no model
        if (!this.editor.hasModel()) {
            return;
        }
        var model = this.editor.getModel();
        // no support
        if (!DocumentRangeFormattingEditProviderRegistry.has(model)) {
            return;
        }
        this.callOnModel.push(this.editor.onDidPaste(function (range) {
            _this.trigger(range);
        }));
    };
    FormatOnPaste.prototype.trigger = function (range) {
        if (!this.editor.hasModel()) {
            return;
        }
        if (this.editor.getSelections().length > 1) {
            return;
        }
        var model = this.editor.getModel();
        formatDocumentRange(this.telemetryService, this.workerService, this.editor, range, model.getFormattingOptions(), CancellationToken.None);
    };
    FormatOnPaste.prototype.getId = function () {
        return FormatOnPaste.ID;
    };
    FormatOnPaste.prototype.dispose = function () {
        this.callOnDispose = dispose(this.callOnDispose);
        this.callOnModel = dispose(this.callOnModel);
    };
    FormatOnPaste.ID = 'editor.contrib.formatOnPaste';
    FormatOnPaste = __decorate([
        __param(1, IEditorWorkerService),
        __param(2, ITelemetryService)
    ], FormatOnPaste);
    return FormatOnPaste;
}());
var FormatDocumentAction = /** @class */ (function (_super) {
    __extends(FormatDocumentAction, _super);
    function FormatDocumentAction() {
        return _super.call(this, {
            id: 'editor.action.formatDocument',
            label: nls.localize('formatDocument.label', "Format Document"),
            alias: 'Format Document',
            precondition: EditorContextKeys.writable,
            kbOpts: {
                kbExpr: EditorContextKeys.editorTextFocus,
                primary: 1024 /* Shift */ | 512 /* Alt */ | 36 /* KEY_F */,
                // secondary: [KeyChord(KeyMod.CtrlCmd | KeyCode.KEY_K, KeyMod.CtrlCmd | KeyCode.KEY_D)],
                linux: { primary: 2048 /* CtrlCmd */ | 1024 /* Shift */ | 39 /* KEY_I */ },
                weight: 100 /* EditorContrib */
            },
            menuOpts: {
                when: EditorContextKeys.hasDocumentFormattingProvider,
                group: '1_modification',
                order: 1.3
            }
        }) || this;
    }
    FormatDocumentAction.prototype.run = function (accessor, editor) {
        if (!editor.hasModel()) {
            return;
        }
        var workerService = accessor.get(IEditorWorkerService);
        var telemetryService = accessor.get(ITelemetryService);
        return formatDocument(telemetryService, workerService, editor, editor.getModel().getFormattingOptions(), CancellationToken.None);
    };
    return FormatDocumentAction;
}(EditorAction));
export { FormatDocumentAction };
var FormatSelectionAction = /** @class */ (function (_super) {
    __extends(FormatSelectionAction, _super);
    function FormatSelectionAction() {
        return _super.call(this, {
            id: 'editor.action.formatSelection',
            label: nls.localize('formatSelection.label', "Format Selection"),
            alias: 'Format Code',
            precondition: ContextKeyExpr.and(EditorContextKeys.writable),
            kbOpts: {
                kbExpr: EditorContextKeys.editorTextFocus,
                primary: KeyChord(2048 /* CtrlCmd */ | 41 /* KEY_K */, 2048 /* CtrlCmd */ | 36 /* KEY_F */),
                weight: 100 /* EditorContrib */
            },
            menuOpts: {
                when: ContextKeyExpr.and(EditorContextKeys.hasDocumentSelectionFormattingProvider, EditorContextKeys.hasNonEmptySelection),
                group: '1_modification',
                order: 1.31
            }
        }) || this;
    }
    FormatSelectionAction.prototype.run = function (accessor, editor) {
        if (!editor.hasModel()) {
            return;
        }
        var workerService = accessor.get(IEditorWorkerService);
        var telemetryService = accessor.get(ITelemetryService);
        return formatDocumentRange(telemetryService, workerService, editor, 1 /* Selection */, editor.getModel().getFormattingOptions(), CancellationToken.None);
    };
    return FormatSelectionAction;
}(EditorAction));
export { FormatSelectionAction };
registerEditorContribution(FormatOnType);
registerEditorContribution(FormatOnPaste);
registerEditorAction(FormatDocumentAction);
registerEditorAction(FormatSelectionAction);
// this is the old format action that does both (format document OR format selection)
// and we keep it here such that existing keybinding configurations etc will still work
CommandsRegistry.registerCommand('editor.action.format', function (accessor) {
    var editor = accessor.get(ICodeEditorService).getFocusedCodeEditor();
    if (!editor || !editor.hasModel()) {
        return undefined;
    }
    var workerService = accessor.get(IEditorWorkerService);
    var telemetryService = accessor.get(ITelemetryService);
    if (editor.getSelection().isEmpty()) {
        return formatDocument(telemetryService, workerService, editor, editor.getModel().getFormattingOptions(), CancellationToken.None);
    }
    else {
        return formatDocumentRange(telemetryService, workerService, editor, 1 /* Selection */, editor.getModel().getFormattingOptions(), CancellationToken.None);
    }
});
