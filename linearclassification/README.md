Linear Classifier Generator
====================

This tool allows you to generate a linear classifier to run as a set of VEDO scoring rules on the DataSift platform.

The tool will:

* Learn a linear classifier from labelled training data 
* Express the classifier in DataSift CSDL ()so that it can be executed in the DataSift platform)

The tool incorporates code to extract candidate features from the training data such as single words, bigrams etc. from the textual content of the interaction. It can also look for candidate features in the metadata, e.g. the **twitter.user.desription**.

After extracting the candidate features, it selects the most effective ones based on a chi-squared test then learns the classifier based on this subset. You specify the number of features to retain in the config file.

Once the classifier has been fit to the data, two quality metrics are reported to the log as confusion matrices for:

* The training data
* The data that was held back for cross validation

You specify how much data to hold back for validation on the command line using the **test_period** parameter.


##Training data

You need to supply a training set, i.e. a representative set of interactions and an associated class label (category) for each one. 

The set of interactions must be provided as JSON where interactions are newline delimited.

There are two options for supplying the labels:

* Add the label to the object in the JSON training set as a new property 
* Supply a separate CSV file which associates the class labels with the **interaction.ids**

If you choose the CSV file option the file must have a header row. For example as follow:

<pre>interaction.id, label</pre>


##Config


Configuration options like the number of features to use, where to source the ngram features, whether to use links info etc. can be set by creating a class that overrides the config_base.py in lib and specifying on the command line.

##Command line

You execute like this:

    python scored_tags_classifier.py --test_period=[Test period] --config_module_path=[config file] --training_json=[training interactions] --training_csv=[OPTIONAL: label file] --classpath=[label path] > [output file]


lib/default_config.py

*  **--training_json** - Path to the file of training interactions formatted as JSON line delimited.
*  **--classpath** - The path the class lable for the interaction. When using a CSV file as the source of labels this is the column header, otherwise this is the path to the appropriate property in the JSON object.
*  **--test_period** - Controls the amount of data held back for testing the resulting classifier. For instance if you specify 4, this means that one in four interactions will be kept back for testing.
*  **--config_module_path** - Python module containing the configuration for the execution.
*  **--training_csv** - OPTIONAL. Path to the CSV file containing class labels.

The resulting classifier will be written to standard output, hence the command above suggests piping this to an output file.

When you execute the script a timestamped log file will be produced giving you further DEBUG information.


##Test

As an example to demonstrate the tool, there is a file called **news_title_training_example.json** inside the /test folder. In this example, the class label has been added as a property for each interaction inside the JSON object. The data structure is minimum but demonstrates the tool cleanly.

To run the example:

    python scored_tags_classifier.py --test_period=4 --config_module_path=lib/default_config.py --classpath=label --training_json=test/news_title_training_example.json > classifier.txt


Dependencies
------------

* python v.3 or greater
* scikit-learn: http://scikit-learn.org/stable/install.html

