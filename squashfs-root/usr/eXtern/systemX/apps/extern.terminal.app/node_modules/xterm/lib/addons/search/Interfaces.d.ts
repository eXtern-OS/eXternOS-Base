import { Terminal } from 'xterm';
export interface ISearchAddonTerminal extends Terminal {
    __searchHelper?: ISearchHelper;
    buffer: any;
    selectionManager: any;
}
export interface ISearchHelper {
    findNext(term: string): boolean;
    findPrevious(term: string): boolean;
}
