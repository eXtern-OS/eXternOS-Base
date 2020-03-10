/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
import { illegalArgument, onUnexpectedExternalError } from '../../../base/common/errors.js';
import { URI } from '../../../base/common/uri.js';
import { isNonEmptyArray } from '../../../base/common/arrays.js';
import { Range } from '../../common/core/range.js';
import { registerLanguageCommand } from '../../browser/editorExtensions.js';
import { DocumentFormattingEditProviderRegistry, DocumentRangeFormattingEditProviderRegistry, OnTypeFormattingEditProviderRegistry } from '../../common/modes.js';
import { IModelService } from '../../common/services/modelService.js';
import { first } from '../../../base/common/async.js';
import { Position } from '../../common/core/position.js';
import { CancellationToken } from '../../../base/common/cancellation.js';
import { IEditorWorkerService } from '../../common/services/editorWorkerService.js';
import { ITelemetryService } from '../../../platform/telemetry/common/telemetry.js';
var _conflictResolver;
function invokeFormatterCallback(formatter, model, mode) {
    if (_conflictResolver) {
        var ids = formatter.map(function (formatter) { return formatter.extensionId; });
        _conflictResolver(ids, model, mode);
    }
}
export function getDocumentRangeFormattingEdits(telemetryService, workerService, model, range, options, mode, token) {
    return __awaiter(this, void 0, void 0, function () {
        var providers;
        return __generator(this, function (_a) {
            providers = DocumentRangeFormattingEditProviderRegistry.ordered(model);
            /* __GDPR__
                "formatterInfo" : {
                    "type" : { "classification": "SystemMetaData", "purpose": "FeatureInsight" },
                    "language" : { "classification": "SystemMetaData", "purpose": "FeatureInsight" },
                    "count" : { "classification": "SystemMetaData", "purpose": "FeatureInsight", "isMeasurement": true }
                }
             */
            telemetryService.publicLog('formatterInfo', {
                type: 'range',
                language: model.getLanguageIdentifier().language,
                count: providers.length,
            });
            invokeFormatterCallback(providers, model, mode | 16 /* Range */);
            return [2 /*return*/, first(providers.map(function (provider) { return function () {
                    return Promise.resolve(provider.provideDocumentRangeFormattingEdits(model, range, options, token)).catch(onUnexpectedExternalError);
                }; }), isNonEmptyArray).then(function (edits) {
                    // break edits into smaller edits
                    return workerService.computeMoreMinimalEdits(model.uri, edits);
                })];
        });
    });
}
export function getDocumentFormattingEdits(telemetryService, workerService, model, options, mode, token) {
    var docFormattingProviders = DocumentFormattingEditProviderRegistry.ordered(model);
    /* __GDPR__
        "formatterInfo" : {
            "type" : { "classification": "SystemMetaData", "purpose": "FeatureInsight" },
            "language" : { "classification": "SystemMetaData", "purpose": "FeatureInsight" },
            "count" : { "classification": "SystemMetaData", "purpose": "FeatureInsight", "isMeasurement": true }
        }
     */
    telemetryService.publicLog('formatterInfo', {
        type: 'document',
        language: model.getLanguageIdentifier().language,
        count: docFormattingProviders.length,
    });
    if (docFormattingProviders.length > 0) {
        return first(docFormattingProviders.map(function (provider) { return function () {
            // first with result wins...
            return Promise.resolve(provider.provideDocumentFormattingEdits(model, options, token)).catch(onUnexpectedExternalError);
        }; }), isNonEmptyArray).then(function (edits) {
            // break edits into smaller edits
            return workerService.computeMoreMinimalEdits(model.uri, edits);
        });
    }
    else {
        // try range formatters when no document formatter is registered
        return getDocumentRangeFormattingEdits(telemetryService, workerService, model, model.getFullModelRange(), options, mode | 8 /* Document */, token);
    }
}
export function getOnTypeFormattingEdits(telemetryService, workerService, model, position, ch, options) {
    var providers = OnTypeFormattingEditProviderRegistry.ordered(model);
    /* __GDPR__
        "formatterInfo" : {
            "type" : { "classification": "SystemMetaData", "purpose": "FeatureInsight" },
            "language" : { "classification": "SystemMetaData", "purpose": "FeatureInsight" },
            "count" : { "classification": "SystemMetaData", "purpose": "FeatureInsight", "isMeasurement": true }
        }
     */
    telemetryService.publicLog('formatterInfo', {
        type: 'ontype',
        language: model.getLanguageIdentifier().language,
        count: providers.length,
    });
    if (providers.length === 0) {
        return Promise.resolve(undefined);
    }
    if (providers[0].autoFormatTriggerCharacters.indexOf(ch) < 0) {
        return Promise.resolve(undefined);
    }
    return Promise.resolve(providers[0].provideOnTypeFormattingEdits(model, position, ch, options, CancellationToken.None)).catch(onUnexpectedExternalError).then(function (edits) {
        return workerService.computeMoreMinimalEdits(model.uri, edits);
    });
}
registerLanguageCommand('_executeFormatRangeProvider', function (accessor, args) {
    var resource = args.resource, range = args.range, options = args.options;
    if (!(resource instanceof URI) || !Range.isIRange(range)) {
        throw illegalArgument();
    }
    var model = accessor.get(IModelService).getModel(resource);
    if (!model) {
        throw illegalArgument('resource');
    }
    return getDocumentRangeFormattingEdits(accessor.get(ITelemetryService), accessor.get(IEditorWorkerService), model, Range.lift(range), options, 1 /* Auto */, CancellationToken.None);
});
registerLanguageCommand('_executeFormatDocumentProvider', function (accessor, args) {
    var resource = args.resource, options = args.options;
    if (!(resource instanceof URI)) {
        throw illegalArgument('resource');
    }
    var model = accessor.get(IModelService).getModel(resource);
    if (!model) {
        throw illegalArgument('resource');
    }
    return getDocumentFormattingEdits(accessor.get(ITelemetryService), accessor.get(IEditorWorkerService), model, options, 1 /* Auto */, CancellationToken.None);
});
registerLanguageCommand('_executeFormatOnTypeProvider', function (accessor, args) {
    var resource = args.resource, position = args.position, ch = args.ch, options = args.options;
    if (!(resource instanceof URI) || !Position.isIPosition(position) || typeof ch !== 'string') {
        throw illegalArgument();
    }
    var model = accessor.get(IModelService).getModel(resource);
    if (!model) {
        throw illegalArgument('resource');
    }
    return getOnTypeFormattingEdits(accessor.get(ITelemetryService), accessor.get(IEditorWorkerService), model, Position.lift(position), ch, options);
});
