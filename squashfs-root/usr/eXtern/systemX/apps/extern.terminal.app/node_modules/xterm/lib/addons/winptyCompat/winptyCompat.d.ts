/// <reference path="../../../typings/xterm.d.ts" />
import { Terminal } from 'xterm';
export declare function winptyCompatInit(terminal: Terminal): void;
export declare function apply(terminalConstructor: typeof Terminal): void;
