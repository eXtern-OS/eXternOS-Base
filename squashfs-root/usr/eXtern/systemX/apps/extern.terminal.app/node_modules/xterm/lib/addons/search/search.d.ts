/// <reference path="../../../typings/xterm.d.ts" />
import { Terminal } from 'xterm';
export declare function findNext(terminal: Terminal, term: string): boolean;
export declare function findPrevious(terminal: Terminal, term: string): boolean;
export declare function apply(terminalConstructor: typeof Terminal): void;
