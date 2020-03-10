{relative, resolve} = require('path')
should = require 'should'
indexer = require '../lib/imageindexer'

testpath = './test/data/'

describe('imageindexer', ->
  describe('#()', () ->
    it('should find images files', (done) ->
      finished = (results) ->
        results.should.have.property(resolve(testpath))
          .with.lengthOf(1)
        file = results[resolve(testpath)][0]
        file.should.have.keys('fullPath', 'stats')
        done()
        
      indexer(testpath)
      .on('done', finished)
      .start()
    )
  )
)
