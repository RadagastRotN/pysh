# Pysh – the power of Bash inside Python

Pysh is a Python library that brings some of the Bash superpowers into Python, most notably
the easy way to make a pipeline of generators using the pipe sign.
Also implements natively in Python some subset of tools available in Bash, like grep or cat.


```python

cat("input_file.txt") | grep("abc") | str.lower | to_file("output_file.txt")

```

The above code reads "input_file.txt", stripping the trailing newline characters
then sends the content to grep which selects only lines containing string "abc"
then lowercases the text (yes, it is the `lower` method of Python's `str` class)
then saves it to "output_file.txt".

Instead of saving the output to file, you can also just iterate over the result and do
whatever you want with it:

```python

for line in cat("input_file.txt") | grep("abc") | str.lower:
    print(line)

```

