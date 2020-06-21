import unittest
import tempfile

from godot_parser import GDScene, Node, ExtResource, GDObject


class TestGDFile(unittest.TestCase):

    """ Tests for GDFile """

    def test_basic_scene(self):
        """ Run the parsing test cases """
        self.assertEqual(str(GDScene()), "[gd_scene load_steps=1 format=2]\n")

    def test_ext_resource(self):
        """ Test serializing a scene with an ext_resource """
        scene = GDScene()
        scene.add_ext_resource("res://Other.tscn", "PackedScene")
        self.assertEqual(
            str(scene),
            """[gd_scene load_steps=2 format=2]

[ext_resource path="res://Other.tscn" type="PackedScene" id=1]
""",
        )

    def test_sub_resource(self):
        """ Test serializing a scene with an sub_resource """
        scene = GDScene()
        scene.add_sub_resource("Animation")
        self.assertEqual(
            str(scene),
            """[gd_scene load_steps=2 format=2]

[sub_resource type="Animation" id=1]
""",
        )

    def test_node(self):
        """ Test serializing a scene with a node """
        scene = GDScene()
        scene.add_node("RootNode", type="Node2D")
        scene.add_node("Child", type="Area2D", parent=".")
        self.assertEqual(
            str(scene),
            """[gd_scene load_steps=1 format=2]

[node name="RootNode" type="Node2D"]

[node name="Child" type="Area2D" parent="."]
""",
        )

    def test_tree_create(self):
        """ Test creating a scene with the tree API """
        scene = GDScene()
        with scene.use_tree() as tree:
            tree.root = Node("RootNode", type="Node2D")
            tree.root.add_child(
                Node("Child", type="Area2D", properties={"visible": False})
            )
        self.assertEqual(
            str(scene),
            """[gd_scene load_steps=1 format=2]

[node name="RootNode" type="Node2D"]

[node name="Child" type="Area2D" parent="."]
visible = false
""",
        )

    def test_tree_deep_create(self):
        """ Test creating a scene with nested children using the tree API """
        scene = GDScene()
        with scene.use_tree() as tree:
            tree.root = Node("RootNode", type="Node2D")
            child = Node("Child", type="Node")
            tree.root.add_child(child)
            child.add_child(Node("ChildChild", type="Node"))
            child.add_child(Node("ChildChild2", type="Node"))
        self.assertEqual(
            str(scene),
            """[gd_scene load_steps=1 format=2]

[node name="RootNode" type="Node2D"]

[node name="Child" type="Node" parent="."]

[node name="ChildChild" type="Node" parent="Child"]

[node name="ChildChild2" type="Node" parent="Child"]
""",
        )

    def test_remove_section(self):
        """ Test that you can remove sections """
        scene = GDScene()
        scene.add_node("RootNode", type="Node2D")
        node = scene.add_node("Child", type="Area2D", parent=".")
        self.assertTrue(scene.remove_section(node))
        self.assertEqual(len(scene.get_sections()), 2)

    def test_section_ordering(self):
        """ Sections maintain an ordering """
        scene = GDScene()
        node = scene.add_node("RootNode")
        scene.add_ext_resource("res://Other.tscn", "PackedScene")
        res = scene.find_section("ext_resource")
        self.assertEqual(scene.get_sections()[1:], [res, node])

    def test_add_ext_node(self):
        """ Test GDScene.add_ext_node """
        scene = GDScene()
        res_id = scene.add_ext_resource("res://Other.tscn", "PackedScene")
        node = scene.add_ext_node("Root", res_id)
        self.assertEqual(node.name, "Root")
        self.assertEqual(node.instance, res_id)

    def test_write(self):
        """ Test writing scene out to a file """
        scene = GDScene()
        outfile = tempfile.mkstemp()[1]
        scene.write(outfile)
        with open(outfile, "r") as ifile:
            gen_scene = GDScene.parse(ifile.read())
        self.assertEqual(scene, gen_scene)

    def test_get_node_none(self):
        """ get_node() works with no nodes """
        scene = GDScene()
        n = scene.get_node()
        self.assertIsNone(n)

    def test_addremove_ext_res(self):
        """ Test adding and removing an ext_resource """
        scene = GDScene()
        res_id = scene.add_ext_resource("res://Res.tscn", "PackedScene")
        self.assertEqual(res_id, 1)
        res2_id = scene.add_ext_resource("res://Sprite.png", "Texture")
        self.assertEqual(res2_id, 2)
        node = scene.add_node("Sprite", "Sprite")
        node["texture"] = ExtResource(res2_id)
        node["textures"] = [ExtResource(res2_id)]
        node["texture_map"] = {"tex": ExtResource(res2_id)}
        node["texture_pool"] = GDObject("ResourcePool", ExtResource(res2_id))

        s = scene.find_section(path="res://Res.tscn")
        scene.remove_section(s)

        s = scene.find_section("ext_resource")
        self.assertEqual(s.id, 1)
        self.assertEqual(node["texture"].id, 1)
        self.assertEqual(node["textures"][0].id, 1)
        self.assertEqual(node["texture_map"]["tex"].id, 1)
        self.assertEqual(node["texture_pool"].args[0].id, 1)