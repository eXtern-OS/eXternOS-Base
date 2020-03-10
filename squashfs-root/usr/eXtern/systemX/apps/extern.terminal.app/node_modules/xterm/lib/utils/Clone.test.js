"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var chai_1 = require("chai");
var Clone_1 = require("./Clone");
describe('clone', function () {
    it('should clone simple objects', function () {
        var test = {
            a: 1,
            b: 2
        };
        chai_1.assert.deepEqual(Clone_1.clone(test), { a: 1, b: 2 });
    });
    it('should clone nested objects', function () {
        var test = {
            bar: {
                a: 1,
                b: 2,
                c: {
                    foo: 'bar'
                }
            }
        };
        chai_1.assert.deepEqual(Clone_1.clone(test), {
            bar: {
                a: 1,
                b: 2,
                c: {
                    foo: 'bar'
                }
            }
        });
    });
    it('should clone null values', function () {
        var test = {
            a: null
        };
        chai_1.assert.deepEqual(Clone_1.clone(test), { a: null });
    });
    it('should clone array values', function () {
        var test = {
            a: [1, 2, 3],
            b: [1, null, 'test', { foo: 'bar' }]
        };
        chai_1.assert.deepEqual(Clone_1.clone(test), {
            a: [1, 2, 3],
            b: [1, null, 'test', { foo: 'bar' }]
        });
    });
    it('should stop mutation from occuring on the original object', function () {
        var test = {
            a: 1,
            b: 2,
            c: {
                foo: 'bar'
            }
        };
        var cloned = Clone_1.clone(test);
        test.a = 5;
        test.c.foo = 'barbaz';
        chai_1.assert.deepEqual(cloned, {
            a: 1,
            b: 2,
            c: {
                foo: 'bar'
            }
        });
    });
    it('should clone to a maximum depth of 5 by default', function () {
        var test = {
            a: {
                b: {
                    c: {
                        d: {
                            e: {
                                f: 'foo'
                            }
                        }
                    }
                }
            }
        };
        var cloned = Clone_1.clone(test);
        test.a.b.c.d.e.f = 'bar';
        chai_1.assert.equal(cloned.a.b.c.d.e.f, 'bar');
    });
    it('should allow an optional maximum depth to be set', function () {
        var test = {
            a: {
                b: {
                    c: 'foo'
                }
            }
        };
        var cloned = Clone_1.clone(test, 2);
        test.a.b.c = 'bar';
        chai_1.assert.equal(cloned.a.b.c, 'bar');
    });
    it('should not throw when cloning a recursive reference', function () {
        var test = {
            a: {
                b: {
                    c: {}
                }
            }
        };
        test.a.b.c = test;
        chai_1.expect(function () { return Clone_1.clone(test); }).to.not.throw();
    });
});

//# sourceMappingURL=Clone.test.js.map
