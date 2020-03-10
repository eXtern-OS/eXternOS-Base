from __future__ import print_function

import libxml2

class Variant:
        def __init__(self, name, desc, raw_desc):
                self.name = name
                self.desc = desc
                self.raw_desc = raw_desc

        def __str__(self):
                return "%s: %s, %s" % (self.name, self.desc, self.raw_desc)

class Layout:
        def __init__(self, name, desc, raw_desc, short_desc, raw_short_desc, variants):
                self.name = name
                self.desc = desc
                self.raw_desc = raw_desc
                self.short_desc = short_desc
                self.raw_short_desc = raw_short_desc
                self.variants = variants
                
        def __str__(self):
                return "%s: %s, %s; %s, %s;; %s" % (self.name,self.desc,self.raw_desc,self.short_desc,self.raw_short_desc,["%s" % x for x in self.variants])

def get_all_layout_possibilities():
        possibility_list = list()
        
        #FIXME: don't call parseFile() twice
        doc = libxml2.parseFile("/etc/X11/xkb/rules/xorg.xml")
        ctxt = doc.xpathNewContext()
                        
        for i in ctxt.xpathEval("/xkbConfigRegistry/layoutList/layout/configItem/name/text()"):
                possibility_list.append(i.content)
        
        return possibility_list

def get_variants(layout_node, lang):
        variant_list = list()

        variant_nodes = layout_node.xpathEval("../../../variantList/variant/configItem/name/text()")
        for i in variant_nodes:
                if len(i.xpathEval("../description[@xml:lang='%s']" % lang)) > 0:
                        trans = i.xpathEval("../description[@xml:lang='%s']" % lang)[0]
                else:
                        trans = ""

                v = Variant(i.content, trans, i.xpathEval("../../description[position()=1]")[0].content)
                variant_list.append(v)
        
        return variant_list


def get_layouts(lang):
        layout_list = list()
        doc = libxml2.parseFile("/etc/X11/xkb/rules/xorg.xml")
        ctxt = doc.xpathNewContext()
        layout_nodes = ctxt.xpathEval("/xkbConfigRegistry/layoutList/layout/configItem/name/text()")

        for i in layout_nodes:
                if i.content == lang:
                        if (len(i.xpathEval("../description[@xml:lang='%s']" % lang)) > 0):
                                translation = i.xpathEval("../description[@xml:lang='%s']" % lang)[0]
                        else:
                                translation = ""
                        if (len(i.xpathEval("../description[@xml:lang='%s']" % lang)) > 0):
                                short_trans = i.xpathEval("../shortDescription[@xml:lang='%s']" % lang)[0]
                        else:
                                short_trans = ""

                        layout_list.append(Layout(i.content, 
                                translation, i.xpathEval("../../description[position()=1]")[0].content, 
                                short_trans, i.xpathEval("../../shortDescription[position()=1]")[0].content,
                                get_variants(i, lang)))

        return layout_list


if __name__ == "__main__":
        for i in get_layouts("fr"): 
                print(i)

        for i in get_all_layout_possibilities():
                print(i)
