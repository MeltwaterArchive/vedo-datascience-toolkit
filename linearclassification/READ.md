linearclassification
====================

This tool allows you to

* learn a linear classifier from labelled training data 
* then express the classifier in DataSift CSDL so that it can be executed in the DataSift platform

The tool incorporates code to extract candidate features from the training data such as single words, bigrams etc. from the textual content of the interaction. It can also look for candidate features in the metadata, e.g. the twitter.user.desription.

After extracting the candidate features, it selects the most effective ones based on a chi-squared test then learns the classifier based on this subset. You specify the number of features to retain in the config file.

Once the classifier has been fit to the data, two quality metrics are reported to the log: confusion matrices for

* the training data
* the data that was held back for cross validation

You specify how much data to hold back for validation on the command line.

Training data
--------------

You need to supply a training set, i.e. a representative set of interactions and an associated class label for each one. There are two options for supplying the labels. You can either

* embed them in the JSON description of the interactions
* supply a csv file which associates the class labels with the interaction.ids, along with the JSON description of the interactions.

Config
------

Configuration options like the number of features to use, where to source the ngram features, whether to use links info etc. can be set by creating a class that overides the config_base.py in lib and specifying on the command line.

Command line
-------------

You execute like this:

    python scored_tags_classifier.py --test_period=4 --config_module_path=lib/default_config.py --training_csv=<labels.csv> --classpath=<label> --training_json=<interactions.json>


*  --training_json TRAINING_JSON
                        path to file containing full json description of all the training interactions
*  --classpath CLASSPATH
                        path to class labels in json file or class label column name in csv
*  --test_period TEST_PERIOD
                        how often to hold back training data for testing
*  --config_module_path CONFIG_MODULE_PATH
                        python module containing the configuration for the training
*  --training_csv TRAINING_CSV
                        path to csv file containing labels (must have header)


Test
----

There's an example training file in the test directory. In this example, the label is embedded in the JSON description of the interaction. Only the minimum structure necessary has been given. Try it like this

    python scored_tags_classifier.py --test_period=4 --config_module_path=lib/default_config.py --classpath=label --training_json=/tmp/news_title_training_example.json


Dependencies
------------

* scikit-learn: http://scikit-learn.org/stable/install.html
