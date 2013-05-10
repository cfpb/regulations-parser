#!/usr/bin/env python
import re
from lxml import etree
from struct import label

reg_xml = '/vagrant/data/regulations/regulation/1005.xml'
doc = etree.parse(reg_xml)

reg_part = int(doc.xpath('//REGTEXT')[0].attrib['PART'])

parent = doc.xpath('//REGTEXT/PART/HD')[0]
title = parent.text

tree = {'label': {
            'parts':[
                reg_part
            ], 
            'text':reg_part, 
            'title':title},
    }

part = doc.xpath('//REGTEXT/PART')[0]
for child in part.getchildren():
    if child.tag == 'SECTION':
        section_title = child.xpath('SECTNO')[0].text + " " + child.xpath('SUBJECT')[0].text
        section_number = int(re.search(r'%d\.(\d+)' % reg_part, section_title).group(1))
        section_text = child.text.strip()
        l = label("%d-%d" % (reg_part, section_number), [reg_part, section_number], section_title)

        for ch in child.getchildren():
            if ch.tag == 'P':
                text_lst = [ch.text] + [c.tail for c in ch if c.tail]
                text = ' '.join(text_lst)
                print text.encode('utf-8', 'ignore')
                
