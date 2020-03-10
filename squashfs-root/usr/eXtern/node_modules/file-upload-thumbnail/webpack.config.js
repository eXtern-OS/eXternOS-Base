var path = require('path');

module.exports = [{
  entry: {
    file_upload_thumbnail: './index.js'
  },
  output: {
		filename: '[name].js',
    path: path.join('./dist/'),
		library: 'FileUploadThumbnail',
		libraryTarget: 'var'
  }
}];
