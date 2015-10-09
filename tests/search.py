from unittest import TestCase

from regparser import search


class SearchTest(TestCase):

    def test_find_start(self):
        text = "Here is \n Some text\nWith Some\nHeader Info Here"
        text += "\nthen nonsense"
        self.assertEqual(30, search.find_start(text, "Header", "Info"))
        self.assertEqual(0, search.find_start(text, "Here", "is"))
        self.assertEqual(47, search.find_start(text, "then", "nonsense"))
        self.assertEqual(None, search.find_start(text, "doesn't", "exist"))
        self.assertEqual(None, search.find_start(text, "Here", "text"))

    def test_find_offsets(self):
        text = "Trying to find the start of this section and the other "
        text += "start here"
        self.assertEqual((19, 55),
                         search.find_offsets(text, lambda t: t.find("start")))
        self.assertEqual((10, len(text)),
                         search.find_offsets(text, lambda t: t.find("find")))
        self.assertEqual((0, len(text)),
                         search.find_offsets(text, lambda t: t.find("Trying")))
        self.assertEqual(None,
                         search.find_offsets(text, lambda t: t.find("xxxx")))

    def test_find_segments_offsets(self):
        def offsets(text, seg_id, exclude):
            if text:
                return (4, 9)
        text = "This is some text, lalalala text text song."
        segs = search.segments(text, offsets)
        self.assertEqual(5, len(segs))
        self.assertEqual((4, 9), segs[0])
        self.assertEqual((13, 18), segs[1])
        self.assertEqual((22, 27), segs[2])
        self.assertEqual((31, 36), segs[3])
        self.assertEqual((40, 45), segs[4])

    def test_find_segments_seg_ids(self):
        seg_ids = []

        def offsets(text, seg_id, exclude):
            if text:
                seg_ids.append(seg_id)
                return (4, 9)
        text = "This is some text, lalalala text text song."
        search.segments(text, offsets)
        self.assertEqual([0, 1, 2, 3, 4], seg_ids)

    def test_find_segments_excludes(self):
        excludes = []

        def offsets(text, seg_id, exclude):
            if text:
                excludes.append(exclude)
                return (4, 9)
        text = "This is some text, lalalala text text song."
        search.segments(text, offsets, [(20, 24), (3, 5)])
        self.assertEqual(5, len(excludes))
        for i in range(5):
            self.assertEqual(2, len(excludes[i]))
        self.assertEqual([(20, 24), (3, 5)], excludes[0])
        self.assertEqual([(11, 15), (-6, -4)], excludes[1])
        self.assertEqual((2, 6), excludes[2][0])
        self.assertEqual((-7, -3), excludes[3][0])
