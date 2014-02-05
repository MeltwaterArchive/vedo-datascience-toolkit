Linear Classifier Generator
====================

This tool allows you to generate a linear classifier to run as a set of VEDO scoring rules on the DataSift platform.

The tool will:

* Learn a linear classifier from labelled training data 
* Express the classifier in CSDL so that it can be executed on the DataSift platform

The tool incorporates code to extract candidate features from the training data such as single words, bigrams etc. from the textual content of the interaction. It can also look for candidate features in the metadata, e.g. the **twitter.user.desription**.

After extracting the candidate features, it selects the most effective ones based on a chi-squared test then learns the classifier based on this subset. You specify the number of features to retain in the config file.

Once the classifier has been fit to the data, two quality metrics are reported to the log as confusion matrices for:

* The training data
* The data that was held back for cross validation

You specify how much data to hold back for validation on the command line using the **test_period** parameter.


##Dependencies

* Python v2.7 or greater
* scikit-learn: http://scikit-learn.org/stable/install.html


##Training data

You need to supply a training set, i.e. a representative set of interactions and an associated class label (category) for each one. 

The set of interactions must be provided as JSON where interactions are newline delimited.

There are two options for supplying the labels:

* Add the label to the object in the JSON training set as a new property 
* Supply a separate CSV file which associates the class labels with the **interaction.ids**

If you choose the CSV file option the file must have a header row. For example as follow:

<pre>interaction.id, label</pre>


##Config

There are a large number of options that you can consider when tuning a linear classifier. The example included in this library (see below) demonstrates a simple use case using the default configuration file.

You can create your own configuration by inheriting from the ConfigBase module (inside lib), and overriding any of these settings:

* **nfeatures** - The maximum number of features to identify.
* **frequency_threshold** - The minimum number of times a feature must occur to be considered.
* **featurepath** - The field of the interaction to inspect for features. Often this will be interaction.content as this will contain the main body of post content.
* **stopwords** - A function that returns a list of words that must be ignored.
* **apriori_features** - A function that returns a list of words that should definitely be considered. This is a chance to supply domain-specific knowledge.
* **keep_apriori_features** - When TRUE this forces the apriori features to be in the final set of selected features, otherwise the apriori features will be considered for the final set alongside learned features.
* **userinteractionsource** - Whether to consider the interaction.source field (for sources such as Twitter this is the textual description of the application used to post the content).
* **usenamewords** - Whether to consider the **interaction.author.name** field which contains the author's name.
* **useuserurlwords** - Whether to consider the **twitter.user.url** field.
* **useshareurlwords** - Whether to consider links in the content.
* **usehashtags** - Whether to consider hashtags in the content.
* **useunigrams, usebigrams, usetrigrams** - Whether to look for features that are one, two or three adjacent words.
* **usewordpairs** - Whether to look for pairs of words that are not adjacent and are in any order.
* **useorderedpairs,useorderedtriples** - Whether to look for pairs or trios of words that are not adjacent and but are in a consistent order.



##Executing

Firstly, clone the repository to your local machine.

Next, you'll need to add the library to your PYTHONPATH environment setting by modifying your .profile or .bash_profile file, for example:

<pre>export PYTHONPATH=$PYTHONPATH:~/Documents/Datasift/Code/vedo-data-science-toolkit</pre>

You execute the tool as follows:

    python scored_tags_classifier.py --test_period=[Test period] --config_module_path=[config file] --training_json=[training interactions] --training_csv=[OPTIONAL: label file] --classpath=[label path] --csdl_file [output file]

*  **--training_json** - Path to the file of training interactions formatted as JSON line delimited.
*  **--classpath** - The path the class lable for the interaction. When using a CSV file as the source of labels this is the column header, otherwise this is the path to the appropriate property in the JSON object.
*  **--test_period** - Controls the amount of data held back for testing the resulting classifier. For instance if you specify 4, this means that one in four interactions will be kept back for testing.
*  **--config_module_path** - Python module containing the configuration for the execution. Default config file is at **lib/default_config.py**
*  **--training_csv** - OPTIONAL. Path to the CSV file containing class labels.
*  **--csdl_file** Output file for CSDL

When you execute the script a timestamped log file will be produced giving you further DEBUG information.


##Test Example

As an example to demonstrate the tool, there is a file called **news_title_training_example.json** inside the /test folder. In this example, the class label has been added as a property for each interaction inside the JSON object. The data structure is minimum but demonstrates the tool cleanly.

To run the example:

    python scored_tags_classifier.py --test_period=4 --config_module_path=lib/default_config.py --classpath=label --training_json=test/news_title_training_example.json --csdl_file classifier.txt



