import { Terminal } from 'xterm';
export interface IAttachAddonTerminal extends Terminal {
    __socket?: WebSocket;
    __attachSocketBuffer?: string;
    __getMessage?(ev: MessageEvent): void;
    __flushBuffer?(): void;
    __pushToBuffer?(data: string): void;
    __sendData?(data: string): void;
}
