# vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

from regparser.notice import address


class NoticeAddressTests(TestCase):

    def test_fetch_addreses_none(self):
        xml = """
        <ROOT>
            <ADD>
                <HD>ADDRESSES:</HD>
            </ADD>
        </ROOT>"""
        self.assertEqual(None, address.fetch_addresses(etree.fromstring(xml)))
        xml = """
        <ROOT>
            <CHILD />
        </ROOT>"""
        self.assertEqual(None, address.fetch_addresses(etree.fromstring(xml)))

    def test_fetch_addresses(self):
        xml = """
        <ROOT>
            <ADD>
                <HD>ADDRESSES:</HD>
                <P>Here is some initial instruction.</P>
                <P><E T="03">Electronic: http://www.example.com.</E> MSG</P>
                <P>Mail: Some address here</P>
                <P>Blah Blah: Final method description</P>
                <P>And then, we have some instructions</P>
                <P>Followed by more instructions.</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(address.fetch_addresses(etree.fromstring(xml)), {
            'intro': 'Here is some initial instruction.',
            'methods': [
                ('Electronic', 'http://www.example.com. MSG'),
                ('Mail', 'Some address here'),
                ('Blah Blah', 'Final method description')
            ],
            'instructions': [
                'And then, we have some instructions',
                'Followed by more instructions.'
            ]
        })

    def test_fetch_addresses_no_intro(self):
        xml = """
        <ROOT>
            <ADD>
                <P>Mail: Some address here</P>
                <P>Followed by more instructions.</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(address.fetch_addresses(etree.fromstring(xml)), {
            'methods': [('Mail', 'Some address here')],
            'instructions': ['Followed by more instructions.']
        })

    def test_fetch_address_http(self):
        xml = """
        <ROOT>
            <ADD>
                <P>Mail:Something here</P>
                <P>Otherwise, visit http://example.com</P>
                <P>or https://example.com</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(address.fetch_addresses(etree.fromstring(xml)), {
            'methods': [('Mail', 'Something here')],
            'instructions': [
                'Otherwise, visit http://example.com',
                'or https://example.com'
            ]
        })

    def test_fetch_address_instructions(self):
        xml = """
        <ROOT>
            <ADD>
                <P>Mail: Something something</P>
                <P>Instructions: Do these things</P>
                <P>Then do those things</P>
            </ADD>
        </ROOT>"""
        self.assertEqual(address.fetch_addresses(etree.fromstring(xml)), {
            'methods': [('Mail', 'Something something')],
            'instructions': ['Do these things', 'Then do those things']
        })

    def test_cleanup_address_p_bullet(self):
        xml = u"""<P>• Bullet: value</P>"""
        self.assertEqual(address.cleanup_address_p(etree.fromstring(xml)),
                         'Bullet: value')

    def test_cleanup_address_p_smushed_tag(self):
        xml = """<P>See<E T="03">This</E></P>"""
        self.assertEqual(address.cleanup_address_p(etree.fromstring(xml)),
                         'See This')

    def test_cleanup_address_p_without_contents(self):
        xml = """<P>See<E /> here!</P>"""
        self.assertEqual(address.cleanup_address_p(etree.fromstring(xml)),
                         'See here!')

    def test_cleanup_address_p_subchildren(self):
        xml = """<P>Oh<E T="03">yeah</E>man</P>"""
        self.assertEqual(address.cleanup_address_p(etree.fromstring(xml)),
                         'Oh yeah man')
