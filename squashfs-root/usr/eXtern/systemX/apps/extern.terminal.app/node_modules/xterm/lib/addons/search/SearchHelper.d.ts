import { ISearchHelper, ISearchAddonTerminal } from './Interfaces';
export declare class SearchHelper implements ISearchHelper {
    private _terminal;
    constructor(_terminal: ISearchAddonTerminal);
    findNext(term: string): boolean;
    findPrevious(term: string): boolean;
    private _findInLine(term, y);
    private _selectResult(result);
}
