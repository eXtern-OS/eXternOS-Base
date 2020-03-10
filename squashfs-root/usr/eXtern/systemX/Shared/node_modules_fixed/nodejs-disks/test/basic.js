var mocha = require("mocha");
var should  = require("should");

var disk = require("../");


describe('Basic Interface', function(){

	it("should have a few functions", function(done){
		disk.drives.should.be.Function
		disk.driveDetail.should.be.Function
		disk.drivesDetail.should.be.Function
		done();
	});


	it("mount should not be empty", function(done){
		disk.drives(function (err, drives) {
			should.not.exist(err);
			disk.drivesDetail(drives, function (err, diskResults) {
				should.not.exist(err);
				diskResults.should.be.Array;
				diskResults[0].mountpoint.should.not.containEql("\n");
				done();
			});
		});
	});
	
	it("mount free percentage should be a number", function(done){
		disk.drives(function (err, drives) {
			should.not.exist(err);
			disk.drivesDetail(drives, function (err, diskResults) {
				should.not.exist(err);
				diskResults.should.be.Array;
				parseInt(diskResults[0].freePer).should.be.Number;
				done();
			});
		});
	});
	
	it("mount used percentage should be a number", function(done){
		disk.drives(function (err, drives) {
			should.not.exist(err);
			disk.drivesDetail(drives, function (err, diskResults) {
				should.not.exist(err);
				diskResults.should.be.Array;
				parseInt(diskResults[0].usedPer).should.be.Number;
				done();
			});
		});
	});


	it("mount total space should be a number", function(done){
		disk.drives(function (err, drives) {
			should.not.exist(err);
			disk.drivesDetail(drives, function (err, diskResults) {
				should.not.exist(err);
				diskResults.should.be.Array;
				parseInt(diskResults[0].usedPer).should.be.Number;
				done();
			});
		});
	});
	
	it("mount used space should be a number", function(done){
		disk.drives(function (err, drives) {
			should.not.exist(err);
			disk.drivesDetail(drives, function (err, diskResults) {
				should.not.exist(err);
				diskResults.should.be.Array;
				parseInt(diskResults[0].used).should.be.Number;
				done();
			});
		});
	});
});