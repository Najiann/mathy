import sys
import collections
import os
import time
import random
import numpy
import math
import sys
from alpha_zero_general.pytorch_classification.utils import Bar, AverageMeter
from alpha_zero_general.NeuralNet import NeuralNet
from mathzero.model.math_estimator import math_estimator
from mathzero.environment_state import MathEnvironmentState
from itertools import zip_longest
from mathzero.model.math_predictor import MathPredictor
from mathzero.model.features import (
    FEATURE_TOKEN_VALUES,
    FEATURE_TOKEN_TYPES,
    FEATURE_NODE_COUNT,
    FEATURE_PROBLEM_TYPE,
    FEATURE_COLUMNS,
)


class NetConfig:
    def __init__(self, lr=0.001, dropout=0.2, epochs=10, batch_size=256):
        self.lr = lr
        self.dropout = dropout
        self.epochs = epochs
        self.batch_size = batch_size


class MathModel(NeuralNet):
    def __init__(self, game, model_dir, all_memory=False, dev_mode=False):
        import tensorflow as tf

        session_config = tf.ConfigProto()
        session_config.gpu_options.per_process_gpu_memory_fraction = (
            game.get_gpu_fraction() if all_memory is False else 1
        )
        estimator_config = tf.estimator.RunConfig(session_config=session_config)
        self.action_size = game.get_agent_actions_count()

        self.args = NetConfig()
        # Feature columns describe how to use the input.
        self.token_value_feature = tf.feature_column.embedding_column(
            tf.feature_column.categorical_column_with_hash_bucket(
                key=FEATURE_TOKEN_VALUES, hash_bucket_size=12
            ),
            dimension=2,
        )
        self.feature_tokens_type = tf.feature_column.embedding_column(
            tf.feature_column.categorical_column_with_hash_bucket(
                key=FEATURE_TOKEN_TYPES, hash_bucket_size=12, dtype=tf.int64
            ),
            dimension=2,
        )

        self.feature_node_count = tf.feature_column.numeric_column(
            key=FEATURE_NODE_COUNT, dtype=tf.int16
        )
        self.feature_problem_type = tf.feature_column.indicator_column(
            tf.feature_column.categorical_column_with_identity(
                key=FEATURE_PROBLEM_TYPE, num_buckets=32
            )
        )
        self.feature_columns = [
            self.feature_problem_type,
            self.feature_tokens_type,
            self.feature_node_count,
            self.token_value_feature,
        ]
        self.network = tf.estimator.Estimator(
            config=estimator_config,
            model_fn=math_estimator,
            model_dir=model_dir,
            params={
                "feature_columns": self.feature_columns,
                "action_size": self.action_size,
                "learning_rate": self.args.lr,
                "hidden_units": [10, 10],
            },
        )
        self._predictor = MathPredictor(self.network)

    def train(self, examples):
        """
        examples: list of examples, each example is of form (env_state, pi, v)
        """
        import tensorflow as tf
        from .math_hooks import TrainingLoggerHook

        # Define the training inputs
        def get_train_inputs(examples, batch_size):

            from json import loads, dumps
            import tensorflow as tf

            with tf.name_scope("PreprocessData"):
                inputs = {}
                outputs = []
                for feature_key in FEATURE_COLUMNS:
                    inputs[feature_key] = []
                # Build up a feature map that can work as input
                for ex in examples:
                    ex_input = ex["inputs"]
                    ex_append = {}
                    for feature_key in FEATURE_COLUMNS:
                        inputs[feature_key].append(ex_input[feature_key])
                    target_pi = numpy.array(ex["policy"], dtype="float32")
                    target_value = ex["reward"]
                    outputs.append(
                        numpy.concatenate((target_pi, [target_value]), axis=0)
                    )
                # Pad the variable length columns to longest in the list
                inputs[FEATURE_TOKEN_TYPES] = numpy.array(
                    list(zip_longest(*inputs[FEATURE_TOKEN_TYPES], fillvalue=-1))
                ).T
                inputs[FEATURE_TOKEN_VALUES] = numpy.array(
                    list(zip_longest(*inputs[FEATURE_TOKEN_VALUES], fillvalue=0))
                ).T
                inputs[FEATURE_NODE_COUNT] = numpy.array(
                    inputs[FEATURE_NODE_COUNT], dtype="int16"
                )
                inputs[FEATURE_PROBLEM_TYPE] = numpy.array(
                    inputs[FEATURE_PROBLEM_TYPE], dtype="int8"
                )
                dataset = tf.data.Dataset.from_tensor_slices(
                    (inputs, numpy.array(outputs))
                )
                dataset = dataset.shuffle(1000).batch(batch_size)
                return dataset

        # total_batches = int(len(examples) / self.args.batch_size)
        # if total_batches == 0:
        #     return False

        print(
            "Training neural net for ({}) epochs with ({}) examples...".format(
                self.args.epochs, len(examples)
            )
        )
        for i in range(self.args.epochs):
            print("EPOCH: {}".format(i + 1))
            sys.stdout.flush()
            self.network.train(
                hooks=[TrainingLoggerHook(1, self.args.batch_size)],
                input_fn=lambda: get_train_inputs(examples, self.args.batch_size),
            )
        return True

    def predict(self, env_state: MathEnvironmentState):
        tokens = env_state.parser.tokenize(env_state.agent.problem)
        types = []
        values = []
        for t in tokens:
            types.append(t.type)
            values.append(t.value)
        input_features = {
            FEATURE_TOKEN_TYPES: [types],
            FEATURE_TOKEN_VALUES: [values],
            FEATURE_NODE_COUNT: [len(values)],
            FEATURE_PROBLEM_TYPE: [env_state.agent.problem_type],
        }
        start = time.time()
        prediction = self._predictor.predict(input_features)
        # print("predict : {0:03f}".format(time.time() - start))
        return prediction["out_policy"], prediction["out_value"][0]

    def start(self):
        self._predictor.start()

    def stop(self):
        self._predictor.stop()
