
#### Prompt formatting using triple-quote
For the text of gpt prompt, we use the triple-quote notation because it elegantly takes care of newlines
and can be integrated within the class functions.
Any preceding spaces are removed with dedent_triple_quote_str().
Note though that this notation does not work with f-string formatting especially when the dynamically
added text includes multiple lines.
We therefore use instead the triple-quote with the .format() notation to get a dynamic, yet structured and
readable, multi-line text.

