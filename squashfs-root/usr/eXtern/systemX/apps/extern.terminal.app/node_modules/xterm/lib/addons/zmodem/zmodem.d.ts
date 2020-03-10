/// <reference path="../../../typings/xterm.d.ts" />
import { Terminal } from 'xterm';
export interface IZModemOptions {
    noTerminalWriteOutsideSession?: boolean;
}
export declare function zmodemAttach(term: Terminal, ws: WebSocket, opts?: IZModemOptions): void;
export declare function apply(terminalConstructor: typeof Terminal): void;
