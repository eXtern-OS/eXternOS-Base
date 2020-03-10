fs = require 'fs'
async = require 'async'
should = require 'should'
MediaLibrary = require '../lib/medialibrary'

dataset = require './dataset'
opts =
  paths: [dataset.path]

describe('MediaLibrary', () ->
  medialib = null

  beforeEach(->
    medialib = new MediaLibrary(opts)
  )

  describe('#scan()', () ->

    it('should return found tracks', (done) ->
      medialib.scan()
        .on('done', (tracks) ->
          tracks.length.should.equal(dataset.files.length)
          done()
        )
        .on('error', done)
    )

    it('should notify progress', (done) ->
      trackCount = 0
      medialib.scan()
        .on('track', ->
          trackCount++
        )
        .on('done', (tracks) ->
          tracks.length.should.equal(dataset.files.length)
          trackCount.should.equal(dataset.files.length)
          done()
        )
        .on('error', done)
    )

    it('should insert path and metadata', (done) ->
      medialib.scan()
        .on('done', (tracks) ->
          track = tracks
            .filter((t) -> /Artist 1 - Track 1\.mp3$/.test(t.path))[0]
          track.should.be.ok
          track.root.should.ok
          track.path.should.ok
          track.title.should.ok
          track.artist.should.ok
          track.artist[0].should.ok
          done()
        )
        .on('error', done)
    )

  )


  describe('#tracks()', () ->

    beforeEach((done) ->
      medialib.scan()
      .on('done', -> done())
      .on('error', done)
    )

    it('should return tracks', (done) ->
      medialib.tracks((err, tracks) ->
        return done(err) if err
        tracks.should.be.instanceof(Array)
          .and.have.lengthOf(dataset.files.length)
        done()
      )
    )

    it('should return artist tracks when called with artist filter', (done) ->
      medialib.tracks({ artist: 'Artist 1' }, (err, tracks) ->
        return done(err) if err
        tracks.should.be.instanceof(Array)
          .and.have.lengthOf(2)
        done()
      )
    )

  )


  describe('#artists()', () ->

    beforeEach((done) ->
      medialib.scan()
      .on('done', -> done())
      .on('error', done)
    )

    it('should return distinct artists', (done) ->
      medialib.artists((err, artists) ->
        return done(err) if err
        artists.map((a) -> a.name).should.eql(['Artist 1', 'Artist 2'])
        done()
      )
    )

  )


  describe('#albums()', () ->

    beforeEach((done) ->
      medialib.scan()
      .on('done', -> done())
      .on('error', done)
    )

    it('should return distinct albums', (done) ->
      medialib.albums((err, albums) ->
        return done(err) if err
        albums.map((a) -> a.artist)
          .should.eql(['Artist 1', 'Artist 2'])
        albums.map((a) -> a.title)
          .should.eql(['Album 1', 'Album 2'])
        done()
      )
    )

  )


  describe('#findTracks()', () ->

    beforeEach((done) ->
      medialib.scan()
      .on('done', -> done())
      .on('error', done)
    )

    it('should find by artist', (done) ->
      medialib.findTracks({artist: 'Artist 1'}, (err, results) ->
        return done(err) if err
        results.should.have.length(2)
        done()
      )
    )

    it('should find by title', (done) ->
      medialib.findTracks({title: 'Track 1'}, (err, results) ->
        return done(err) if err
        results.should.have.length(2)
        done()
      )
    )

  )


  describe('#files()', ->

    beforeEach((done) ->
      medialib.scan()
      .on('done', -> done())
      .on('error', done)
    )

    it('should return root folder if called without argument', (done) ->
      medialib.files((err, files) ->
        return done(err) if err
        files.should.be.instanceof(Array).and.have.lengthOf(1)
        files[0].should.have.property('type', 'folder')
        files[0].should.have.property('name', 'data')
        done()
      )
    )

    it('should return subfolders when called with a folder path', (done) ->
      medialib.files(dataset.path, (err, files) ->
        return done(err) if err
        files.filter((file) -> file.type == 'folder')
          .should.have.lengthOf(1)
        done()
      )
    )

    it('should return files when called with a folder path', (done) ->
      medialib.files(dataset.path, (err, files) ->
        return done(err) if err
        files.filter((file) -> file.type == 'file')
          .should.have.lengthOf(3)
        done()
      )
    )

  )


  describe('#scanCovers()', ->

    beforeEach((done) ->
      medialib.scan()
      .on('done', -> done())
      .on('error', done)
    )

    it('should create covers property on tracks', (done) ->
      medialib.scanCovers((err, totalUpdated) ->
        totalUpdated.should.equal(3)
        medialib.tracks((err, tracks) ->
          done(err) if err?
          tracksWithCovers = tracks.filter((track) -> track.covers)
          tracksWithCovers.should.have.lengthOf(3)
          tracksWithCovers[0].covers.should
            .be.instanceOf(Array)
            .with.lengthOf(1)
          tracksWithCovers[0].covers[0].should.eql(
            name: 'cover.jpg'
            size: 631
          )
          done()
        )
      )
    )

  )


)
