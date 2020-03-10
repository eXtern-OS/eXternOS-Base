
# debtags.py -- Access and manipulate Debtags information
# Copyright (C) 2006-2007  Enrico Zini <enrico@enricozini.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function

import re
try:
    import cPickle as pickle
except ImportError:
    import pickle

import six

from debian.deprecation import function_deprecated_by

def parse_tags(input):
	lre = re.compile(r"^(.+?)(?::?\s*|:\s+(.+?)\s*)$")
	for line in input:
		# Is there a way to remove the last character of a line that does not
		# make a copy of the entire line?
		m = lre.match(line)
		pkgs = set(m.group(1).split(', '))
		if m.group(2):
			tags = set(m.group(2).split(', '))
		else:
			tags = set()
		yield pkgs, tags

parseTags = function_deprecated_by(parse_tags)

def read_tag_database(input):
	"Read the tag database, returning a pkg->tags dictionary"
	db = {}
	for pkgs, tags in parse_tags(input):
		# Create the tag set using the native set
		for p in pkgs:
			db[p] = tags.copy()
	return db;

readTagDatabase = function_deprecated_by(read_tag_database)

def read_tag_database_reversed(input):
	"Read the tag database, returning a tag->pkgs dictionary"
	db = {}
	for pkgs, tags in parse_tags(input):
		# Create the tag set using the native set
		for tag in tags:
			if tag in db:
				db[tag] |= pkgs
			else:
				db[tag] = pkgs.copy()
	return db;

readTagDatabaseReversed = function_deprecated_by(read_tag_database_reversed)

def read_tag_database_both_ways(input, tag_filter = None):
	"Read the tag database, returning a pkg->tags and a tag->pkgs dictionary"
	db = {}
	dbr = {}
	for pkgs, tags in parse_tags(input):
		# Create the tag set using the native set
		if tag_filter == None:
			tags = set(tags)
		else:
			tags = set(filter(tag_filter, tags))
		for pkg in pkgs:
			db[pkg] = tags.copy()
		for tag in tags:
			if tag in dbr:
				dbr[tag] |= pkgs
			else:
				dbr[tag] = pkgs.copy()
	return db, dbr;

readTagDatabaseBothWays = function_deprecated_by(read_tag_database_both_ways)

def reverse(db):
	"Reverse a tag database, from package -> tags to tag->packages"
	res = {}
	for pkg, tags in db.items():
		for tag in tags:
			if tag not in res:
				res[tag] = set()
			res[tag].add(pkg)
	return res


def output(db):
	"Write the tag database"
	for pkg, tags in db.items():
		# Using % here seems awkward to me, but if I use calls to
		# sys.stdout.write it becomes a bit slower
		print("%s:" % (pkg), ", ".join(tags))


def relevance_index_function(full, sub):
	#return (float(sub.card(tag)) / float(sub.tag_count())) / \
	#       (float(full.card(tag)) / float(full.tag_count()))
	#return sub.card(tag) * full.card(tag) / sub.tag_count()

	# New cardinality divided by the old cardinality
	#return float(sub.card(tag)) / float(full.card(tag))

	## Same as before, but weighted by the relevance the tag had in the
	## full collection, to downplay the importance of rare tags
	#return float(sub.card(tag) * full.card(tag)) / float(full.card(tag) * full.tag_count())
	# Simplified version:
	#return float(sub.card(tag)) / float(full.tag_count())
	
	# Weighted by the square root of the relevance, to downplay the very
	# common tags a bit
	#return lambda tag: float(sub.card(tag)) / float(full.card(tag)) * math.sqrt(full.card(tag) / float(full.tag_count()))
	#return lambda tag: float(sub.card(tag)) / float(full.card(tag)) * math.sqrt(full.card(tag) / float(full.package_count()))
	# One useless factor removed, and simplified further, thanks to Benjamin Mesing
	return lambda tag: float(sub.card(tag)**2) / float(full.card(tag))

	# The difference between how many packages are in and how many packages are out
	# (problems: tags that mean many different things can be very much out
	# as well.  In the case of 'image editor', for example, there will be
	# lots of editors not for images in the outside group.
	# It is very, very good for nonambiguous keywords like 'image'.
	#return lambda tag: 2 * sub.card(tag) - full.card(tag)
	# Same but it tries to downplay the 'how many are out' value in the
	# case of popular tags, to mitigate the 'there will always be popular
	# tags left out' cases.  Does not seem to be much of an improvement.
	#return lambda tag: sub.card(tag) - float(full.card(tag) - sub.card(tag))/(math.sin(float(full.card(tag))*3.1415/full.package_count())/4 + 0.75)

relevanceIndexFunction = function_deprecated_by(relevance_index_function)

