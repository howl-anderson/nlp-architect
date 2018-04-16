# ******************************************************************************
# Copyright 2017-2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ******************************************************************************

from __future__ import unicode_literals, print_function, division, \
    absolute_import

import csv
import io
import os

from neon.backends import gen_backend
from neon.util.argparser import NeonArgparser

from models.np_semantic_segmentation.data import NpSemanticSegData, extract_y_labels
from models.np_semantic_segmentation.model import NpSemanticSegClassifier


def classify_collocation(dataset, model_file_path, num_epochs, callback_args):
    """
    Classify the dataset by the given trained model
    Args:
        model_file_path (str): model path
        num_epochs (int): number of epochs
        callback_args (dict): callback_arg
        dataset: NpSemanticSegData object containing the dataset
    Returns:
        the output of the final layer for the entire Dataset
    """
    # load existing model
    if not os.path.isabs(model_file_path):
        # handle case using default value\relative paths
        model_file_path = os.path.join(os.path.dirname(__file__), model_file_path)
    loaded_model = NpSemanticSegClassifier(num_epochs, callback_args)
    loaded_model.load(model_file_path)
    print("Model loaded")
    # arrange the data
    return loaded_model.get_outputs(dataset.train_set)


def print_evaluation(y_test, predictions):
    """
    Print evaluation of the model's predictions comparing to the given y labels (if given)
    Args:
        y_test: list of the labels given in the data
        predictions: the model's predictions
    """
    tp = 0.0
    fp = 0.0
    tn = 0.0
    fn = 0.0
    for y_true, prediction in zip(y_test, predictions):
        if prediction == 1:
            if y_true == 1:
                tp = tp + 1
            else:
                fp = fp + 1
        elif y_true == 0:
            tn = tn + 1
        else:
            fn = fn + 1
    acc = 100 * ((tp + tn) / len(predictions))
    prec = 100 * (tp / (tp + fp))
    rec = 100 * (tp / (tp + fn))
    print("Model statistics:\naccuracy: {0:.2f}\nprecision: {1:.2f}"
          "\nrecall: {2:.2f}\n".format(acc, prec, rec))


def write_results(predictions, output_path):
    """
    Write csv file of predication results to specified --output
    Args:
        output_path (str): output file path
        predictions:
            the model's predictions
    """
    results_list = predictions.tolist()
    out_file = io.open(output_path, 'w', encoding='utf-8')
    writer = csv.writer(out_file, delimiter=',', quotechar='"')
    for result in results_list:
        writer.writerow([result])
    out_file.close()
    print("Results of inference saved in {0}".format(output_path))


if __name__ == "__main__":
    # parse the command line arguments
    parser = NeonArgparser()
    parser.add_argument('--data', default='datasets/prepared_data.csv',
                        help='prepared data CSV file path')
    parser.add_argument('--model', help='path to the trained model file')
    parser.add_argument('--print_stats', default=False, type=bool,
                        help='print evaluation stats for the model '
                             'predictions - if your data has tagging')
    parser.add_argument('--output', default="datasets/inference_data.csv",
                        help='path to location for inference output file')
    args = parser.parse_args()
    data_path = args.data
    if not os.path.exists(data_path):
        raise Exception('Not valid model settings file')
    model_path = args.model
    if not os.path.exists(data_path):
        raise Exception('Not valid model settings file')
    # generate backend
    be = gen_backend(batch_size=10)
    data_set = NpSemanticSegData(data_path, train_to_test_ratio=1)
    results = classify_collocation(data_set, model_path, args.num_epochs, **args.callback_args)
    if args.print_stats and (data_set.is_y_labels is not None):
        y_labels = extract_y_labels(data_path)
        print_evaluation(y_labels, results.argmax(1))
    write_results(results.argmax(1), args.output)
