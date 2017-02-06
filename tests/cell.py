######################################################################
#                                                                    #
#  Copyright 2009-2017 Lucas Heitzmann Gabrielli                     #
#                                                                    #
#  This file is part of gdspy.                                       #
#                                                                    #
#  gdspy is free software: you can redistribute it and/or modify it  #
#  under the terms of the GNU General Public License as published    #
#  by the Free Software Foundation, either version 3 of the          #
#  License, or any later version.                                    #
#                                                                    #
#  gdspy is distributed in the hope that it will be useful, but      #
#  WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
#  GNU General Public License for more details.                      #
#                                                                    #
#  You should have received a copy of the GNU General Public         #
#  License along with gdspy.  If not, see                            #
#  <http://www.gnu.org/licenses/>.                                   #
#                                                                    #
######################################################################

import pytest
import gdspy
import numpy
import uuid


def unique():
    return str(uuid.uuid4())


def test_duplicate():
    name = 'c_duplicate'
    c1 = gdspy.Cell(name)
    with pytest.raises(ValueError) as e:
        c2 = gdspy.Cell(name)
    assert name in str(e.value)


def test_ignore_duplicate():
    c1 = gdspy.Cell('c_ignore_duplicate')
    c2 = gdspy.Cell(c1.name, True)


def test_add_element():
    p = gdspy.Polygon(((0, 0), (1, 0), (0, 1)))
    c = gdspy.Cell('c_add_element')
    assert c.add(p) is c
    assert c.add([p, p]) is c
    assert c.elements == [p, p, p]


def test_add_label():
    l = gdspy.Label('label', (0, 0))
    c = gdspy.Cell('c_add_label')
    assert c.add(l) is c
    assert c.add([l, l]) is c
    assert c.labels == [l, l, l]


def test_copy():
    name = 'c_copy'
    p = gdspy.Polygon(((0, 0), (1, 0), (0, 1)))
    l = gdspy.Label('label', (0, 0))
    c1 = gdspy.Cell(name)
    c1.add(p)
    c1.add(l)
    with pytest.raises(ValueError) as e:
        c2 = c1.copy(name)
    assert name in str(e.value)

    c3 = c1.copy(name, True)
    assert c3.elements == c1.elements and c3.elements is not c1.elements
    assert c3.labels == c1.labels and c3.labels is not c1.labels

    c4 = c1.copy('c_copy_1', False, True)
    assert c4.elements != c1.elements
    assert c4.labels != c1.labels


@pytest.fixture
def tree():
    p1 = gdspy.Polygon(((0, 0), (0, 1), (1, 0)), 0, 0)
    p2 = gdspy.Polygon(((2, 0), (2, 1), (1, 0)), 1, 1)
    l = gdspy.Label('label', (0, 0), layer=10)
    c1 = gdspy.Cell('tree_' + unique())
    c1.add(p1)
    c1.add(l)
    c2 = gdspy.Cell('tree_' + unique())
    c2.add(p2)
    c2.add(gdspy.CellReference(c1))
    c3 = gdspy.Cell('tree_' + unique())
    c3.add(gdspy.CellArray(c2, 3, 2, (3, 3)))
    return c3, c2, c1


def test_flatten_00(tree):
    c3, c2, c1 = tree
    c3.flatten()
    assert len(c3.elements) == 2
    for i in range(2):
        assert (c3.elements[i].layers == [0] * 6 or
                c3.elements[i].layers == [1] * 6)
        assert c3.elements[i].layers == c3.elements[i].datatypes


def test_flatten_01(tree):
    c3, c2, c1 = tree
    c3.flatten(None, 2)
    assert len(c3.elements) == 2
    for i in range(2):
        assert (c3.elements[i].layers == [0] * 6 or
                c3.elements[i].layers == [1] * 6)
        assert c3.elements[i].datatypes == [2] * 6


def test_flatten_10(tree):
    c3, c2, c1 = tree
    c3.flatten(2)
    assert len(c3.elements) == 2
    for i in range(2):
        assert (c3.elements[i].datatypes == [0] * 6 or
                c3.elements[i].datatypes == [1] * 6)
        assert c3.elements[i].layers == [2] * 6


def test_flatten_11(tree):
    c3, c2, c1 = tree
    c3.flatten(2, 3)
    assert len(c3.elements) == 1
    assert c3.elements[0].layers == [2] * 12
    assert c3.elements[0].datatypes == [3] * 12


def test_bb(tree):
    c3, c2, c1 = tree
    err = numpy.array(((0, 0), (8, 4))) - c3.get_bounding_box()
    assert numpy.max(numpy.abs(err)) == 0

    p2 = gdspy.Polygon(((-1, 2), (-1, 1), (0, 2)), 2, 2)
    c2.add(p2)
    err = numpy.array(((-1, 0), (8, 5))) - c3.get_bounding_box()
    assert numpy.max(numpy.abs(err)) == 0

    p1 = gdspy.Polygon(((0, 3), (0, 2), (1, 3)), 3, 3)
    c1.add(p1)
    err = numpy.array(((-1, 0), (8, 6))) - c3.get_bounding_box()
    assert numpy.max(numpy.abs(err)) == 0


def test_layers(tree):
    assert tree[0].get_layers() == {0, 1, 10}


def test_datatypes(tree):
    assert tree[0].get_datatypes() == {0, 1}


def test_polygons(tree):
    c3, c2, c1 = tree
    p1 = gdspy.Polygon(((0, 3), (0, 2), (1, 3)), 3, 3)
    c1.add(p1)
    assert len(c3.get_polygons()) == 18
    assert len(c3.get_polygons(False, 0)) == 6
    assert len(c3.get_polygons(False, 1)) == 12
    assert set(c3.get_polygons(True).keys()) == {(0, 0), (1, 1), (3, 3)}
    assert set(c3.get_polygons(True, 0).keys()) == {c2.name}
    assert set(c3.get_polygons(True, 1).keys()) == {c1.name, (1, 1)}
