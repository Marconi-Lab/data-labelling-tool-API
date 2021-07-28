from urllib.request import urlopen
from datetime import datetime
import tensorflow as tf

from PIL import Image
import numpy as np
import sys

# import mscviplib


filename = "./model.pb"
labels_filename = "labels.txt"

network_input_size = 0

output_layer = "model_output:0"
input_node = "data:0"

graph_def = tf.compat.v1.GraphDef()
labels = []


def initialize():
    print("Loading model...", end=""),
    with open(filename, "rb") as f:
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name="")

    # Retrieving 'network_input_size' from shape of 'input_node'
    with tf.compat.v1.Session() as sess:
        input_tensor_shape = sess.graph.get_tensor_by_name(input_node).shape.as_list()

    assert len(input_tensor_shape) == 4
    assert input_tensor_shape[1] == input_tensor_shape[2]

    global network_input_size
    network_input_size = input_tensor_shape[1]

    print("Success!")
    print("Loading labels...", end="")
    with open(labels_filename, "rt") as lf:
        global labels
        labels = [l.strip() for l in lf.readlines()]
    print(len(labels), "found. Success!")