class DB:
	"""
	In-memory database mapping packages to tags and tags to packages.
	"""

	def __init__(self):
		self.db = {}
		self.rdb = {}
	
	def read(self, input, tag_filter=None):
		"""
		Read the database from a file.

		Example::
			# Read the system Debtags database
			db.read(open("/var/lib/debtags/package-tags", "r"))
		"""
		self.db, self.rdb = read_tag_database_both_ways(input, tag_filter)

	def qwrite(self, file):
		"Quickly write the data to a pickled file"
		pickle.dump(self.db, file)
		pickle.dump(self.rdb, file)

	def qread(self, file):
		"Quickly read the data from a pickled file"
		self.db = pickle.load(file)
		self.rdb = pickle.load(file)

	def insert(self, pkg, tags):
		self.db[pkg] = tags.copy()
		for tag in tags:
			if tag in self.rdb:
				self.rdb[tag].add(pkg)
			else:
				self.rdb[tag] = set((pkg))

	def dump(self):
		output(self.db)

	def dump_reverse(self):
		output(self.rdb)

	dumpReverse = function_deprecated_by(dump_reverse)
	
	def reverse(self):
		"Return the reverse collection, sharing tagsets with this one"
		res = DB()
		res.db = self.rdb
		res.rdb = self.db
		return res

	def facet_collection(self):
		"""
		Return a copy of this collection, but replaces the tag names
		with only their facets.
		"""
		fcoll = DB()
		tofacet = re.compile(r"^([^:]+).+")
		for pkg, tags in self.iter_packagesTags():
			ftags = set([tofacet.sub(r"\1", t) for t in tags])
			fcoll.insert(pkg, ftags)
		return fcoll

	facetCollection = function_deprecated_by(facet_collection)

	def copy(self):
		"""
		Return a copy of this collection, with the tagsets copied as
		well.
		"""
		res = DB()
		res.db = self.db.copy()
		res.rdb = self.rdb.copy()
		return res

	def reverse_copy(self):
		"""
		Return the reverse collection, with a copy of the tagsets of
		this one.
		"""
		res = DB()
		res.db = self.rdb.copy()
		res.rdb = self.db.copy()
		return res

	reverseCopy = function_deprecated_by(reverse_copy)

	def choose_packages(self, package_iter):
		"""
		Return a collection with only the packages in package_iter,
		sharing tagsets with this one
		"""
		res = DB()
		db = {}
		for pkg in package_iter:
			if pkg in self.db: db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	choosePackages = function_deprecated_by(choose_packages)

	def choose_packages_copy(self, package_iter):
		"""
		Return a collection with only the packages in package_iter,
		with a copy of the tagsets of this one
		"""
		res = DB()
		db = {}
		for pkg in package_iter:
			db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	choosePackagesCopy = function_deprecated_by(choose_packages_copy)

	def filter_packages(self, package_filter):
		"""
		Return a collection with only those packages that match a
		filter, sharing tagsets with this one.  The filter will match
		on the package.
		"""
		res = DB()
		db = {}
		for pkg in filter(package_filter, six.iterkeys(self.db)):
			db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	filterPackages = function_deprecated_by(filter_packages)

	def filter_packages_copy(self, filter):
		"""
		Return a collection with only those packages that match a
		filter, with a copy of the tagsets of this one.  The filter
		will match on the package.
		"""
		res = DB()
		db = {}
		for pkg in filter(filter, six.iterkeys(self.db)):
			db[pkg] = self.db[pkg].copy()
		res.db = db
		res.rdb = reverse(db)
		return res

	filterPackagesCopy = function_deprecated_by(filter_packages_copy)

	def filter_packages_tags(self, package_tag_filter):
		"""
		Return a collection with only those packages that match a
		filter, sharing tagsets with this one.  The filter will match
		on (package, tags).
		"""
		res = DB()
		db = {}
		for pkg, tags in filter(package_tag_filter, six.iteritems(self.db)):
			db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	filterPackagesTags = function_deprecated_by(filter_packages_tags)

	def filter_packages_tags_copy(self, package_tag_filter):
		"""
		Return a collection with only those packages that match a
		filter, with a copy of the tagsets of this one.  The filter
		will match on (package, tags).
		"""
		res = DB()
		db = {}
		for pkg, tags in filter(package_tag_filter, six.iteritems(self.db)):
			db[pkg] = self.db[pkg].copy()
		res.db = db
		res.rdb = reverse(db)
		return res

	filterPackagesTagsCopy = function_deprecated_by(filter_packages_tags_copy)

	def filter_tags(self, tag_filter):
		"""
		Return a collection with only those tags that match a
		filter, sharing package sets with this one.  The filter will match
		on the tag.
		"""
		res = DB()
		rdb = {}
		for tag in filter(tag_filter, six.iterkeys(self.rdb)):
			rdb[tag] = self.rdb[tag]
		res.rdb = rdb
		res.db = reverse(rdb)
		return res

	filterTags = function_deprecated_by(filter_tags)

	def filter_tags_copy(self, tag_filter):
		"""
		Return a collection with only those tags that match a
		filter, with a copy of the package sets of this one.  The
		filter will match on the tag.
		"""
		res = DB()
		rdb = {}
		for tag in filter(tag_filter, six.iterkeys(self.rdb)):
			rdb[tag] = self.rdb[tag].copy()
		res.rdb = rdb
		res.db = reverse(rdb)
		return res

	filterTagsCopy = function_deprecated_by(filter_tags_copy)

	def has_package(self, pkg):
		"""Check if the collection contains the given package"""
		return pkg in self.db

	hasPackage = function_deprecated_by(has_package)

	def has_tag(self, tag):
		"""Check if the collection contains packages tagged with tag"""
		return tag in self.rdb

	hasTag = function_deprecated_by(has_tag)

	def tags_of_package(self, pkg):
		"""Return the tag set of a package"""
		return pkg in self.db and self.db[pkg] or set()

	tagsOfPackage = function_deprecated_by(tags_of_package)

	def packages_of_tag(self, tag):
		"""Return the package set of a tag"""
		return tag in self.rdb and self.rdb[tag] or set()

	packagesOfTag = function_deprecated_by(packages_of_tag)

	def tags_of_packages(self, pkgs):
		"""Return the set of tags that have all the packages in pkgs"""
		res = None
		for p in pkgs:
			if res == None:
				res = set(self.tags_of_package(p))
			else:
				res &= self.tags_of_package(p)
		return res

	tagsOfPackages = function_deprecated_by(tags_of_packages)

	def packages_of_tags(self, tags):
		"""Return the set of packages that have all the tags in tags"""
		res = None
		for t in tags:
			if res == None:
				res = set(self.packages_of_tag(t))
			else:
				res &= self.packages_of_tag(t)
		return res

	packagesOfTags = function_deprecated_by(packages_of_tags)

	def card(self, tag):
		"""
		Return the cardinality of a tag
		"""
		return tag in self.rdb and len(self.rdb[tag]) or 0

	def discriminance(self, tag):
		"""
		Return the discriminance index if the tag.
		
		Th discriminance index of the tag is defined as the minimum
		number of packages that would be eliminated by selecting only
		those tagged with this tag or only those not tagged with this
		tag.
		"""
		n = self.card(tag)
		tot = self.package_count()
		return min(n, tot - n)

	def iter_packages(self):
		"""Iterate over the packages"""
		return six.iterkeys(self.db)

	iterPackages = function_deprecated_by(iter_packages)

	def iter_tags(self):
		"""Iterate over the tags"""
		return six.iterkeys(self.rdb)

	iterTags = function_deprecated_by(iter_tags)

	def iter_packages_tags(self):
		"""Iterate over 2-tuples of (pkg, tags)"""
		return six.iteritems(self.db)

	iterPackagesTags = function_deprecated_by(iter_packages_tags)

	def iter_tags_packages(self):
		"""Iterate over 2-tuples of (tag, pkgs)"""
		return six.iteritems(self.rdb)

	iterTagsPackages = function_deprecated_by(iter_tags_packages)

	def package_count(self):
		"""Return the number of packages"""
		return len(self.db)

	packageCount = function_deprecated_by(package_count)

	def tag_count(self):
		"""Return the number of tags"""
		return len(self.rdb)

	tagCount = function_deprecated_by(tag_count)

	def ideal_tagset(self, tags):
		"""
		Return an ideal selection of the top tags in a list of tags.

		Return the tagset made of the highest number of tags taken in
		consecutive sequence from the beginning of the given vector,
		that would intersecate with the tagset of a comfortable amount
		of packages.

		Comfortable is defined in terms of how far it is from 7.
		"""

		# TODO: the scoring function is quite ok, but may need more
		# tuning.  I also center it on 15 instead of 7 since we're
		# setting a starting point for the search, not a target point
		def score_fun(x):
			return float((x-15)*(x-15))/x

		hits = []
		tagset = set()
		min_score = 3
		for i in range(len(tags)):
			pkgs = self.packages_of_tags(tags[:i+1])
			card = len(pkgs)
			if card == 0: break;
			score = score_fun(card)
			if score < min_score:
				min_score = score
				tagset = set(tags[:i+1])

		# Return always at least the first tag
		if len(tagset) == 0:
			return set(tags[:1])
		else:
			return tagset

	idealTagset = function_deprecated_by(ideal_tagset)

	def correlations(self):
		"""
		Generate the list of correlation as a tuple (hastag, hasalsotag, score).

		Every touple will indicate that the tag 'hastag' tends to also
		have 'hasalsotag' with a score of 'score'.
		"""
		for pivot in self.iter_tags():
			with_ = self.filter_packages_tags(lambda pt: pivot in pt[1])
			without = self.filter_packages_tags(lambda pt: pivot not in pt[1])
			for tag in with_.iter_tags():
				if tag == pivot: continue
				has = float(with_.card(tag)) / float(with_.package_count())
				hasnt = float(without.card(tag)) / float(without.package_count())
				yield pivot, tag, has - hasnt
