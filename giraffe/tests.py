import unittest

from giraffe.activitymessages import MessageSet


class MessageTest(unittest.TestCase):

    def test_simple(self):
        mset = MessageSet()
        mset.add_message("hi")

        self.assertEqual(mset.get_message(), "hi")
        self.assertEqual(mset.get_message(target="hello"), "hi")
        self.assertEqual(mset.get_message(object="moof"), "hi")
        self.assertEqual(mset.get_message(actor="blah", object="moof", target="hello"), "hi")

    def test_rules(self):
        mset = MessageSet()
        mset.add_message("default")
        mset.add_message("with target", target="tag:some:uri")
        mset.add_message("with actor", actor="tag:some:uri")
        mset.add_message("with target and actor", target="tag:some:uri", actor="tag:some:uri")
        mset.add_message("with other target", target="tag:some:other:uri")

        self.assertEqual(mset.get_message(), "default")
        self.assertEqual(mset.get_message(target="tag:some:uri"), "with target")
        self.assertEqual(mset.get_message(actor="tag:some:uri"), "with actor")
        self.assertEqual(mset.get_message(target="tag:some:uri", actor="tag:some:uri"), "with target and actor")
        self.assertEqual(mset.get_message(target="tag:some:other:uri"), "with other target")
