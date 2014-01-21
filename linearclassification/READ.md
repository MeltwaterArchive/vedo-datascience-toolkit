linearclassification
====================

This tool allows you to

* learn a linear classifier from labelled training data
* then express the classifier in DataSift CSDL so that it can be executed in the DataSift platform

The tool incorporates code to extract candidate features from the training data such as single words, bigrams etc.

After extracting the candidate features, it selects the most effective ones based on a chi-squared test then learns the classifier based on this subset. You specify the number of features to retain in the config file.

Once the classifier has been fit to the data, two quality metrics are reported to the log: confusion matrices for

* the training data
* the data that was held back for cross validation

You specify how much data to hold back for validation on the command line
